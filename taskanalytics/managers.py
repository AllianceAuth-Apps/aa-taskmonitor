import traceback as tb
from uuid import UUID

from django.db import models
from django.utils import timezone


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
        from .core import TASK_RECEIVED, TASK_STARTED, extract_app_name

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
            traceback_out = None
        args = {
            "app_name": extract_app_name(task_name),
            "parent_id": UUID(request.parent_id) if request.parent_id else None,
            "priority": sender.priority if sender else None,
            "received": records.fetch(task_id, TASK_RECEIVED),
            "retries": request.retries,
            "started": records.fetch(task_id, TASK_STARTED),
            "state": state,
            "task_id": UUID(task_id),
            "task_name": task_name,
            "timestamp": timezone.now(),
            "exception": str(exception) if exception else None,
            "traceback": traceback_out,
        }
        return self.create(**args)
