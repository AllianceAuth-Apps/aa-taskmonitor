"""Container for caching the reports data."""

import datetime as dt
from typing import Optional

from django.core.cache import cache
from django.db import models
from django.db.models import Count, F, Max, Min, Sum, Value
from django.utils import timezone

from ..app_settings import TASKANALYTICS_HOUSEKEEPING_FREQUENCY
from ..models import TaskLog

CACHE_KEY = "TASKANALYTICS_REPORTS_DATA"
TIMEOUT = 3600


def data() -> dict:
    """Return the cached reports data."""
    context = cache.get_or_set(CACHE_KEY, _calc_data, timeout=TIMEOUT)
    ttl = cache.ttl(CACHE_KEY)
    context["last_update_at"] = _last_update_at(ttl)
    context["next_update_at"] = _next_update_at(ttl)
    return context


def _last_update_at(ttl) -> Optional[dt.datetime]:
    """When the cache was last updated or None if there is no cache."""
    if not ttl:
        return None
    return timezone.now() - dt.timedelta(seconds=max(0, TIMEOUT - ttl))


def _next_update_at(ttl) -> Optional[dt.datetime]:
    """When the cache will be updated next (earliest) or None if no cache."""
    if not ttl:
        return None
    duration = TASKANALYTICS_HOUSEKEEPING_FREQUENCY * 60 / 2 + ttl
    return timezone.now() + dt.timedelta(seconds=duration)


def refresh_cache() -> None:
    """Refresh the cache."""
    cache.set(CACHE_KEY, _calc_data, timeout=TIMEOUT)


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
    task_totals_by_state = [
        {
            "state": state.label,
            "num_runs": (amount := TaskLog.objects.filter(state=state.value).count()),
            "p_total": amount / total_runs * 100,
        }
        for state in TaskLog.State
    ]
    task_runs_per_app = (
        TaskLog.objects.values("app_name")
        .annotate(num_runs=Count("pk"))
        .annotate(
            p_total=F("num_runs")
            / Value(total_runs, output_field=models.FloatField())
            * 100
        )
        .order_by("-num_runs")
    )
    tasks_top_runs = (
        TaskLog.objects.values("task_name")
        .annotate(num_runs=Count("pk"))
        .annotate(
            p_total=F("num_runs")
            / Value(total_runs, output_field=models.FloatField())
            * 100
        )
        .order_by("-num_runs")[:10]
    )
    tasks_top_runtime = (
        TaskLog.objects.values("task_name")
        .annotate(max_runtime=Max("runtime"))
        .order_by("-max_runtime")[:10]
    )
    context = {
        "oldest_date": oldest_date,
        "youngest_date": youngest_date,
        "total_runs": total_runs,
        "total_runtime_date": total_runtime_date,
        "task_totals_by_state": task_totals_by_state,
        "task_runs_per_app": task_runs_per_app,
        "tasks_top_runs": tasks_top_runs,
        "tasks_top_runtime": tasks_top_runtime,
    }
    return context
