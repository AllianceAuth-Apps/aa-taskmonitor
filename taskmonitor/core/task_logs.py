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


def task_success_handler_2(sender):
    """Handle task success signal."""
    if sender and sender.request:
        task_id = sender.request.id
        TaskLog.objects.create_from_task(
            task_id=task_id,
            task_name=sender.name,
            state=TaskLog.State.SUCCESS,
            retries=sender.request.retries,
            priority=sender.request.delivery_info["priority"],
            parent_id=sender.request.parent_id,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
        )
    run_housekeeping_if_stale()


def task_retry_handler_2(sender, request, reason):
    """Handle task retry signal."""
    if sender and request:
        task_id = request.id
        TaskLog.objects.create_from_task(
            task_id=task_id,
            task_name=sender.name,
            state=TaskLog.State.RETRY,
            retries=request.retries,
            priority=request.delivery_info["priority"],
            parent_id=request.parent_id,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
            exception=reason,
        )
    run_housekeeping_if_stale()


def task_failure_handler_2(sender, task_id, exception):
    """Handle task failure signal."""
    if sender and task_id:
        TaskLog.objects.create_from_task(
            task_id=task_id,
            task_name=sender.name,
            state=TaskLog.State.FAILURE,
            retries=sender.request.retries,
            priority=sender.request.delivery_info["priority"],
            parent_id=sender.request.parent_id,
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
            exception=exception,
        )
    run_housekeeping_if_stale()


def task_internal_error_handler_2(sender, task_id, request, exception):
    """Handle task internal error signal."""
    if task_id and request:
        TaskLog.objects.create_from_task(
            task_id=task_id,
            task_name=sender.name if sender else "?",
            state=TaskLog.State.FAILURE,
            retries=request["retries"],
            priority=request["delivery_info"].get("priority"),
            parent_id=request.get("parent_id"),
            received=task_records.fetch(task_id, TASK_RECEIVED),
            started=task_records.fetch(task_id, TASK_STARTED),
            exception=exception,
        )
    run_housekeeping_if_stale()


# def request_asdict(request) -> dict:
#     """Convert a request object into a dict."""
#     return {
#         "delivery_info": request.delivery_info,
#         "retries": request.retries,
#         "parent_id": request.parent_id,
#     }
