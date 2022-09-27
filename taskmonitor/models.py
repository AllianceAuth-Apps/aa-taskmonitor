import uuid

from django.db import models

from .helpers import extract_app_name
from .managers import QueuedTaskManager, TaskLogManager


class QueuedTask(models.Model):
    """A task that has been queued for later execution."""

    class Meta:
        managed = False

    app_name = models.CharField(max_length=255)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=255)
    priority = models.PositiveIntegerField(null=True, default=None)
    position = models.PositiveIntegerField()

    objects = QueuedTaskManager()

    def __str__(self):
        return self.id

    @classmethod
    def create_from_dict(cls, obj: dict, position: int) -> "QueuedTask":
        if "headers" not in obj:
            raise ValueError("headers missing in obj")
        headers = obj["headers"]
        properties = obj["properties"] if "properties" in obj else {}
        task_name = headers["task"]
        return cls(
            app_name=extract_app_name(task_name),
            id=headers["id"],
            name=task_name,
            priority=properties.get("priority"),
            position=position,
        )


class TaskReport(models.Model):
    """Dummy model to fake a 'Reports' entry on the admin index page."""

    class Meta:
        managed = False
        verbose_name = "report"

    id = models.BigIntegerField(primary_key=True)


class TaskLog(models.Model):
    """Log entry for an executed celery task."""

    class State(models.IntegerChoices):
        SUCCESS = 1, "success"
        RETRY = 2, "retry"
        FAILURE = 3, "failure"

    app_name = models.CharField(max_length=255, db_index=True)
    exception = models.TextField()
    parent_id = models.UUIDField(null=True, default=None)
    priority = models.IntegerField(null=True, default=None)
    retries = models.IntegerField()
    received = models.DateTimeField(null=True, default=None)
    runtime = models.FloatField(null=True, default=None, db_index=True)
    started = models.DateTimeField(null=True, default=None)
    state = models.IntegerField(choices=State.choices, db_index=True)
    task_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    task_name = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    traceback = models.TextField()

    objects = TaskLogManager()

    def __str__(self):
        return f"{self.task_name}:{self.pk}"

    def save(self, *args, **kwargs) -> None:
        if self.started:
            self.runtime = (self.timestamp - self.started).total_seconds()
        super().save(*args, **kwargs)
