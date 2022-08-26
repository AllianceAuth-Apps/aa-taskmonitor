import datetime as dt

from celery import shared_task

from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import TASKMONITOR_DATA_MAX_AGE
from .core import cached_reports
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

DEFAULT_TASK_PRIORITY = 7


@shared_task(base=QueueOnce)
def run_housekeeping():
    """Run all housekeeping tasks."""
    delete_stale_tasklogs.apply_async(priority=DEFAULT_TASK_PRIORITY)
    refresh_reports_cache.apply_async(priority=DEFAULT_TASK_PRIORITY)


@shared_task
def delete_stale_tasklogs():
    """Delete all stale tasklogs from the database."""
    old_entries = TaskLog.objects.filter(
        timestamp__lte=timezone.now() - dt.timedelta(hours=TASKMONITOR_DATA_MAX_AGE)
    )
    old_entries_count = old_entries.count()
    old_entries._raw_delete(old_entries.db)
    logger.info(f"Deleted {old_entries_count:,} stale tasklogs.")


@shared_task
def refresh_reports_cache():
    cached_reports.refresh_cache()
    logger.info("Refreshed the reports cache.")
