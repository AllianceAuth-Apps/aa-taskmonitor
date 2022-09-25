import datetime as dt
import traceback as tb
from typing import List
from uuid import UUID

from django.db import models
from django.db.models import Avg, Count, Max
from django.db.models.functions import TruncMinute
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

    def aggregate_timestamp_trunc(self):
        """Aggregate timestamp trunc."""
        return (
            self.annotate(timestamp_trunc=TruncMinute("timestamp"))
            .values("timestamp_trunc")
            .annotate(task_runs=Count("id"))
        )

    def max_throughput(self) -> int:
        """Calculate the maximum throughput in task executions per minute."""
        qs = self.aggregate_timestamp_trunc().aggregate(Max("task_runs"))
        return qs["task_runs__max"]

    def avg_throughput(self) -> float:
        """Calculate the average throughput in task executions per minute."""
        qs = self.aggregate_timestamp_trunc().aggregate(Avg("task_runs"))
        return qs["task_runs__avg"]


class TaskLogManagerBase(models.Manager):
    def create_from_task(
        self,
        *,
        task_id: str,
        task_name: str,
        state: int,
        retries: int,
        priority: int,
        received: dt.datetime = None,
        started: dt.datetime = None,
        parent_id: str = None,
        exception=None,
    ) -> models.Model:
        """Create new object from a celery task."""
        args = {
            "app_name": extract_app_name(task_name),
            "priority": priority,
            "parent_id": UUID(parent_id) if parent_id else None,
            "received": received,
            "retries": retries,
            "started": started,
            "state": state,
            "task_id": UUID(task_id),
            "task_name": task_name,
            "timestamp": timezone.now(),
        }
        if exception:
            args["exception"] = str(exception)
            if traceback := getattr(exception, "__traceback__"):
                args["traceback"] = "".join(
                    tb.format_exception(None, value=exception, tb=traceback)
                )
        return self.create(**args)


TaskLogManager = TaskLogManagerBase.from_queryset(TaskLogQuerySet)
