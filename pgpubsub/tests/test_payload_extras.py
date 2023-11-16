import json
import os
from contextlib import contextmanager

import pytest

from django.db import connections
from django.db.models import Q
from django.db.transaction import atomic
from pgpubsub.listen import process_notifications
from pgpubsub.listeners import ListenerFilterProvider
from pgpubsub.models import Notification
from pgpubsub.tests.channels import (
    MediaTriggerChannel,
)
from pgpubsub.tests.models import Author, Media, Post

@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    is_multitenant = True
    print(f"django_db_modify_db_settings: {is_multitenant=}")
    if is_multitenant:
        from django.conf import settings
        settings.PGPUBSUB_ENABLE_PAYLOAD_EXTRAS = True

"""
@pytest.fixture
def is_multitenant(request):
    marks = [m.name for m in request.node.iter_markers()]
    if request.node.parent:
        marks += [m.name for m in request.node.parent.iter_markers()]
    return 'multitenant' in marks
    """


@pytest.mark.multitenant
@pytest.mark.django_db(transaction=True)
def test_payload_extras_are_not_added_by_default(pg_connection):
    Media.objects.create(name='avatar.jpg', content_type='image/png', size=15000)
    stored_notification = Notification.from_channel(channel=MediaTriggerChannel).get()
    assert 'extras' not in stored_notification.payload

    pg_connection.poll()
    assert 1 == len(pg_connection.notifies)


@pytest.fixture
def configure_payload_extras():
    @contextmanager
    def configurer(func_name: str, extras: dict[str, str]):
        with connections['default'].cursor() as cursor:
            cursor.execute(f"""
                create or replace function {func_name}()
                    returns JSONB
                    language sql
                as $$
                    SELECT '{json.dumps(extras)}'::JSONB
                $$
            """)
            yield
            cursor.execute("drop function if exists get_test_payload_extras()")

    return configurer


@pytest.mark.parametrize("db", [None, "default"])
@pytest.mark.django_db(transaction=True)
def test_payload_extras_are_added_if_enabled(
        pg_connection, db, configure_payload_extras
):
    with (
            atomic(),
            configure_payload_extras(
                func_name='get_test_payload_extras',
                extras={'test_key': 'test-value'},
            )
    ):
        Notification.set_payload_extras_builder('get_test_payload_extras', using=db)
        Media.objects.create(name='avatar.jpg', content_type='image/png', size=15000)
        stored_notification = Notification.from_channel(channel=MediaTriggerChannel).get()
        assert stored_notification.payload['extras'] == {'test_key': 'test-value'}

    pg_connection.poll()
    assert 1 == len(pg_connection.notifies)


@pytest.mark.django_db(transaction=True)
def test_process_notifications_gets_all_by_default(pg_connection):
    Author.objects.create(name='no-filter')
    assert not Post.objects.exists()
    process_notifications(pg_connection)
    assert 1 == Post.objects.filter(author__name='no-filter').count()


class TestListenerFilterProvider(ListenerFilterProvider):
    __test__ = False
    def get_filter(self) -> Q:
        return Q(payload__extras__test_key='test-value')


@pytest.mark.django_db(transaction=True)
def test_process_notifications_filters_out_unmatching_notifications(
        pg_connection, settings, configure_payload_extras
):
    Author.objects.create(name='notmatching')
    with (
            atomic(),
            configure_payload_extras(
                func_name='get_test_payload_extras',
                extras={'test_key': 'test-value'},
            )
    ):
        Notification.set_payload_extras_builder('get_test_payload_extras')
        Author.objects.create(name='matching')

    settings.PGPUBSUB_LISTENER_FILTER = 'pgpubsub.tests.test_payload_extras.TestListenerFilterProvider'
    assert not Post.objects.exists()
    process_notifications(pg_connection)
    assert 1 == Post.objects.filter(author__name='matching').count()
    assert 0 == Post.objects.filter(author__name='notmatching').count()


