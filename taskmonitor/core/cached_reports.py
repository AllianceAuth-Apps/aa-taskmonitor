"""Container for caching the reports data used in views."""

import datetime as dt
import inspect
import sys
from typing import Optional

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


class CachedReport:
    """A cached report."""

    name = ""

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

    @functional.cached_property
    def now(self) -> dt.datetime:
        return timezone.now()

    def data(self) -> list:
        return cache.get_or_set(
            f"{CACHE_KEY}_{self.name}", self._calc_data, timeout=_timeout()
        )

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


class TaskDates(CachedReport):
    name = "task_dates"

    def _calc_data(self):
        oldest_date = TaskLog.objects.aggregate(oldest=Min("timestamp"))["oldest"]
        youngest_date = TaskLog.objects.aggregate(youngest=Max("timestamp"))["youngest"]
        return oldest_date, youngest_date


class TaskRunsByState(CachedReport):
    name = "task_runs_by_state"

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


class TaskRunsByApp(CachedReport):
    name = "task_runs_by_app"

    def _calc_data(self):
        if not self.total_runs:
            return None
        return list(
            TaskLog.objects.values(name=F("app_name"))
            .annotate(y=Count("pk"))
            .annotate(url=Concat(Value(f"{self.changelist_url}?app_name="), F("name")))
            .order_by("-y")
        )


class TasksTopRuns(CachedReport):
    name = "tasks_top_runs"

    def _calc_data(self):
        if not self.total_runs:
            return None
        return list(
            TaskLog.objects.values(name=F("task_name"))
            .annotate(y=Count("pk"))
            .annotate(url=Concat(Value(f"{self.changelist_url}?task_name="), F("name")))
            .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
        )


class TasksTopRuntime(CachedReport):
    name = "tasks_top_runtime"

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


class TasksTopFailed(CachedReport):
    name = "tasks_top_failed"

    def _calc_data(self):
        # def _calc_tasks_top_failed(changelist_url):
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


class TasksTopRetried(CachedReport):
    name = "tasks_top_retried"

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


class TasksThroughput(CachedReport):
    name = "tasks_throughput"

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


class TasksThroughputByState(CachedReport):
    name = "tasks_throughput_by_state"

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


class TasksThroughputByApp(CachedReport):
    name = "tasks_throughput_by_app"

    def _calc_data(self):
        series = []
        apps = (
            TaskLog.objects.values_list("app_name", flat=True)
            .distinct()
            .order_by("app_name")
        )
        for app_name in apps:
            result = (
                TaskLog.objects.filter(app_name=app_name)
                .annotate(x=TruncMinute("timestamp"))
                .values("x")
                .annotate(y=Count("id"))
            )
            data = [[int(obj["x"].timestamp() * 1000), obj["y"]] for obj in result]
            series.append({"name": app_name, "data": data})
        return series


def data() -> dict:
    """Return the cached reports data."""
    context = cache.get_or_set(CACHE_KEY, _calc_data, timeout=_timeout())
    ttl = cache.ttl(CACHE_KEY)
    context["last_update_at"] = _last_update_at(ttl)
    context["next_update_at"] = _next_update_at(ttl)
    return context


def _timeout() -> int:
    """Timeout in seconds."""
    return TASKMONITOR_REPORTS_MAX_AGE * 60


def _last_update_at(ttl) -> Optional[dt.datetime]:
    """When the cache was last updated or None if there is no cache."""
    if not ttl:
        return None
    return timezone.now() - dt.timedelta(seconds=max(0, _timeout() - ttl))


def _next_update_at(ttl) -> Optional[dt.datetime]:
    """When the cache will be updated next (earliest) or None if no cache."""
    if not ttl:
        return None
    duration = TASKMONITOR_HOUSEKEEPING_FREQUENCY * 60 / 2 + ttl
    return timezone.now() + dt.timedelta(seconds=duration)


def refresh_cache() -> None:
    """Refresh the cache."""
    cache.set(CACHE_KEY, _calc_data(), timeout=_timeout())


def clear_cache() -> None:
    """Clear the cache."""
    cache.delete(CACHE_KEY)


def _calc_data() -> dict:
    """Calculate the report data."""
    # oldest_date, youngest_date = _reports["task_dates"].data()
    context = {
        "oldest_date": None,
        "youngest_date": None,
        "total_runs": _reports["task_runs_by_state"].total_runs,
        "total_runtime_date": _reports["task_runs_by_state"].total_runtime_date,
        "task_totals_by_state": _reports["task_runs_by_state"].data(),
        "task_runs_per_app": _reports["task_runs_by_app"].data(),
        "tasks_top_runs": _reports["tasks_top_runs"].data(),
        "tasks_top_runtime": _reports["tasks_top_runtime"].data(),
        "tasks_top_failed": _reports["tasks_top_failed"].data(),
        "tasks_top_retried": _reports["tasks_top_retried"].data(),
        "tasks_throughput": _reports["tasks_throughput"].data(),
        "tasks_throughput_by_state": _reports["tasks_throughput_by_state"].data(),
        "tasks_throughput_by_app": _reports["tasks_throughput_by_app"].data(),
        "MAX_TOP": TASKMONITOR_REPORTS_MAX_TOP,
    }
    return context


_reports = {obj.name: obj for obj in [cls() for cls in CachedReport.report_classes()]}
