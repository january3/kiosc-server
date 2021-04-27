# Generated by Django 3.1.8 on 2021-04-26 16:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('containers', '0005_auto_20210416_1334'),
    ]

    operations = [
        migrations.AddField(
            model_name='containerlogentry',
            name='user',
            field=models.ForeignKey(blank=True, help_text='User who caused the log entry', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='container_log_entries', to=settings.AUTH_USER_MODEL),
        ),
    ]