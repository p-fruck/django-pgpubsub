# Generated by Django 3.2.12 on 2023-04-11 08:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='alternative_name',
            field=models.TextField(db_column='other', null=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='profile_picture',
            field=models.ForeignKey(db_column='picture', null=True, on_delete=django.db.models.deletion.PROTECT, to='tests.media'),
        ),
    ]