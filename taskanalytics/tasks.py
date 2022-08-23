import datetime as dt

from celery import shared_task

from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import TASKANALYTICS_LOGS_AGE
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

DEFAULT_TASK_PRIORITY = 7


@shared_task(base=QueueOnce)
def run_housekeeping():
    """Remove all old task log entries."""

    old_entries = TaskLog.objects.filter(
        timestamp__lte=timezone.now() - dt.timedelta(days=TASKANALYTICS_LOGS_AGE)
    )
    old_entries_count = old_entries.count()
    old_entries._raw_delete(old_entries.db)
    logger.info(f"House keeping deleted {old_entries_count:,} old entries from logs.")
