import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from allianceauth import NAME as site_header
from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import TASKMONITOR_DATA_MAX_AGE
from .core import cached_reports
from .helpers import Echo
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@staff_member_required
def admin_taskmonitor_download_csv(request) -> StreamingHttpResponse:
    """Return all tasklogs as CSV file for download."""
    queryset = TaskLog.objects.order_by("pk")
    model = queryset.model
    exclude_fields = ("traceback",)

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
    }
    context.update(cached_reports.data())
    return render(request, "admin/taskmonitor/tasklog/reports.html", context)


@login_required
@staff_member_required
def admin_taskmonitor_reports_clear_cache(request):
    """Reload the reports page with cleared cache."""
    cached_reports.clear_cache()
    return redirect("taskmonitor:admin_taskmonitor_reports")
