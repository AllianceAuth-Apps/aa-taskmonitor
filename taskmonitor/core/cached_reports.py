"""Container for caching the reports data used in views."""

import datetime as dt
import inspect
import re
import sys
from typing import List, Optional

from django.core.cache import cache
from django.db.models import Count, F, Max, Min, Sum, Value
from django.db.models.functions import Concat, TruncMinute
from django.urls import reverse
from django.utils import functional, timezone

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
        # Set name as Class name in snake case
        self.name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__class__.__name__).lower()

    @functional.cached_property
    def changelist_url(self) -> str:
        return reverse("admin:taskmonitor_tasklog_changelist")

    @functional.cached_property
    def total_runs(self) -> int:
        return TaskLog.objects.count()

    @functional.cached_property
    def total_runtime(self):
        return TaskLog.objects.aggregate(total_runtime=Sum("runtime"))["total_runtime"]

    @property
    def total_runtime_date(self):
        try:
            return self.now - dt.timedelta(seconds=self.total_runtime)
        except TypeError:
            return None

    @property
    def cache_key(self):
        return f"{CACHE_KEY}_{self.name}"

    @property
    def timeout(self):
        """Timeout in seconds."""
        return TASKMONITOR_REPORTS_MAX_AGE * 60

    @functional.cached_property
    def now(self) -> dt.datetime:
        return timezone.now()

    def data(self) -> list:
        return cache.get_or_set(self.cache_key, self._calc_data, timeout=self.timeout)

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

    @classmethod
    def report_classes(cls):
        return [
            obj
            for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(obj, cls) and obj is not cls
        ]


class BasicInformation(_CachedReport):
    def _calc_data(self):
        oldest_date = TaskLog.objects.aggregate(oldest=Min("timestamp"))["oldest"]
        youngest_date = TaskLog.objects.aggregate(youngest=Max("timestamp"))["youngest"]
        return {
            "oldest_date": oldest_date,
            "youngest_date": youngest_date,
            "total_runs": self.total_runs,
            "total_runtime_date": self.total_runtime_date,
            "MAX_TOP": TASKMONITOR_REPORTS_MAX_TOP,
        }


class TaskRunsByState(_CachedReport):
    def _calc_data(self):
        if not self.total_runs:
            return None
        return [
            {
                "name": state.label,
                "y": TaskLog.objects.filter(state=state.value).count(),
                "url": f"{self.changelist_url}?state__exact={state}",
            }
            for state in TaskLog.State
        ]


class TaskRunsByApp(_CachedReport):
    def _calc_data(self):
        if not self.total_runs:
            return None
        data = list(
            TaskLog.objects.values(name=F("app_name"))
            .annotate(y=Count("pk"))
            .annotate(url=Concat(Value(f"{self.changelist_url}?app_name="), F("name")))
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
        if not self.total_runs:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Count("pk"))
            .annotate(url=Concat(Value(f"{self.changelist_url}?task_name="), F("name")))
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopRuntime(_CachedReport):
    def _calc_data(self):
        if not self.total_runtime:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Max("runtime"))
            .annotate(
                url=Concat(Value(f"{self.changelist_url}?o=5&task_name="), F("name"))
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
                    Value(f"{self.changelist_url}?state__exact=3&task_name="), F("name")
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
                    Value(f"{self.changelist_url}?state__exact=2&task_name="), F("name")
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
            result = (
                TaskLog.objects.filter(state=state)
                .annotate(x=TruncMinute("timestamp"))
                .values("x")
                .annotate(y=Count("id"))
            )
            data = [[int(obj["x"].timestamp() * 1000), obj["y"]] for obj in result]
            series.append({"name": state.label, "data": data})
        return series


class TasksThroughputByApp(_CachedReport):
    is_included = False

    def _calc_data(self):
        series = []
        app_names = [app["name"] for app in report("task_runs_by_app").data()]
        real_app_name = {name for name in app_names if name != APP_NAME_OTHERS}
        for app_name in app_names:
            if app_name in real_app_name:
                app_qs = TaskLog.objects.filter(app_name=app_name)
            else:
                app_qs = TaskLog.objects.exclude(app_name__in=real_app_name)
            result = (
                app_qs.annotate(x=TruncMinute("timestamp"))
                .values("x")
                .annotate(y=Count("id"))
            )
            data = [[int(obj["x"].timestamp() * 1000), obj["y"]] for obj in result]
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


def report_data(report_name: str):
    """Data of an cached report."""
    return report(report_name).data()


def reports() -> List[_CachedReport]:
    """List of all cached reports."""
    return _reports.values()


def report(report_name: str) -> _CachedReport:
    """Access report by name."""
    return _reports[report_name]


# Instantiation of all cached reports
_reports = {obj.name: obj for obj in [cls() for cls in _CachedReport.report_classes()]}
