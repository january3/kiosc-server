"""Models for the ``dockerapps`` app."""
import contextlib
import uuid as uuid_object

from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.shortcuts import reverse
from django.db import models, transaction
from django.contrib.postgres.fields.jsonb import JSONField

from projectroles.models import Project
from bgjobs.models import BackgroundJob, JobModelMessageMixin

#: Token for "initial" state of container.
STATE_INITIAL = "initial"
#: Token for "idle" state of container.
STATE_IDLE = "idle"
#: Token for "starting" state of image and container.
STATE_STARTING = "starting"
#: Token for "running" state of container.
STATE_RUNNING = "running"
#: Token for "stopping" state of container.
STATE_STOPPING = "stopping"
#: Token for "failed" state of image and container.
STATE_FAILED = "failed"
#: Token for "pulling" state of image.
STATE_PULLING = "pulling"
#: Token for "deleting" state of container.
STATE_DELETING = "deleting"

#: Django model field choices for images.
IMAGE_STATE_CHOICES = (
    (STATE_INITIAL, STATE_INITIAL),
    (STATE_PULLING, STATE_PULLING),
    (STATE_IDLE, STATE_IDLE),
    (STATE_DELETING, STATE_DELETING),
    (STATE_FAILED, STATE_FAILED),
)

#: Django model field choices for container.
CONTAINER_STATE_CHOICES = (
    (STATE_IDLE, STATE_IDLE),
    (STATE_STARTING, STATE_STARTING),
    (STATE_RUNNING, STATE_RUNNING),
    (STATE_STOPPING, STATE_STOPPING),
    (STATE_FAILED, STATE_FAILED),
)


class DockerImage(models.Model):
    """Makes a Docker image available in a ``Project``."""

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: DateTime of last modification
    date_modified = models.DateTimeField(auto_now=True, help_text="DateTime of last modification")

    #: UUID used for identification throughout SODAR.
    sodar_uuid = models.UUIDField(
        default=uuid_object.uuid4, unique=True, help_text="Barcodeset SODAR UUID"
    )

    #: The project containing this barcode set.
    project = models.ForeignKey(Project, help_text="Project in which this objects belongs")

    #: The title of the application
    title = models.CharField(max_length=100, help_text="Title of the docker app")

    #: The description of the application
    description = models.TextField(help_text="Description of the docker app", blank=True, null=True)

    #: The "repository" of the image, if any.
    repository = models.CharField(max_length=512, help_text="The repository/name of the image.")

    #: The tag of the image, if any.
    tag = models.CharField(max_length=128, help_text="The tag of the image")

    #: The internal image ID.
    image_id = models.CharField(
        max_length=100, help_text="Internal ID of the Docker image", blank=True, null=True
    )

    #: The current state.
    state = models.CharField(
        max_length=64,
        default=STATE_INITIAL,
        help_text="The state of the image.",
        choices=IMAGE_STATE_CHOICES,
        blank=False,
        null=False,
    )

    @property
    def process(self):
        return self.dockerprocess_set.first()

    def get_absolute_url(self):
        return reverse(
            "dockerapps:image-detail",
            kwargs={"project": self.project.sodar_uuid, "image": self.sodar_uuid},
        )

    def __str__(self):
        return "DockerImage: %s (%s)" % (self.title, self.image_id)

    class Meta:
        ordering = ("-date_created",)

    def delete(self, *args, **kwargs):
        """Implementation that also removes all connected background job records."""
        for pk in [j.bg_job.pk for j in self.imagebackgroundjob_set.all()]:
            ImageBackgroundJob.objects.get(pk=pk).bg_job.delete()
        for pk in [j.bg_job.pk for j in self.process.containerstatecontrolbackgroundjob_set.all()]:
            ContainerStateControlBackgroundJob.objects.get(pk=pk).bg_job.delete()
        super().delete(*args, **kwargs)


