"""Celery signal bindings.

This module is kept intentionally small, since it is difficult to test signals directly.
"""
from celery.signals import (
    task_failure,
    task_internal_error,
    task_prerun,
    task_received,
    task_retry,
    task_success,
)

from .core.store_tasklogs import (
    task_failure_handler_2,
    task_internal_error_handler_2,
    task_prerun_handler_2,
    task_received_handler_2,
    task_retry_handler_2,
    task_success_handler_2,
)


@task_received.connect
def task_received_handler(request=None, **kw):
    task_received_handler_2(request)


@task_prerun.connect
def task_prerun_handler(task_id=None, **kw):
    task_prerun_handler_2(task_id)


@task_retry.connect
def task_retry_handler(sender=None, request=None, reason=None, **kw):
    task_retry_handler_2(sender=sender, request=request, reason=reason)


@task_success.connect
def task_success_handler(sender=None, **kw):
    task_success_handler_2(sender)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kw):
    task_failure_handler_2(sender, task_id, exception)


@task_internal_error.connect
def task_internal_error_handler(task_id=None, request=None, exception=None, **kw):
    task_internal_error_handler_2(task_id, request, exception)
