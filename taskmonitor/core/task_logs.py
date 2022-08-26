"""Create tasklogs from executed celery tasks."""

from django.core.cache import cache
from django.utils import timezone

from ..app_settings import TASKMONITOR_HOUSEKEEPING_FREQUENCY
from ..models import TaskLog
from ..tasks import DEFAULT_TASK_PRIORITY, run_housekeeping
from . import task_records

TASK_RECEIVED = "received"
TASK_STARTED = "started"

CACHE_KEY = "TASKMONITOR_LAST_HOUSEKEEPING"


def run_housekeeping_if_stale():
    """Spawn a task to run house keeping if last run was too long ago."""
    was_expired = cache.add(
        key=CACHE_KEY,
        value="no-value",
        timeout=TASKMONITOR_HOUSEKEEPING_FREQUENCY * 60,
    )
    if was_expired:
        run_housekeeping.apply_async(priority=DEFAULT_TASK_PRIORITY)


def task_received_handler_2(request):
    """Handle task received signal."""
    if request:
        task_records.set(request.id, TASK_RECEIVED, timezone.now())


def task_prerun_handler_2(task_id):
    """Handle task prerun signal."""
    if task_id:
        task_records.set(task_id, TASK_STARTED, timezone.now())


def task_retry_handler_2(sender, request, reason):
    """Handle task retry signal."""
    if sender and request:
        task_id = request.id
        TaskLog.objects.create_from_task(
            state=TaskLog.State.RETRY,
            sender=sender,
            request=request,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
            exception=reason,
        )
    run_housekeeping_if_stale()


def task_success_handler_2(sender):
    """Handle task success signal."""
    if sender and sender.request:
        task_id = sender.request.id
        TaskLog.objects.create_from_task(
            state=TaskLog.State.SUCCESS,
            sender=sender,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
        )
    run_housekeeping_if_stale()


def task_failure_handler_2(sender, task_id, exception):
    """Handle task failure signal."""
    if sender and task_id:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.FAILURE,
            sender=sender,
            task_id=task_id,
            exception=exception,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
        )
    run_housekeeping_if_stale()


def task_internal_error_handler_2(task_id, request, exception):
    """Handle task internal error signal."""
    if task_id and request:
        TaskLog.objects.create_from_task(
            state=TaskLog.State.FAILURE,
            request=request,
            task_id=task_id,
            exception=exception,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
        )
    run_housekeeping_if_stale()
