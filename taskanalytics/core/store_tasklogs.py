"""Main logic for storing logs for celery tasks."""

from collections import defaultdict
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone

from ..app_settings import TASKANALYTICS_HOUSEKEEPING_FREQUENCY
from ..models import TaskLog
from ..tasks import DEFAULT_TASK_PRIORITY, run_housekeeping

TASK_RECEIVED = "received"
TASK_STARTED = "started"

CACHE_KEY = "TASKANALYTICS_LAST_HOUSEKEEPING"


class TaskRecords:
    """Storing key/value pairs for tasks."""

    def __init__(self) -> None:
        self._data = defaultdict(dict)

    def set(self, task_id: str, key: str, value: Any):
        self._data[str(task_id)][str(key)] = value

    def get(self, task_id: str, key: str) -> Optional[Any]:
        """Returns the value."""
        try:
            return self._data[str(task_id)][str(key)]
        except KeyError:
            return None

    def delete(self, task_id: str, key: str) -> None:
        """Removes the data from the store."""
        try:
            del self._data[str(task_id)][str(key)]
        except KeyError:
            pass

    def fetch(self, task_id: str, key: str) -> Optional[Any]:
        """Fetches the value and removes it from the store."""
        value = self.get(task_id, key)
        self.delete(task_id, key)
        return value


def extract_app_name(task_name: str) -> str:
    """Extract the app name from a typical task name."""
    parts = task_name.split(".")
    try:
        idx = parts.index("tasks")
    except ValueError:
        if len(parts) == 2:
            return parts[0]
        else:
            return ""
    return parts[idx - 1] if idx > 0 else ""


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
