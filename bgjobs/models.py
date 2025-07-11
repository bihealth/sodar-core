"""
Models and model helper code provided by the bgjobs app.

The central class is BackgroundJob that stores the core information about a
background job.  You can "subclass" this class by creating your own models in
your apps and having a bg_job field referencing BackgroundJob
through a OneToOneField.

Further, the BackgroundJobLogEntry model allows to manage background log
entries for your background jobs.  Use the JobModelMessageMixin for adding
helper functions for applying state changes and adding log messages.
"""

import contextlib
import uuid as uuid_object

from django.conf import settings
from django.db import models

# Projectroles dependency
from projectroles.models import Project


# Access Django user model
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

# Levels to use in BackgroundJobLogEntry
LOG_LEVEL_DEBUG = 'debug'
LOG_LEVEL_INFO = 'info'
LOG_LEVEL_WARNING = 'warning'
LOG_LEVEL_ERROR = 'error'

# Choices to use in CharField for log level
LOG_LEVEL_CHOICES = (
    (LOG_LEVEL_DEBUG, 'debug'),
    (LOG_LEVEL_INFO, 'info'),
    (LOG_LEVEL_WARNING, 'warning'),
    (LOG_LEVEL_ERROR, 'error'),
)

# The possible states of BackgroundJob objects and their labels
JOB_STATE_INITIAL = 'initial'
JOB_STATE_RUNNING = 'running'
JOB_STATE_DONE = 'done'
JOB_STATE_FAILED = 'failed'

#: Choices to use in the CharField
JOB_STATE_CHOICES = (
    (JOB_STATE_INITIAL, 'initial'),
    ('running', 'running'),
    ('done', 'done'),
    ('failed', 'failed'),
)


class BackgroundJob(models.Model):
    """Common background job information."""

    #: DateTime of creation
    date_created = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of creation'
    )
    #: DateTime of last modification
    date_modified = models.DateTimeField(
        auto_now=True, help_text='DateTime of last modification'
    )
    #: The UUID for this job
    sodar_uuid = models.UUIDField(
        default=uuid_object.uuid4, unique=True, help_text='BG Job SODAR UUID'
    )
    #: The project this job belongs to. Set to None for site-wide jobs
    project = models.ForeignKey(
        Project,
        null=True,
        help_text='Project in which this objects belongs',
        on_delete=models.CASCADE,
    )
    #: The user initiating the job
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        null=False,
        related_name='background_jobs',
        on_delete=models.CASCADE,
    )
    #: Specializing string of the job
    job_type = models.CharField(
        max_length=512, null=False, help_text='Type of the job'
    )
    #: A human-readable name for this job
    name = models.CharField(max_length=512)
    #: An optional, extend description for this job
    description = models.TextField()
    #: The job status
    status = models.CharField(
        max_length=50, choices=JOB_STATE_CHOICES, default=JOB_STATE_INITIAL
    )

    class Meta:
        ordering = ["-date_created"]

    def get_human_readable_type(self) -> str:
        """
        Also implement in your sub classes to show human-readable type in the
        views.
        """
        return '(generic job)'

    def add_log_entry(
        self, message: str, level: str = LOG_LEVEL_INFO
    ) -> 'BackgroundJobLogEntry':
        """Add and return a new BackgroundJobLogEntry."""
        return self.log_entries.create(level=level, message=message)

    def __str__(self):
        return self.name


class BackgroundJobLogEntry(models.Model):
    """Log entry for background job"""

    #: Creation time of log entry
    date_created = models.DateTimeField(
        auto_now_add=True, help_text='DateTime of creation'
    )

    #: The BackgroundJob that the log entry is for
    job = models.ForeignKey(
        BackgroundJob,
        related_name='log_entries',
        help_text='Owning background job',
        on_delete=models.CASCADE,
    )

    #: The entry's log level
    level = models.CharField(
        max_length=50, choices=LOG_LEVEL_CHOICES, help_text='Level of log entry'
    )
    #: The message contained by the log entry
    message = models.TextField(help_text="Log level's message")

    class Meta:
        ordering = ['date_created']


class JobModelMessageMixin:
    """
    Mixin with shortcuts for marking job state and adding log entry.

    Use this in your BackgroundJob "subclasses" (sub classing meaning
    OneToOneField specializations).
    """

    task_desc = None

    @contextlib.contextmanager
    def marks(self):
        """
        Return a context manager that allows to run tasks between start and
        success/error marks.
        """
        self.mark_start()
        try:
            yield
        except Exception as e:
            self.mark_error(f'Error: {e}')
            raise
        else:
            self.mark_success()

    def mark_start(self):
        """Mark the export job as started."""
        self.bg_job.status = JOB_STATE_RUNNING
        self.bg_job.add_log_entry(f'{self.task_desc} started')
        self.bg_job.save()

    def mark_error(self, msg: str):
        """Mark the export job as complete successfully."""
        self.bg_job.status = JOB_STATE_FAILED
        self.bg_job.add_log_entry(f'{self.task_desc} file failed: {msg}')
        self.bg_job.save()

    def mark_success(self):
        """Mark the export job as complete successfully."""
        self.bg_job.status = JOB_STATE_DONE
        self.bg_job.add_log_entry(f'{self.task_desc} succeeded')
        self.bg_job.save()

    def add_log_entry(self, *args, **kwargs) -> BackgroundJobLogEntry:
        """Add a log entry through the related BackgroundJob."""
        return self.bg_job.add_log_entry(*args, **kwargs)
