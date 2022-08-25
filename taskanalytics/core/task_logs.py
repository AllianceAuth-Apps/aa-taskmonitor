"""Create tasklogs from executed celery tasks."""

from django.core.cache import cache
from django.utils import timezone

from ..app_settings import TASKANALYTICS_HOUSEKEEPING_FREQUENCY
from ..models import TaskLog
from ..tasks import DEFAULT_TASK_PRIORITY, run_housekeeping
from .task_records import TaskRecords

TASK_RECEIVED = "received"
TASK_STARTED = "started"

CACHE_KEY = "TASKANALYTICS_LAST_HOUSEKEEPING"


def run_housekeeping_if_stale():
    """Spawn a task to run house keeping if last run was too long ago."""
    was_expired = cache.add(
        key=CACHE_KEY,
        value="no-value",
        timeout=TASKANALYTICS_HOUSEKEEPING_FREQUENCY * 60,
    )
    if was_expired:
        run_housekeeping.apply_async(priority=DEFAULT_TASK_PRIORITY)


def task_received_handler_2(request):
    """Handle task received signal."""
    if request:
        records.set(request.id, TASK_RECEIVED, timezone.now())


def task_prerun_handler_2(task_id):
    """Handle task prerun signal."""
    if task_id:
        records.set(task_id, TASK_STARTED, timezone.now())


def task_retry_handler_2(sender, request, reason):
    """Handle task retry signal."""
    if sender and request:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.RETRY,
            records=records,
            sender=sender,
            request=request,
            exception=reason,
        )
    run_housekeeping_if_stale()


def task_success_handler_2(sender):
    """Handle task success signal."""
    if sender and sender.request:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.SUCCESS, records=records, sender=sender
        )
    run_housekeeping_if_stale()


def task_failure_handler_2(sender, task_id, exception):
    """Handle task failure signal."""
    if sender and task_id:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.FAILURE,
            records=records,
            sender=sender,
            task_id=task_id,
            exception=exception,
        )
    run_housekeeping_if_stale()


def task_internal_error_handler_2(task_id, request, exception):
    """Handle task internal error signal."""
    if task_id and request:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.FAILURE,
            records=records,
            request=request,
            task_id=task_id,
            exception=exception,
        )
    run_housekeeping_if_stale()


records = TaskRecords()
