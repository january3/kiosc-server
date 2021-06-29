# Generated by Django 3.1.8 on 2021-06-10 12:35

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projectroles', '0019_project_public_guest_access'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContainerTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Title of the container template.', max_length=512)),
                ('description', models.TextField(blank=True, help_text='Description of the container template.', null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='DateTime of ContainerTemplate creation')),
                ('date_modified', models.DateTimeField(auto_now=True, help_text='DateTime of last ContainerTemplate modification')),
                ('repository', models.CharField(blank=True, help_text='The repository/name of the image.', max_length=512, null=True)),
                ('tag', models.CharField(blank=True, help_text='The tag of the image.', max_length=128, null=True)),
                ('sodar_uuid', models.UUIDField(default=uuid.uuid4, help_text='ContainerTemplate SODAR UUID', unique=True)),
                ('container_port', models.IntegerField(blank=True, default=80, help_text='Server port within the container', null=True)),
                ('container_path', models.CharField(blank=True, help_text='Path segment of the container URL', max_length=512, null=True)),
                ('heartbeat_url', models.CharField(blank=True, help_text='Optional heartbeat URL to check if server in Docker container is alive', max_length=512, null=True)),
                ('timeout', models.IntegerField(blank=True, default=60, help_text='Interval in seconds for any Docker action to be performed.', null=True)),
                ('environment', models.JSONField(blank=True, help_text='The environment variables to use', null=True)),
                ('environment_secret_keys', models.CharField(blank=True, help_text='Comma-separated list of keys in the environment that are set but not read (use for tokens/keys).', max_length=512, null=True)),
                ('command', models.TextField(blank=True, help_text='The command to execute', null=True)),
                ('max_retries', models.IntegerField(blank=True, default=5, help_text='Maximal number of retries for an action in case of failure', null=True)),
                ('project', models.ForeignKey(help_text='Project in which this containertemplate belongs', on_delete=django.db.models.deletion.CASCADE, related_name='containertemplates', to='projectroles.project')),
            ],
            options={
                'ordering': ('-date_created',),
            },
        ),
    ]