class DockerProcess(models.Model):
    """Represents an instance of a Docker container.

    Running processes correspond to Docker images.  However, the ``DockerProcess`` also allows to define a
    container including environment variables without starting it and keeping it representation while it is
    not running.
    """

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: DateTime of last modification
    date_modified = models.DateTimeField(auto_now=True, help_text="DateTime of last modification")

    #: The image that the process is to be based on.
    image = models.ForeignKey(
        DockerImage,
        help_text="Docker container that this image is based on",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    #: The ID of the Docker container (when running).
    container_id = models.CharField(max_length=128, help_text="Container ID", blank=True, null=True)

    #: The port within the Docker container to listen on.
    internal_port = models.IntegerField(
        default=80, help_text="Server port within the container", blank=False, null=False
    )

    #: The port on the host (to redirect the requests/web socket to).
    host_port = models.IntegerField(
        help_text="The port of the container on the host", blank=False, null=False, unique=True
    )

    #: Whether or not the container should be running.
    do_run = models.BooleanField(
        default=False,
        help_text="Whether or not the container should be running",
        blank=False,
        null=False,
    )

    #: The current state.
    state = models.CharField(
        max_length=64,
        help_text="The state of the container.",
        choices=CONTAINER_STATE_CHOICES,
        default=STATE_IDLE,
        blank=False,
        null=False,
    )

    #: Define the environment variables to use, as an array of dicts with keys "name" and "value.
    #: This guarantees that the order of environment variable definitions does not change.
    environment = JSONField(help_text="The environment variables to use.")

    def __str__(self):
        return "DockerProcess: %s (%s)" % (self.image.title, self.container_id)

    class Meta:
        ordering = ("-date_created",)


class JobModelMessageMixin2(JobModelMessageMixin):
    @contextlib.contextmanager
    def marks(self):
        """Return a context manager that allows to run tasks between start and success/error marks."""
        self.mark_start()
        try:
            yield
        except:
            self.mark_error()
            raise
        else:
            self.mark_success()


class ContainerStateControlBackgroundJob(JobModelMessageMixin2, models.Model):
    """Background job for controlling container state."""

    spec_name = "dockerapps.container_jobcontrol"

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: UUID of the job
    sodar_uuid = models.UUIDField(
        default=uuid_object.uuid4, unique=True, help_text="Background job specialization SODAR UUID"
    )

    #: The Docker process that the job belongs to.
    process = models.ForeignKey(
        DockerProcess,
        help_text="The docker process that the job belongs to",
        on_delete=models.CASCADE,
    )

    #: The background job that is specialized.
    bg_job = models.ForeignKey(
        BackgroundJob,
        null=False,
        blank=False,
        related_name="%(app_label)s_%(class)s_related",
        help_text="Background job for state etc.",
        on_delete=models.CASCADE,
    )


# TODO: It would probably be nice to have a morge general for "ImageBackgroundJobs".


class ImageBackgroundJob(JobModelMessageMixin2, models.Model):
    """Background job for manipulating ``DockerImage`` records."""

    @classmethod
    @transaction.atomic()
    def construct(cls, image, user, action):
        image.log_entries.create(text="Performing action on image: %s." % action)
        return image.imagebackgroundjob_set.create(
            action=action,
            bg_job=BackgroundJob.objects.create(
                project=image.project,
                user=user,
                job_type=cls.spec_name,
                name="Performing action %s on %s:%s (%s)"
                % (action, image.repository, image.tag, image.title),
            ),
        )

    spec_name = "dockerapps.image_process"

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: UUID of the job
    sodar_uuid = models.UUIDField(
        default=uuid_object.uuid4, unique=True, help_text="Background job specialization SODAR UUID"
    )

    #: The action to perform.
    action = models.CharField(max_length=32, choices=(("pull", "pull"), ("delete", "delete")))

    #: The Docker image that the job belongs to.
    image = models.ForeignKey(
        DockerImage,
        help_text="The docker image that the job belongs to",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    #: The background job that is specialized.
    bg_job = models.ForeignKey(
        BackgroundJob,
        null=False,
        related_name="%(app_label)s_%(class)s_related",
        help_text="Background job for state etc.",
        on_delete=models.CASCADE,
    )


@transaction.atomic()
def update_container_states():
    """Look at all ``DockerContainer`` objects and synchronize their state with the one from Docker."""
    print("updating container states...")


#     statuses = {}
#     for container in docker.from_env().containers.list():
#         statuses[container.image.id] = container.status
#     for app in DockerApp.objects.all():
#         if statuses.get(app.image_id) == "running":
#             app.state = "running"
#             app.save()
#         elif statuses.get(app.image_id, "exited") == "exited":
#             app.state = "idle"
#             app.save()


class LogEntry(models.Model):
    class Meta:
        abstract = True

    #: DateTime of creation
    date_created = models.DateTimeField(auto_now_add=True, help_text="DateTime of creation")

    #: The level of the log entry.
    level = models.CharField(
        max_length=32,
        choices=(("info", "info"), ("warning", "warning"), ("error", "error")),
        default="info",
        help_text="Level of log entry",
        blank=False,
        null=False,
    )

    #: The log entry text.
    text = models.TextField()


class ImageLogEntry(LogEntry):

    #: The ``DockerImage`` that the log entry is for.
    image = models.ForeignKey(DockerImage, related_name="log_entries", blank=False, null=False)


class ContainerLogEntry(LogEntry):

    #: The ``DockerProcess`` that the log entry is for.
    process = models.ForeignKey(DockerProcess, related_name="log_entries", blank=False, null=False)
