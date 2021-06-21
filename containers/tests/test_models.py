"""Tests for the container models"""
import json
from datetime import timedelta

from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

from containers.models import (
    Container,
    STATE_INITIAL,
    LOG_LEVEL_INFO,
    ContainerLogEntry,
    PROCESS_DOCKER,
    PROCESS_OBJECT,
)
from containers.tests.factories import ContainerLogEntryFactory
from containers.tests.helpers import TestBase


class TestContainerModel(TestBase):
    """Tests for the ``Container`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.data = {
            "repository": "repository",
            "tag": "tag",
            "project": self.project,
            "container_port": 80,
            "timeout": 60,
            "state": STATE_INITIAL,
            "environment": json.loads('{"test": 1}'),
        }

    def test_initialization(self):
        container = Container.objects.create(**self.data)
        expected = {
            **self.data,
            "command": None,
            "container_id": None,
            "container_path": None,
            "heartbeat_url": None,
            "environment_secret_keys": None,
            "image_id": None,
            "date_last_status_update": None,
            "project": self.project.pk,
            "id": container.id,
            "sodar_uuid": container.sodar_uuid,
            "max_retries": container.max_retries,
        }
        self.assertEqual(model_to_dict(container), expected)

    def test___str__(self):
        self.assertEqual(
            str(self.container1),
            "Container: {} [{}]".format(
                self.container1.get_repos_full(),
                self.container1.state,
            ),
        )

    def test___repr__(self):
        self.assertEqual(
            repr(self.container1),
            "Container({})".format(
                self.container1.get_repos_full(),
            ),
        )

    def test_get_repos_full(self):
        self.assertEqual(
            self.container1.get_repos_full(),
            "{}:{}".format(
                self.container1.repository,
                self.container1.tag,
            ),
        )

    def test_get_repos_full_no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            self.container1.get_repos_full(),
            self.container1.repository,
        )

    def test_get_display_name(self):
        self.assertEqual(
            self.container1.get_display_name(),
            "{}:{}".format(
                self.container1.repository,
                self.container1.tag,
            ),
        )

    def test_get_display_name_no_tag(self):
        self.container1.tag = ""
        self.container1.save()
        self.assertEqual(
            self.container1.get_display_name(), self.container1.repository
        )

    def test_get_date_created(self):
        self.assertEqual(
            self.container1.get_date_created(),
            localtime(self.container1.date_created).strftime("%Y-%m-%d %H:%M"),
        )

    def test_get_date_modified(self):
        self.assertEqual(
            self.container1.get_date_modified(),
            localtime(self.container1.date_modified).strftime("%Y-%m-%d %H:%M"),
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.container1.get_absolute_url(),
            reverse(
                "containers:container-detail",
                kwargs={"container": self.container1.sodar_uuid},
            ),
        )


class TestContainerLogEntry(TestBase):
    """Tests for the ``ContainerLogEntry`` model."""

    def setUp(self):
        super().setUp()
        self.create_one_container()
        self.log_entry = ContainerLogEntryFactory(
            container=self.container1, user=self.superuser
        )
        self.log_entry_no_user = ContainerLogEntryFactory(
            container=self.container1
        )
        self.log_entry_docker1 = ContainerLogEntryFactory(
            container=self.container1,
            user=self.superuser,
            process=PROCESS_DOCKER,
            date_docker_log=timezone.now() - timedelta(minutes=2),
        )
        self.log_entry_docker2 = ContainerLogEntryFactory(
            container=self.container1,
            user=self.superuser,
            process=PROCESS_DOCKER,
            date_docker_log=timezone.now() - timedelta(minutes=2),
        )
        self.data = {
            "process": PROCESS_OBJECT,
            "level": LOG_LEVEL_INFO,
            "text": "Log entry",
            "user": self.superuser,
            "container": self.container1,
        }
        self.data_docker_log = {
            "process": PROCESS_DOCKER,
            "date_docker_log": timezone.now() - timedelta(minutes=2),
            "level": LOG_LEVEL_INFO,
            "text": "Log entry",
            "user": self.superuser,
            "container": self.container1,
        }

    def test_initialization(self):
        log_entry = ContainerLogEntry.objects.create(**self.data)
        expected = {
            **self.data,
            "user": self.superuser.pk,
            "container": self.container1.pk,
            "id": log_entry.pk,
            "date_docker_log": None,
        }
        self.assertEqual(model_to_dict(log_entry), expected)

    def test_initialization_docker_log(self):
        log_entry = ContainerLogEntry.objects.create(**self.data_docker_log)
        expected = {
            **self.data_docker_log,
            "user": self.superuser.pk,
            "container": self.container1.pk,
            "id": log_entry.pk,
            "date_docker_log": log_entry.date_docker_log,
        }
        self.assertEqual(model_to_dict(log_entry), expected)

    def test_get_date_created(self):
        self.assertEqual(
            self.log_entry.get_date_created(),
            localtime(self.log_entry.date_created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def test_get_date_docker_log(self):
        self.assertEqual(
            self.log_entry_docker1.get_date_docker_log(),
            localtime(self.log_entry_docker1.date_docker_log).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def test_get_date_docker_log_none(self):
        self.assertEqual(self.log_entry.get_date_docker_log(), "")

    def test_get_date_order_by(self):
        self.assertEqual(
            self.log_entry.get_date_order_by(),
            localtime(self.log_entry.date_created).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def test_get_date_order_by_docker_log(self):
        self.assertEqual(
            self.log_entry_docker1.get_date_order_by(),
            localtime(self.log_entry_docker1.date_docker_log).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

    def test___str__(self):
        self.assertEqual(
            str(self.log_entry),
            "[{} {} {}] ({}) {}".format(
                self.log_entry.get_date_order_by(),
                self.log_entry.level.upper(),
                self.log_entry.user.username,
                self.log_entry.process.capitalize(),
                self.log_entry.text,
            ),
        )

    def test___str___docker_log(self):
        self.assertEqual(
            str(self.log_entry_docker1),
            "[{} {} {}] ({}) {}".format(
                self.log_entry_docker1.get_date_order_by(),
                self.log_entry_docker1.level.upper(),
                self.log_entry_docker1.user.username,
                self.log_entry_docker1.process.capitalize(),
                self.log_entry_docker1.text,
            ),
        )

    def test___str___no_user(self):
        self.assertEqual(
            str(self.log_entry_no_user),
            "[{} {} anonymous] ({}) {}".format(
                self.log_entry_no_user.get_date_order_by(),
                self.log_entry_no_user.level.upper(),
                self.log_entry_no_user.process.capitalize(),
                self.log_entry_no_user.text,
            ),
        )

    def test_containerlogentrymanager_merge_order(self):
        self.assertEqual(
            [
                self.log_entry_docker1,
                self.log_entry_docker2,
                self.log_entry,
                self.log_entry_no_user,
            ],
            list(ContainerLogEntry.objects.merge_order()),
        )

    def test_containerlogentrymanager_get_date_last_docker_log(self):
        self.assertEqual(
            self.log_entry_docker2.get_date_docker_log(),
            ContainerLogEntry.objects.get_date_last_docker_log(),
        )