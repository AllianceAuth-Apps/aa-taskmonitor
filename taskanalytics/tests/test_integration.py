from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from taskanalytics.core import (
    task_failure_handler_2,
    task_retry_handler_2,
    task_success_handler_2,
)
from taskanalytics.models import TaskLogEntry

from .factories import TaskLogEntryFactory
from .helpers import SenderStub

CORE_PATH = "taskanalytics.core"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(CORE_PATH + ".TaskRecords")
class TestSignalHandlingEnd2End(TestCase):
    def test_should_create_entry_for_succeeded_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogEntryFactory.build(state=TaskLogEntry.State.SUCCESS)
        sender = SenderStub.create_from_obj(expected)
        # when
        task_success_handler_2(sender=sender)
        # then
        self.assertTrue(
            TaskLogEntry.objects.filter(
                task_id=expected.task_id, state=TaskLogEntry.State.SUCCESS
            ).exists()
        )

    def test_should_create_entry_for_failed_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogEntryFactory.build(
            state=TaskLogEntry.State.FAILURE, exception=None, traceback=None
        )
        sender = SenderStub.create_from_obj(expected)
        other_task = TaskLogEntryFactory.build()
        sender.request.id = str(other_task.task_id)  # now different from expected
        # when
        task_failure_handler_2(
            sender=sender, task_id=str(expected.task_id), exception=None
        )
        # then
        self.assertTrue(
            TaskLogEntry.objects.filter(
                task_id=expected.task_id, state=TaskLogEntry.State.FAILURE
            ).exists()
        )

    def test_should_create_entry_for_retried_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogEntryFactory.build(
            state=TaskLogEntry.State.RETRY, exception=None, traceback=None
        )
        sender = SenderStub.create_from_obj(expected)
        sender_no_request = SenderStub.create_from_obj(expected)
        sender_no_request.request = None
        # when
        task_retry_handler_2(
            sender=sender_no_request, request=sender.request, reason=None
        )
        # then
        self.assertTrue(
            TaskLogEntry.objects.filter(
                task_id=expected.task_id, state=TaskLogEntry.State.RETRY
            ).exists()
        )
