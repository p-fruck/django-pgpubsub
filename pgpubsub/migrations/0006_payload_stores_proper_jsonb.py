# Generated by Django 3.2.12 on 2023-11-14 07:06

from django.db import migrations
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pgpubsub', '0005_alter_notification_options'),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name='notification',
            name='pgpubsub_notification_set_db_version',
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='notification',
            trigger=pgtrigger.compiler.Trigger(
                name='pgpubsub_notification_set_db_version',
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func="\n                    NEW.db_version := (\n                        SELECT max(id)\n                        FROM django_migrations\n                        WHERE app = NEW.payload ->> 'app'\n                    );\n                    NEW.created_at := NOW();\n                    RETURN NEW;\n                ",
                    hash='f2daa84904927c62a207e64749448e6b56da3b96',
                    operation='INSERT',
                    pgid='pgtrigger_pgpubsub_notification_set_db_version_ac4cd',
                    table='pgpubsub_notification',
                    when='BEFORE',
                ),
            ),
        ),
    ]