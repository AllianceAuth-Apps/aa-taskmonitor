from unittest.mock import patch

# from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from taskanalytics.core import task_logs
from taskanalytics.models import TaskLog

from .factories import TaskLogFactory
from .helpers import SenderStub

# from app_utils.testdata_factories import UserFactory


CORE_PATH = "taskanalytics.core.task_logs"


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(CORE_PATH + ".TaskRecords")
class TestSignalHandlingEnd2End(TestCase):
    def test_should_create_entry_for_succeeded_task(self, mock_TaskRecords):
        # given
        mock_TaskRecords.return_value.get.return_value = timezone.now()
        expected = TaskLogFactory.build(state=TaskLog.State.SUCCESS)
        sender = SenderStub.create_from_obj(expected)
        # when
        task_logs.task_success_handler_2(sender=sender)
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
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        other_task = TaskLogFactory.build()
        sender.request.id = str(other_task.task_id)  # now different from expected
        # when
        task_logs.task_failure_handler_2(
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
            state=TaskLog.State.RETRY, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        sender_no_request = SenderStub.create_from_obj(expected)
        sender_no_request.request = None
        # when
        task_logs.task_retry_handler_2(
            sender=sender_no_request, request=sender.request, reason=None
        )
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.RETRY
            ).exists()
        )


# class TestUIEnd2End(TestCase):
#     def test_should_show_reports(self):
#         # given
#         cache.clear()
#         user = UserFactory(is_staff=True, is_superuser=True)
#         self.client.force_login(user)
#         TaskLogFactory()
#         TaskLogFactory()
#         TaskLogFactory()
#         # when
#         response = self.client.get("/taskanalytics/admin_taskanalytics_reports")
#         # then
#         self.assertEqual(response.status_code, 200)
