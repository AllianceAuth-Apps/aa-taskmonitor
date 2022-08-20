import datetime as dt
import traceback as tb
from typing import Optional

from celery.signals import (
    task_failure,
    task_internal_error,
    task_prerun,
    task_received,
    task_retry,
    task_success,
)

from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__
from .models import TaskLog

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

tasks_received = {}
tasks_started = {}


def extract_app_name(task_name: str) -> str:
    parts = task_name.split(".")
    try:
        idx = parts.index("tasks")
    except ValueError:
        if len(parts) == 2:
            return parts[0]
        else:
            return ""
    return parts[idx - 1] if idx > 0 else ""


def fetch_received(task_id: str) -> Optional[dt.datetime]:
    try:
        received = tasks_received[task_id]
        del tasks_received[task_id]
    except KeyError:
        received = None
    return received


def fetch_started(task_id) -> Optional[dt.datetime]:
    try:
        started = tasks_started[task_id]
        del tasks_started[task_id]
    except KeyError:
        started = None
    return started


@task_received.connect
def task_received_handler(request=None, **kw):
    if request:
        tasks_received[request.id] = timezone.now()


@task_prerun.connect
def task_prerun_handler(task_id=None, **kw):
    if task_id:
        tasks_started[task_id] = timezone.now()


@task_retry.connect
def task_retry_handler(request=None, reason=None, **kw):
    if request:
        task_id = request.id
        task_name = request.task
        TaskLog.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(reason) if reason else None,
            received=fetch_received(task_id),
            retries=request.retries,
            started=fetch_started(task_id),
            state=TaskLog.State.RETRY,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if reason else "",
        )


@task_success.connect
def task_success_handler(sender=None, **kw):
    if sender and sender.request:
        task_id = sender.request.id
        task_name = sender.request.task
        TaskLog.objects.create(
            app_name=extract_app_name(task_name),
            received=fetch_received(task_id),
            retries=sender.request.retries,
            started=fetch_started(task_id),
            state=TaskLog.State.SUCCESS,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
        )


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, **kw
):
    if sender and task_id:
        task_name = sender.request.task if sender.request else ""
        TaskLog.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(exception) if exception else "",
            received=fetch_received(task_id),
            retries=sender.request.retries if sender.request else None,
            started=fetch_started(task_id),
            state=TaskLog.State.FAILURE,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if traceback else "",
        )


@task_internal_error.connect
def task_internal_error_handler(
    task_id=None, request=None, exception=None, traceback=None, **kw
):
    if task_id and request:
        task_name = request.task
        TaskLog.objects.create(
            app_name=extract_app_name(task_name),
            exception=str(exception) if exception else "",
            received=fetch_received(task_id),
            retries=request.retries,
            started=fetch_started(task_id),
            state=TaskLog.State.FAILURE,
            task_id=task_id,
            task_name=task_name,
            timestamp=timezone.now(),
            traceback=str(tb.format_exc()) if traceback else "",
        )
