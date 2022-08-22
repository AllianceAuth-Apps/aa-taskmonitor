import datetime as dt

from celery import shared_task

from django.core.cache import cache
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce
from app_utils.logging import LoggerAddTag

from . import __title__
from .app_settings import TASKANALYTICS_HOUSEKEEPING_FREQUENCY, TASKANALYTICS_LOGS_AGE
from .models import TaskLogEntry

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

CACHE_KEY = "TASKANALYTICS_LAST_HOUSEKEEPING"


def run_housekeeping_if_stale():
    """Spawn a task to run house keeping if last run was too long ago."""
    was_expired = cache.add(
        key=CACHE_KEY,
        value="no-value",
        timeout=TASKANALYTICS_HOUSEKEEPING_FREQUENCY * 60,
    )
    if was_expired:
        run_housekeeping.delay()


@shared_task(base=QueueOnce)
def run_housekeeping():
    """Remove all old task log entries."""

    old_entries = TaskLogEntry.objects.filter(
        timestamp__lte=timezone.now() - dt.timedelta(days=TASKANALYTICS_LOGS_AGE)
    )
    old_entries_count = old_entries.count()
    old_entries._raw_delete(old_entries.db)
    logger.info(f"House keeping deleted {old_entries_count:,} old entries from logs.")
