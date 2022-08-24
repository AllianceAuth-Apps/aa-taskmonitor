from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from taskanalytics.core.store_tasklogs import (
    task_failure_handler_2,
    task_retry_handler_2,
    task_success_handler_2,
)
from taskanalytics.models import TaskLog

from .factories import TaskLogFactory
from .helpers import SenderStub

CORE_PATH = "taskanalytics.core.store_tasklogs"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(CORE_PATH + ".TaskRecords")
class TestSignalHandlingEnd2End(TestCase):
    def test_should_create_entry_for_succeeded_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogFactory.build(state=TaskLog.State.SUCCESS)
        sender = SenderStub.create_from_obj(expected)
        # when
        task_success_handler_2(sender=sender)
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.SUCCESS
            ).exists()
        )

    def test_should_create_entry_for_failed_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception=None, traceback=None
        )
        sender = SenderStub.create_from_obj(expected)
        other_task = TaskLogFactory.build()
        sender.request.id = str(other_task.task_id)  # now different from expected
        # when
        task_failure_handler_2(
            sender=sender, task_id=str(expected.task_id), exception=None
        )
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.FAILURE
            ).exists()
        )

    def test_should_create_entry_for_retried_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.RETRY, exception=None, traceback=None
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
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.RETRY
            ).exists()
        )
