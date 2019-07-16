# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-07-15 16:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dockerapps", "0007_auto_20190627_2135")]

    operations = [
        migrations.AlterField(
            model_name="dockerprocess",
            name="host_port",
            field=models.IntegerField(
                help_text="The port of the container on the host", unique=True
            ),
        ),
        migrations.AlterField(
            model_name="dockerprocess",
            name="internal_port",
            field=models.IntegerField(default=80, help_text="Server port within the container"),
        ),
    ]