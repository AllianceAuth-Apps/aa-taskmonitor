import datetime as dt
import json
import traceback as tb
from typing import List
from uuid import UUID

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Avg, Count, Max, Min
from django.db.models.functions import TruncMinute
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.database import TableSizeMixin
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import (
    TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT,
    TASKMONITOR_TRUNCATE_NESTED_DATA,
)
from .core import celery_queues
from .helpers import extract_app_name, truncate_dict, truncate_list, truncate_result

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class QuerySetQueryStub:
    def __init__(self) -> None:
        self.select_related = None
        self.order_by = []


class ListAsQuerySet(list):
    """Masquerade a list as QuerySet."""

    def __init__(self, *args, model, distinct=False, **kwargs):
        self.model = model
        self.query = QuerySetQueryStub()
        self.distinct_enabled = distinct
        super().__init__(*args, **kwargs)
        self._id_mapper = {str(obj.id): n for n, obj in enumerate(self)}
        self._list_size = len(self)

    def all(self) -> models.QuerySet:
        return self

    def none(self) -> models.QuerySet:
        return ListAsQuerySet([], model=self.model)

    def get(self, *args, **kwargs):
        try:
            return self[self._id_mapper[str(kwargs["id"])]]
        except KeyError:
            raise self.model.DoesNotExist from None

    def distinct(self):
        return ListAsQuerySet(list(set(self)), model=self.model, distinct=True)

    def values(self, *args):
        result = [
            {k: v for k, v in obj.__dict__.items() if not args or k in args}
            for obj in self
        ]
        return result

    def values_list(self, *args, **kwargs):
        items = [tuple(obj.values()) for obj in self.values(*args)]
        if kwargs.get("flat"):
            items = [obj[0] for obj in items]
            if self.distinct_enabled:
                return list(dict.fromkeys(items))
            return items
        return items

    def first(self):
        return self[0] if self else None

    def filter(self, *args, **kwargs):
        if args:
            raise NotImplementedError("filter with positional args not supported.")
        if not kwargs:
            return self
        new_list = [
            obj
            for obj in self
            if all([str(getattr(obj, k)) == str(v) for k, v in kwargs.items()])
        ]
        return ListAsQuerySet(new_list, model=self.model)

    def order_by(self, *args, **kwargs):
        if kwargs:
            raise NotImplementedError("order with kw args not supported.")
        if args:
            for prop in reversed(args):
                if prop[0:1] == "-":
                    reverse = True
                    prop = prop[1:]
                else:
                    reverse = False
                self.sort(key=lambda d: getattr(d, prop), reverse=reverse)
        return self

    def count(self):
        return self._list_size

    def _clone(self):
        return self


class QueuedTaskQuerySet(models.QuerySet):
    def count(self):
        return celery_queues.queue_length()


class QueuedTaskManagerBase(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        if celery_queues.queue_length() > TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT:
            return self._none()
        return self.from_dto_list(celery_queues.fetch_tasks())

    @staticmethod
    def _none():
        from .models import QueuedTask

        return ListAsQuerySet([], model=QueuedTask)

    @staticmethod
    def from_dto_list(tasks: list) -> models.QuerySet:
        """Create from a list of QueuedTaskShort objects."""
        from .models import QueuedTask

        objs = [
            QueuedTask.from_dto(obj, position) for position, obj in enumerate(tasks)
        ]
        return ListAsQuerySet(objs, model=QueuedTask)


QueuedTaskManager = QueuedTaskManagerBase.from_queryset(QueuedTaskQuerySet)


class TaskLogQuerySet(models.QuerySet):
    def csv_line_generator(self, fields: List[str]):
        """Return the tasklogs for a CSV file line by line.
        And return the field names as first line.
        """
        field_names = [field.name for field in fields]
        yield field_names
        for obj in self.iterator():
            values = [
                value for key, value in obj.asdict().items() if key in set(field_names)
            ]
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

    def oldest_date(self) -> dt.datetime:
        return self.aggregate(oldest=Min("timestamp"))["oldest"]

    def newest_date(self) -> dt.datetime:
        return self.aggregate(youngest=Max("timestamp"))["youngest"]


class TaskLogManagerBase(TableSizeMixin, models.Manager):
    def create_from_task(
        self,
        *,
        task_id: str,
        task_name: str,
        state: int,
        retries: int,
        priority: int,
        args: list,
        kwargs: dict,
        received: dt.datetime = None,
        started: dt.datetime = None,
        parent_id: str = None,
        exception=None,
        result=None,
        current_queue_length: int = None,
    ) -> models.Model:
        """Create new object from a celery task."""
        params = {
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
            "current_queue_length": current_queue_length,
        }
        params["args"] = (
            truncate_list(args) if TASKMONITOR_TRUNCATE_NESTED_DATA else args
        )
        params["kwargs"] = (
            truncate_dict(kwargs) if TASKMONITOR_TRUNCATE_NESTED_DATA else kwargs
        )
        try:
            json.dumps(result, cls=DjangoJSONEncoder)
        except TypeError:
            logger.warning(
                "%s [%s]: Result was not JSON serializable and therefore discarded.",
                task_name,
                task_id,
            )
            result = None
        params["result"] = (
            truncate_result(result) if TASKMONITOR_TRUNCATE_NESTED_DATA else result
        )
        if exception:
            params["exception"] = str(exception)
            if traceback := getattr(exception, "__traceback__"):
                params["traceback"] = "".join(
                    tb.format_exception(None, value=exception, tb=traceback)
                )
        return self.create(**params)


TaskLogManager = TaskLogManagerBase.from_queryset(TaskLogQuerySet)
