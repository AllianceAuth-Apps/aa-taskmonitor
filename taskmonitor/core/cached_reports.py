"""Container for caching the reports data used in views."""

import datetime as dt
from typing import Optional

from django.core.cache import cache
from django.db import models
from django.db.models import Count, F, Max, Min, Sum, Value
from django.db.models.functions import Concat
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
    oldest_date = TaskLog.objects.aggregate(oldest=Min("timestamp"))["oldest"]
    youngest_date = TaskLog.objects.aggregate(youngest=Max("timestamp"))["youngest"]
    total_runtime = TaskLog.objects.aggregate(total_runtime=Sum("runtime"))[
        "total_runtime"
    ]
    try:
        total_runtime_date = timezone.now() - dt.timedelta(seconds=total_runtime)
    except TypeError:
        total_runtime_date = None
    total_runs = TaskLog.objects.count()
    changelist_url = reverse("admin:taskmonitor_tasklog_changelist")
    if not total_runs:
        task_totals_by_state = None
        task_runs_per_app = None
        tasks_top_runs = None
    else:
        task_totals_by_state = [
            {
                "name": state.label,
                "amount": (amount := TaskLog.objects.filter(state=state.value).count()),
                "percent": amount / total_runs * 100,
                "url": f"{changelist_url}?state__exact={state}",
            }
            for state in TaskLog.State
        ]
        task_runs_per_app = (
            TaskLog.objects.values(name=F("app_name"))
            .annotate(amount=Count("pk"))
            .annotate(
                percent=F("amount")
                / Value(total_runs, output_field=models.FloatField())
                * 100
            )
            .annotate(url=Concat(Value(f"{changelist_url}?app_name="), F("name")))
            .order_by("-amount")
        )
        tasks_top_runs = (
            TaskLog.objects.values(name=F("task_name"))
            .annotate(amount=Count("pk"))
            .annotate(
                percent=F("amount")
                / Value(total_runs, output_field=models.FloatField())
                * 100
            )
            .annotate(url=Concat(Value(f"{changelist_url}?task_name="), F("name")))
            .order_by("-amount")[:TASKMONITOR_REPORTS_MAX_TOP]
        )
    if not total_runtime:
        tasks_top_runtime = None
    else:
        tasks_top_runtime = (
            TaskLog.objects.values(name=F("task_name"))
            .annotate(amount=Max("runtime"))
            .annotate(
                percent=F("amount")
                / Value(total_runtime, output_field=models.FloatField())
                * 100
            )
            .annotate(url=Concat(Value(f"{changelist_url}?o=5&task_name="), F("name")))
            .order_by("-amount")[:TASKMONITOR_REPORTS_MAX_TOP]
        )
    total_failed = TaskLog.objects.filter(state=TaskLog.State.FAILURE).count()
    if not total_failed:
        tasks_top_failed = None
    else:
        tasks_top_failed = (
            TaskLog.objects.filter(state=TaskLog.State.FAILURE)
            .values(name=F("task_name"))
            .annotate(amount=Count("pk"))
            .annotate(
                percent=F("amount")
                / Value(total_failed, output_field=models.FloatField())
                * 100
            )
            .annotate(
                url=Concat(
                    Value(f"{changelist_url}?state__exact=3&task_name="), F("name")
                )
            )
            .order_by("-amount")[:TASKMONITOR_REPORTS_MAX_TOP]
        )
    total_retried = TaskLog.objects.filter(state=TaskLog.State.RETRY).count()
    if not total_retried:
        tasks_top_retried = None
    else:
        tasks_top_retried = (
            TaskLog.objects.filter(state=TaskLog.State.RETRY)
            .values(name=F("task_name"))
            .annotate(amount=Count("pk"))
            .annotate(
                percent=F("amount")
                / Value(total_retried, output_field=models.FloatField())
                * 100
            )
            .annotate(
                url=Concat(
                    Value(f"{changelist_url}?state__exact=2&task_name="), F("name")
                )
            )
            .order_by("-amount")[:TASKMONITOR_REPORTS_MAX_TOP]
        )
    tasklogs_not_failed = TaskLog.objects.exclude(state=TaskLog.State.FAILURE)
    tasks_throughput = [
        {"name": "Maximum", "amount": tasklogs_not_failed.max_throughput()},
        {"name": "Average", "amount": tasklogs_not_failed.avg_throughput()},
    ]
    context = {
        "oldest_date": oldest_date,
        "youngest_date": youngest_date,
        "total_runs": total_runs,
        "total_runtime_date": total_runtime_date,
        "task_totals_by_state": task_totals_by_state,
        "task_runs_per_app": task_runs_per_app,
        "tasks_top_runs": tasks_top_runs,
        "tasks_top_runtime": tasks_top_runtime,
        "tasks_top_failed": tasks_top_failed,
        "tasks_top_retried": tasks_top_retried,
        "tasks_throughput": tasks_throughput,
        "MAX_TOP": TASKMONITOR_REPORTS_MAX_TOP,
    }
    return context
