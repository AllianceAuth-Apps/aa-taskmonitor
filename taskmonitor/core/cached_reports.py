"""Container for caching the reports data used in views."""

import datetime as dt
import inspect
import re
import sys
from collections import defaultdict
from statistics import mean
from typing import Callable, Iterable, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Avg, Count, F, Max, Sum, Value
from django.db.models.functions import Concat, TruncMinute
from django.urls import reverse
from django.utils import timezone

from ..app_settings import (
    TASKMONITOR_HOUSEKEEPING_FREQUENCY,
    TASKMONITOR_REPORTS_MAX_AGE,
    TASKMONITOR_REPORTS_MAX_TOP,
)
from ..models import TaskLog

CACHE_KEY = "taskmonitor_reports_data"
MAX_APPS_COUNT = 14
APP_NAME_OTHERS = "Others"


class _CachedReport:
    """Base class for a cached report."""

    is_included = True  # whether a report is included in the main group

    def __init__(self) -> None:
        self.name = self._to_snake_case(self.__class__.__name__)

    @property
    def cache_key(self):
        return f"{CACHE_KEY}_{self.name}"

    @property
    def timeout(self):
        """Timeout in seconds."""
        return TASKMONITOR_REPORTS_MAX_AGE * 60

    @property
    def now(self) -> dt.datetime:
        return timezone.now()

    @staticmethod
    def changelist_url() -> str:
        return reverse("admin:taskmonitor_tasklog_changelist")

    def data(self, use_cache=True):
        if use_cache:
            return cache.get_or_set(
                self.cache_key, self._calc_data, timeout=self.timeout
            )
        data = self._calc_data()
        cache.set(self.cache_key, data, timeout=self.timeout)
        return data

    def refresh_cache(self) -> None:
        """Refresh the cache."""
        cache.set(self.cache_key, self._calc_data(), timeout=self.timeout)

    def clear_cache(self) -> None:
        """Clear the cache."""
        cache.delete(self.cache_key)

    def last_update_at(self, ttl) -> Optional[dt.datetime]:
        """When the cache was last updated or None if there is no cache."""
        ttl = self._ttl()
        if not ttl:
            return None
        return timezone.now() - dt.timedelta(seconds=max(0, self.timeout - ttl))

    def next_update_at(self, ttl) -> Optional[dt.datetime]:
        """When the cache will be updated next (earliest) or None if no cache."""
        ttl = self._ttl()
        if not ttl:
            return None
        duration = TASKMONITOR_HOUSEKEEPING_FREQUENCY * 60 / 2 + ttl
        return timezone.now() + dt.timedelta(seconds=duration)

    def _ttl(self):
        return cache.ttl(self.cache_key)

    def _calc_data(self):
        """Calculate data."""
        raise NotImplementedError()

    @staticmethod
    def _truncate_minutes(
        func: Callable, qs: Iterable, minutes: int = 1
    ) -> List[Tuple[int, int]]:
        """Truncate data to one aggregated value over a span of minutes.

        Result will be sorted ascending by datetime.

        Args:
            - func: function which takes a list of values and returns one value
            - values: iterable of values in the format: [{"x": 1, "y": 2}, ...]
            - minutes: number of minutes to apply the function over.
            Must be a divider of 60.

        This function is necessary, because tests show that the ORM grouping
        with TruncMinute is not reliable.
        """

        def _func_or_zero(func, lst) -> int:
            return func(lst) if lst else 0

        if 60 % minutes > 0:
            raise ValueError("minutes must be a divider of 60.")
        data_raw = defaultdict(list)
        for x, y in qs.values_list("x", "y").iterator():
            new_minutes = x.minute // minutes * minutes
            new_x = x.replace(minute=new_minutes, second=0, microsecond=0)
            x_timestamp = int(new_x.timestamp() * 1000)
            data_raw[x_timestamp].append(y)
        data_raw = dict(sorted(data_raw.items()))
        data = [
            tuple([x, int(round(_func_or_zero(func, values), 0))])
            for x, values in data_raw.items()
        ]
        return data

    @staticmethod
    def _to_snake_case(name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @classmethod
    def report_classes(cls):
        return [
            obj
            for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(obj, cls) and obj is not cls
        ]


class TasksBasics(_CachedReport):
    """Basic information about tasks used by many other reports."""

    def _calc_data(self):
        total_runs = TaskLog.objects.count()
        total_runtime = TaskLog.objects.aggregate(total_runtime=Sum("runtime"))[
            "total_runtime"
        ]
        oldest_date = TaskLog.objects.oldest_date()
        newest_date = TaskLog.objects.newest_date()
        return {
            "total_runs": total_runs,
            "total_runtime": total_runtime,
            "oldest_date": oldest_date,
            "newest_date": newest_date,
        }


class QueueLengthOverTime(_CachedReport):
    is_included = False

    def _calc_data(self):
        qs = (
            TaskLog.objects.exclude(current_queue_length__isnull=True)
            .order_by("timestamp")
            .annotate(x=TruncMinute("timestamp"))
            .values("x")
            .annotate(y=Avg("current_queue_length"))
        )
        data = self._truncate_minutes(mean, qs, 5)
        return [{"name": "length", "data": data}]


class TaskStatistics(_CachedReport):
    def _calc_data(self):
        qs = (
            TaskLog.objects.values("app_name", "task_name")
            .annotate(x=Count("pk"))
            .annotate(y=Avg("runtime"))
        )
        grouped_by_app = defaultdict(list)
        for obj in qs:
            point = {
                "x": obj["x"],
                "y": obj["y"],
                "task_name": obj["task_name"],
            }
            grouped_by_app[obj["app_name"]].append(point)
        data = [{"name": name, "data": data} for name, data in grouped_by_app.items()]
        return data


class TaskRunsByState(_CachedReport):
    def _calc_data(self):
        if not report("tasks_basics").data()["total_runs"]:
            return None
        return [
            {
                "name": state.label,
                "y": TaskLog.objects.filter(state=state.value).count(),
                "url": f"{self.changelist_url()}?state__exact={state}",
            }
            for state in TaskLog.State
        ]


class TaskRunsByApp(_CachedReport):
    def _calc_data(self):
        if not report("tasks_basics").data()["total_runs"]:
            return None
        data = list(
            TaskLog.objects.values(name=F("app_name"))
            .annotate(y=Count("pk"))
            .annotate(
                url=Concat(Value(f"{self.changelist_url()}?app_name="), F("name"))
            )
            .order_by("-y")
        )
        if len(data) > MAX_APPS_COUNT:
            others_y = sum(
                [app["y"] for i, app in enumerate(data, start=1) if i > MAX_APPS_COUNT]
            )
            return data[:MAX_APPS_COUNT] + [
                {"name": APP_NAME_OTHERS, "y": others_y, "url": "#"}
            ]
        return data


class TasksTopRuns(_CachedReport):
    def _calc_data(self):
        if not report("tasks_basics").data()["total_runs"]:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Count("pk"))
            .annotate(
                url=Concat(Value(f"{self.changelist_url()}?task_name="), F("name"))
            )
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopMaxRuntime(_CachedReport):
    def _calc_data(self):
        if not report("tasks_basics").data()["total_runtime"]:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Max("runtime"))
            .annotate(
                url=Concat(Value(f"{self.changelist_url()}?o=5&task_name="), F("name"))
            )
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopAvgRuntime(_CachedReport):
    def _calc_data(self):
        if not report("tasks_basics").data()["total_runtime"]:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Avg("runtime"))
            .annotate(
                url=Concat(Value(f"{self.changelist_url()}?o=5&task_name="), F("name"))
            )
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopFailed(_CachedReport):
    def _calc_data(self):
        total_failed = TaskLog.objects.filter(state=TaskLog.State.FAILURE).count()
        if not total_failed:
            return None
        return list(
            TaskLog.objects.filter(state=TaskLog.State.FAILURE)
            .values(name=F("task_name"))
            .annotate(y=Count("pk"))
            .annotate(
                url=Concat(
                    Value(f"{self.changelist_url()}?state__exact=3&task_name="),
                    F("name"),
                )
            )
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopRetried(_CachedReport):
    def _calc_data(self):
        total_retried = TaskLog.objects.filter(state=TaskLog.State.RETRY).count()
        if not total_retried:
            return None
        return list(
            TaskLog.objects.filter(state=TaskLog.State.RETRY)
            .values(name=F("task_name"))
            .annotate(y=Count("pk"))
            .annotate(
                url=Concat(
                    Value(f"{self.changelist_url()}?state__exact=2&task_name="),
                    F("name"),
                )
            )
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksThroughput(_CachedReport):
    def _calc_data(self):
        tasklogs_not_failed = TaskLog.objects.exclude(state=TaskLog.State.FAILURE)
        tasks_throughput = []
        average_last_hours = dict()
        for hours in [1, 3, 6, 12, 24]:
            average_last_hours[hours] = tasklogs_not_failed.filter(
                timestamp__gt=self.now - dt.timedelta(hours=hours)
            ).avg_throughput()
        for hours, y in average_last_hours.items():
            tasks_throughput.append({"name": f"Average last {hours} hours", "y": y})
        average_overall = tasklogs_not_failed.avg_throughput()
        tasks_throughput.append({"name": "Average overall", "y": average_overall})
        peak_overall = tasklogs_not_failed.max_throughput()
        tasks_throughput.append({"name": "Peak overall", "y": peak_overall})
        return tasks_throughput


class TasksThroughputByState(_CachedReport):
    is_included = False

    def _calc_data(self):
        series = []
        for state in TaskLog.State:
            qs = (
                TaskLog.objects.filter(state=state)
                .order_by("timestamp")
                .annotate(x=TruncMinute("timestamp"))
                .values("x")
                .annotate(y=Count("id"))
            )
            data = self._truncate_minutes(sum, qs, 5)
            series.append({"name": state.label, "data": data})
        return series


class TasksThroughputByApp(_CachedReport):
    is_included = False

    def _calc_data(self):
        apps = report("task_runs_by_app").data()
        if not apps:
            return []
        series = []
        app_names = [app["name"] for app in apps]
        real_app_name = {name for name in app_names if name != APP_NAME_OTHERS}
        for app_name in app_names:
            if app_name in real_app_name:
                app_qs = TaskLog.objects.filter(app_name=app_name)
            else:
                app_qs = TaskLog.objects.exclude(app_name__in=real_app_name)
            qs = (
                app_qs.order_by("timestamp")
                .annotate(x=TruncMinute("timestamp"))
                .values("x")
                .annotate(y=Count("id"))
            )
            data = self._truncate_minutes(sum, qs, 5)
            series.append({"name": app_name, "data": data})
        return series


def refresh_cache() -> None:
    """Refresh the cache."""
    for report in reports():
        report.refresh_cache()


def clear_cache() -> None:
    """Clear the cache."""
    for report in reports():
        report.clear_cache()


def data() -> dict:
    """Calculate the report data."""
    return {
        report.name: report_data(report.name)
        for report in reports()
        if report.is_included
    }


def report_data(report_name: str, use_cache: bool = True):
    """Data of an cached report."""
    return report(report_name).data(use_cache)


def reports() -> List[_CachedReport]:
    """List of all cached reports."""
    return _reports.values()


def report(report_name: str) -> _CachedReport:
    """Access report by name."""
    return _reports[report_name]


# Instantiation of all cached reports
_reports = {obj.name: obj for obj in [cls() for cls in _CachedReport.report_classes()]}
