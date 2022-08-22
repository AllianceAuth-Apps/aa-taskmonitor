import csv

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .models import TaskLogEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@staff_member_required
def admin_taskanalytics_download_csv(request):
    queryset = TaskLogEntry.objects.order_by("pk")
    model = queryset.model
    exclude_fields = ("traceback",)

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
