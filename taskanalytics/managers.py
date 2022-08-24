import traceback as tb
from uuid import UUID

from django.db import models
from django.utils import timezone

from .helpers import extract_app_name


class TaskLogManager(models.Manager):
    def create_from_task(
        self,
        *,
        state: int,
        records,
        sender=None,
        request: dict = None,
        task_id: str = None,
        exception=None,
    ) -> models.Model:
        """Create new objects from task infos."""
        from .core.tasklogs import TASK_RECEIVED, TASK_STARTED

        if request is None:
            request = sender.request
        if task_id is None:
            task_id = request.id
        task_name = request.task
        if exception and (traceback := getattr(exception, "__traceback__")):
            traceback_out = "".join(
                tb.format_exception(None, value=exception, tb=traceback)
            )
        else:
            traceback_out = ""
        args = {
            "app_name": extract_app_name(task_name),
            "received": records.fetch(task_id, TASK_RECEIVED),
            "retries": request.retries,
            "started": records.fetch(task_id, TASK_STARTED),
            "state": state,
            "task_id": UUID(task_id),
            "task_name": task_name,
            "timestamp": timezone.now(),
        }
        if sender:
            args["priority"] = sender.priority
        if request.parent_id:
            args["parent_id"] = UUID(request.parent_id)
        if exception:
            args["exception"] = str(exception)
        if traceback_out:
            args["traceback"] = traceback_out
        return self.create(**args)
