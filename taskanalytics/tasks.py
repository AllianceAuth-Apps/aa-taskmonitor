from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import TASKANALYTICS_LOGS_AGE
from .models import TaskLogEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@shared_task
def run_housekeeping():
    """Cleanup Database."""

    old_entries = TaskLogEntry.objects.filter(
        time__lte=timezone.now() - timedelta(days=TASKANALYTICS_LOGS_AGE)
    )
    old_entries_count = old_entries.count()
    old_entries.delete()
    logger.info(f"House keeping deleted {old_entries_count} old entries from logs.")
