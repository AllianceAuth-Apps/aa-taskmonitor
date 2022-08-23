import traceback as tb

from celery.signals import (
    task_failure,
    task_internal_error,
    task_prerun,
    task_received,
    task_retry,
    task_success,
)

from django.utils import timezone

from .core import TaskRecords, extract_app_name
from .models import TaskLogEntry
from .tasks import run_housekeeping_if_stale

records = TaskRecords()

TASK_RECEIVED = "received"
TASK_STARTED = "started"


@task_received.connect
def task_received_handler(request=None, **kw):
    if request:
        records.set(request.id, TASK_RECEIVED, timezone.now())


@task_prerun.connect
def task_prerun_handler(task_id=None, **kw):
    if task_id:
        records.set(task_id, TASK_STARTED, timezone.now())


@task_retry.connect
def task_retry_handler(sender=None, request=None, reason=None, **kw):
    if sender and request:
        store_task_info(
            state=TaskLogEntry.State.RETRY,
            records=records,
            sender=sender,
            request=request,
            exception=reason,
        )
    run_housekeeping_if_stale()


@task_success.connect
def task_success_handler(sender=None, **kw):
    if sender and sender.request:
        store_task_info(
            state=TaskLogEntry.State.SUCCESS, records=records, sender=sender
        )
    run_housekeeping_if_stale()


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, **kw
):
    if sender and task_id:
        store_task_info(
            state=TaskLogEntry.State.FAILURE,
            records=records,
            sender=sender,
            task_id=task_id,
            exception=exception,
        )
    run_housekeeping_if_stale()


@task_internal_error.connect
def task_internal_error_handler(task_id=None, request=None, exception=None, **kw):
    if task_id and request:
        store_task_info(
            state=TaskLogEntry.State.FAILURE,
            records=records,
            request=request,
            task_id=task_id,
            exception=exception,
        )
    run_housekeeping_if_stale()


def store_task_info(
    *,
    state: int,
    records: TaskRecords,
    sender=None,
    request: dict = None,
    task_id: str = None,
    exception=None,
) -> dict:
    """Build args from a task request."""
    if request is None:
        request = sender.request
    if task_id is None:
        task_id = request.id
    task_name = request.task
    args = {
        "app_name": extract_app_name(task_name),
        "parent_id": request.parent_id,
        "priority": sender.priority if sender else None,
        "received": records.fetch(task_id, TASK_RECEIVED),
        "retries": request.retries,
        "started": records.fetch(task_id, TASK_STARTED),
        "state": state,
        "task_id": task_id,
        "task_name": task_name,
        "timestamp": timezone.now(),
        "exception": str(exception) if exception else None,
        "traceback": str(tb.format_exc()) if exception else None,
    }
    return TaskLogEntry.objects.create(**args)
