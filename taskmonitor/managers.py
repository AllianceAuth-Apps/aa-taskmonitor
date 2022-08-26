import datetime as dt
import traceback as tb
from typing import List
from uuid import UUID

from django.db import models
from django.utils import timezone

from .helpers import extract_app_name


class TaskLogQuerySet(models.QuerySet):
    def csv_line_generator(self, fields: List[str]):
        """Return the tasklogs for a CSV file line by line.
        And return the field names as first line.
        """
        yield [field.name for field in fields]
        for obj in self.iterator():
            values = []
            for field in fields:
                if field.choices:
                    value = getattr(obj, f"get_{field.name}_display")()
                else:
                    value = getattr(obj, field.name)
                # if callable(value):
                #     try:
                #         value = value() or ""
                #     except Exception:
                #         value = "Error retrieving value"
                if value is None:
                    value = ""
                values.append(value)
            yield values


class TaskLogManagerBase(models.Manager):
    def create_from_task(
        self,
        *,
        state: int,
        sender=None,
        request: dict = None,
        task_id: str = None,
        received: dt.datetime = None,
        started: dt.datetime = None,
        exception=None,
    ) -> models.Model:
        """Create new object from a celery task."""
        if request is None:
            request = sender.request
        if task_id is None:
            task_id = request.id
        task_name = sender.name if sender else "?"
        if exception and (traceback := getattr(exception, "__traceback__")):
            traceback_out = "".join(
                tb.format_exception(None, value=exception, tb=traceback)
            )
        else:
            traceback_out = ""
        args = {
            "app_name": extract_app_name(task_name),
            "received": received,
            "retries": request.retries,
            "started": started,
            "state": state,
            "task_id": UUID(task_id),
            "task_name": task_name,
            "timestamp": timezone.now(),
        }
        if request.delivery_info and "priority" in request.delivery_info:
            args["priority"] = request.delivery_info["priority"]
        if request.parent_id:
            args["parent_id"] = UUID(request.parent_id)
        if exception:
            args["exception"] = str(exception)
        if traceback_out:
            args["traceback"] = traceback_out
        return self.create(**args)


TaskLogManager = TaskLogManagerBase.from_queryset(TaskLogQuerySet)
