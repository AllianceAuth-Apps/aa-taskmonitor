import tempfile
import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import redirect

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@staff_member_required
def admin_taskanalytics_download_csv(request):
    hash = str(uuid.uuid4())
    return redirect("taskanalytics:admin_taskanalytics_download_csv_file", hash)


@login_required
@staff_member_required
def admin_taskanalytics_download_csv_file(request, hash: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_file = TaskLog.objects.export_to_csv(temp_dir)
        logger.info("Returning file %s for download of topic", zip_file)
        return FileResponse(zip_file.open("rb"))
