"""Container for caching the reports data used in views."""

import datetime as dt
from typing import Optional

from django.core.cache import cache
from django.db.models import Count, F, Max, Min, Q, Sum, Value
from django.db.models.functions import Concat, TruncMinute
from django.urls import reverse
from django.utils import timezone

from ..app_settings import (
    TASKMONITOR_HOUSEKEEPING_FREQUENCY,
    TASKMONITOR_REPORTS_MAX_AGE,
    TASKMONITOR_REPORTS_MAX_TOP,
)
from ..models import TaskLog

CACHE_KEY = "TASKMONITOR_REPORTS_DATA"


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
    now = timezone.now()
    oldest_date = TaskLog.objects.aggregate(oldest=Min("timestamp"))["oldest"]
    youngest_date = TaskLog.objects.aggregate(youngest=Max("timestamp"))["youngest"]
    total_runtime, total_runtime_date = _calc_total_runtime(now)
    total_runs = TaskLog.objects.count()
    changelist_url = reverse("admin:taskmonitor_tasklog_changelist")
    context = {
        "oldest_date": oldest_date,
        "youngest_date": youngest_date,
        "total_runs": total_runs,
        "total_runtime_date": total_runtime_date,
        "task_totals_by_state": _calc_task_totals_by_state(total_runs, changelist_url),
        "task_runs_per_app": _calc_task_runs_per_app(total_runs, changelist_url),
        "tasks_top_runs": _calc_tasks_top_runs(total_runs, changelist_url),
        "tasks_top_runtime": _calc_tasks_top_runtime(total_runtime, changelist_url),
        "tasks_top_failed": _calc_tasks_top_failed(changelist_url),
        "tasks_top_retried": _calc_tasks_top_retried(changelist_url),
        "tasks_throughput": _calc_tasks_throughput(now),
        "tasks_throughput_2": _calc_tasks_throughput_2(now),
        "MAX_TOP": TASKMONITOR_REPORTS_MAX_TOP,
    }
    return context


def _calc_total_runtime(now):
    total_runtime = TaskLog.objects.aggregate(total_runtime=Sum("runtime"))[
        "total_runtime"
    ]
    try:
        total_runtime_date = now - dt.timedelta(seconds=total_runtime)
    except TypeError:
        total_runtime_date = None
    return total_runtime, total_runtime_date


def _calc_task_totals_by_state(total_runs, changelist_url):
    if not total_runs:
        return None
    return [
        {
            "name": state.label,
            "y": TaskLog.objects.filter(state=state.value).count(),
            "url": f"{changelist_url}?state__exact={state}",
        }
        for state in TaskLog.State
    ]


def _calc_task_runs_per_app(total_runs, changelist_url):
    if not total_runs:
        return None
    return list(
        TaskLog.objects.values(name=F("app_name"))
        .annotate(y=Count("pk"))
        .annotate(url=Concat(Value(f"{changelist_url}?app_name="), F("name")))
        .order_by("-y")
    )


def _calc_tasks_top_runs(total_runs, changelist_url):
    if not total_runs:
        return None
    return list(
        TaskLog.objects.values(name=F("task_name"))
        .annotate(y=Count("pk"))
        .annotate(url=Concat(Value(f"{changelist_url}?task_name="), F("name")))
        .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
    )


def _calc_tasks_top_runtime(total_runtime, changelist_url):
    if not total_runtime:
        return None
    return list(
        TaskLog.objects.values(name=F("task_name"))
        .annotate(y=Max("runtime"))
        .annotate(url=Concat(Value(f"{changelist_url}?o=5&task_name="), F("name")))
        .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
    )


def _calc_tasks_top_failed(changelist_url):
    total_failed = TaskLog.objects.filter(state=TaskLog.State.FAILURE).count()
    if not total_failed:
        return None
    return list(
        TaskLog.objects.filter(state=TaskLog.State.FAILURE)
        .values(name=F("task_name"))
        .annotate(y=Count("pk"))
        .annotate(
            url=Concat(Value(f"{changelist_url}?state__exact=3&task_name="), F("name"))
        )
        .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
    )


def _calc_tasks_top_retried(changelist_url):
    total_retried = TaskLog.objects.filter(state=TaskLog.State.RETRY).count()
    if not total_retried:
        return None
    return list(
        TaskLog.objects.filter(state=TaskLog.State.RETRY)
        .values(name=F("task_name"))
        .annotate(y=Count("pk"))
        .annotate(
            url=Concat(Value(f"{changelist_url}?state__exact=2&task_name="), F("name"))
        )
        .order_by("-y")[:TASKMONITOR_REPORTS_MAX_TOP]
    )


def _calc_tasks_throughput(now):
    tasklogs_not_failed = TaskLog.objects.exclude(state=TaskLog.State.FAILURE)
    tasks_throughput = []
    average_last_hours = dict()
    for hours in [1, 3, 6, 12, 24]:
        average_last_hours[hours] = tasklogs_not_failed.filter(
            timestamp__gt=now - dt.timedelta(hours=hours)
        ).avg_throughput()
    for hours, y in average_last_hours.items():
        tasks_throughput.append({"name": f"Average last {hours} hours", "y": y})
    average_overall = tasklogs_not_failed.avg_throughput()
    tasks_throughput.append({"name": "Average overall", "y": average_overall})
    peak_overall = tasklogs_not_failed.max_throughput()
    tasks_throughput.append({"name": "Peak overall", "y": peak_overall})
    return tasks_throughput


def _calc_tasks_throughput_2(now):
    result = (
        TaskLog.objects.annotate(x=TruncMinute("timestamp"))
        .values("x")
        .annotate(succeeded=Count("id", filter=Q(state=TaskLog.State.SUCCESS)))
        .annotate(retried=Count("id", filter=Q(state=TaskLog.State.RETRY)))
        .annotate(failed=Count("id", filter=Q(state=TaskLog.State.FAILURE)))
    )
    return list(result)
