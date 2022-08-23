import csv
import datetime as dt

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count, F, Max, Min, Sum, Value
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@staff_member_required
def admin_taskanalytics_download_csv(request):
    queryset = TaskLog.objects.order_by("pk")
    model = queryset.model
    exclude_fields = ("traceback",)

    logger.info("Preparing to export the task log with %s entries.", queryset.count())

    fields = [
        field
        for field in model._meta.fields + model._meta.many_to_many
        if field.name not in exclude_fields
    ]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="tasklogs.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow([field.name for field in fields])
    for obj in queryset.iterator():
        values = []
        for field in fields:
            if field.choices:
                value = getattr(obj, f"get_{field.name}_display")()
            else:
                value = getattr(obj, field.name)
            if callable(value):
                try:
                    value = value() or ""
                except Exception:
                    value = "Error retrieving value"
            if value is None:
                value = ""
            values.append(value)
        writer.writerow(values)
    return response


@login_required
@staff_member_required
def admin_taskanalytics_reports(request):
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
    return render(request, "admin/taskanalytics/tasklog/reports.html", context)
