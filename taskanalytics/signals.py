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
def task_retry_handler(request=None, reason=None, **kw):
    if request:
        task_id = request.id
        task_name = request.task
        TaskLogEntry.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(reason) if reason else None,
            received=records.fetch(task_id, TASK_RECEIVED),
            retries=request.retries,
            started=records.fetch(task_id, TASK_STARTED),
            state=TaskLogEntry.State.RETRY,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if reason else "",
        )
    run_housekeeping_if_stale()


@task_success.connect
def task_success_handler(sender=None, **kw):
    if sender and sender.request:
        task_id = sender.request.id
        task_name = sender.request.task
        TaskLogEntry.objects.create(
            app_name=extract_app_name(task_name),
            received=records.fetch(task_id, TASK_RECEIVED),
            retries=sender.request.retries,
            started=records.fetch(task_id, TASK_STARTED),
            state=TaskLogEntry.State.SUCCESS,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
        )
    run_housekeeping_if_stale()


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, **kw
):
    if sender and task_id:
        task_name = sender.request.task if sender.request else ""
        TaskLogEntry.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(exception) if exception else "",
            received=records.fetch(task_id, TASK_RECEIVED),
            retries=sender.request.retries if sender.request else None,
            started=records.fetch(task_id, TASK_STARTED),
            state=TaskLogEntry.State.FAILURE,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if traceback else "",
        )
    run_housekeeping_if_stale()


@task_internal_error.connect
def task_internal_error_handler(
    task_id=None, request=None, exception=None, traceback=None, **kw
):
    if task_id and request:
        task_name = request.task
        TaskLogEntry.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(exception) if exception else "",
            received=records.fetch(task_id, TASK_RECEIVED),
            retries=request.retries,
            started=records.fetch(task_id, TASK_STARTED),
            state=TaskLogEntry.State.FAILURE,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if traceback else "",
        )
    run_housekeeping_if_stale()
