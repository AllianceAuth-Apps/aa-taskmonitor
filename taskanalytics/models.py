import uuid

from django.db import models

from .managers import TaskLogEntryManager


class TaskLogEntry(models.Model):
    """The log entry for an executed celery task."""

    class State(models.IntegerChoices):
        SUCCESS = 1, "success"
        RETRY = 2, "retry"
        FAILURE = 3, "failure"

    app_name = models.CharField(max_length=255, db_index=True)
    exception = models.TextField(null=True, default=None)
    retries = models.IntegerField(null=True, default=None)
    received = models.DateTimeField(null=True, default=None)
    runtime = models.FloatField(null=True, default=None)
    started = models.DateTimeField(null=True, default=None)
    state = models.IntegerField(choices=State.choices, db_index=True)
    task_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    task_name = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    traceback = models.TextField(null=True, default=None)

    objects = TaskLogEntryManager()

    def __str__(self):
        return f"{self.task_name}:{self.pk}"

    def save(self, *args, **kwargs) -> None:
        if self.started:
            self.runtime = (self.timestamp - self.started).total_seconds()
        super().save(*args, **kwargs)
