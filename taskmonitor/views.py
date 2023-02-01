import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render

from allianceauth import NAME as site_header
from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__, tasks
from .app_settings import TASKMONITOR_DATA_MAX_AGE
from .core import cached_reports, celery_queues
from .helpers import Echo
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@staff_member_required
def admin_taskmonitor_download_csv(request) -> StreamingHttpResponse:
    """Return all tasklogs as CSV file for download."""
    queryset = TaskLog.objects.order_by("pk")
    model = queryset.model
    exclude_fields = ("traceback", "args", "kwargs", "result")

    logger.info("Preparing to export the task log with %s entries.", queryset.count())

    fields = [
        field
        for field in model._meta.fields + model._meta.many_to_many
        if field.name not in exclude_fields
    ]
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=";")
    return StreamingHttpResponse(
        (writer.writerow(row) for row in queryset.csv_line_generator(fields)),
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="tasklogs.csv"'},
    )


@login_required
@staff_member_required
def admin_taskmonitor_reports(request):
    """Show the reports page."""
    context = {
        "title": "Reports",
        "site_header": site_header,
        "cl": {"opts": TaskLog._meta},
        "data_max_age": TASKMONITOR_DATA_MAX_AGE,
        "debug_mode": settings.DEBUG,
    }
    context.update(cached_reports.data())
    return render(request, "admin/taskmonitor/tasklog/reports.html", context)


@login_required
@staff_member_required
def admin_taskmonitor_reports_clear_cache(request):
    """Reload the reports page with cleared cache."""
    cached_reports.clear_cache()
    return redirect("taskmonitor:admin_taskmonitor_reports")


@login_required
@staff_member_required
def admin_taskmonitor_reports_recalculation(request):
    """Start the reports recalculation."""
    tasks.refresh_reports_cache.apply_async(priority=tasks.DEFAULT_TASK_PRIORITY)
    messages.info(
        request,
        (
            "Reports are being recalculated, which can take a while. "
            "Please reload this page in a minute to see the update."
        ),
    )
    return redirect("taskmonitor:admin_taskmonitor_reports")


@login_required
@staff_member_required
def admin_taskmonitor_report_data(request, report_name: str):
    """Data for a report."""
    try:
        data = {"data": cached_reports.report_data(report_name)}
    except KeyError:
        raise Http404(f'No report with name: "{report_name}"')
    return JsonResponse(data)


@login_required
@staff_member_required
def admin_queued_task_purge(request):
    """Purge the task queue."""
    queue_length = celery_queues.queue_length()
    celery_queues.clear_tasks()
    messages.info(request, f"Purged queue with {queue_length:,} tasks.")
    return redirect("admin:taskmonitor_queuedtask_changelist")


@login_required
@staff_member_required
def admin_queued_task_clear_cache(request):
    """Clear the cache for queued tasks."""
    celery_queues.local_cache.clear()
    return redirect("admin:taskmonitor_queuedtask_changelist")
