from unittest.mock import patch

from django.utils.timezone import now

from app_utils.testing import NoSocketsTestCase

from taskmonitor.core import task_logs
from taskmonitor.models import TaskLog

from ..factories import SenderStub, TaskLogFactory

MODULE_PATH = "taskmonitor.core.task_logs"


@patch(MODULE_PATH + ".celery_queues.queue_length_cached", lambda: 0)
@patch(MODULE_PATH + ".task_records.fetch", spec=True)
@patch(MODULE_PATH + ".run_housekeeping_if_stale", spec=True)
class TestTaskFailureHandler(NoSocketsTestCase):
    def test_should_create_log_for_complete_task(
        self, mock_run_housekeeping_if_stale, mock_task_records_fetch
    ):
        # given
        mock_task_records_fetch.return_value = now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
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
        self.assertTrue(mock_run_housekeeping_if_stale.called)

    def test_should_create_log_for_task_without_delivery_info(
        self, mock_run_housekeeping_if_stale, mock_task_records_fetch
    ):
        # given
        mock_task_records_fetch.return_value = now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        sender.request.delivery_info = None
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
        self.assertTrue(mock_run_housekeeping_if_stale.called)


@patch(MODULE_PATH + ".celery_queues.queue_length_cached", lambda: 0)
@patch(MODULE_PATH + ".task_records.fetch", spec=True)
@patch(MODULE_PATH + ".run_housekeeping_if_stale", spec=True)
class TestTaskInternalErrorHandler(NoSocketsTestCase):
    def test_should_create_log_for_complete_task(
        self, mock_run_housekeeping_if_stale, mock_task_records_fetch
    ):
        # given
        mock_task_records_fetch.return_value = now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        # when
        task_logs.task_internal_error_handler_2(
            sender=sender,
            task_id=str(expected.task_id),
            request=sender.request.asdict(),
            exception=None,
        )
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.FAILURE
            ).exists()
        )
        self.assertTrue(mock_run_housekeeping_if_stale.called)

    def test_should_create_log_for_task_without_delivery_info_1(
        self, mock_run_housekeeping_if_stale, mock_task_records_fetch
    ):
        # given
        mock_task_records_fetch.return_value = now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        sender.request.delivery_info = None
        # when
        task_logs.task_internal_error_handler_2(
            sender=sender,
            task_id=str(expected.task_id),
            request=sender.request.asdict(),
            exception=None,
        )
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.FAILURE
            ).exists()
        )
        self.assertTrue(mock_run_housekeeping_if_stale.called)

    def test_should_create_log_for_task_without_delivery_info_2(
        self, mock_run_housekeeping_if_stale, mock_task_records_fetch
    ):
        # given
        mock_task_records_fetch.return_value = now()
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        request = sender.request.asdict()
        del request["delivery_info"]
        # when
        task_logs.task_internal_error_handler_2(
            sender=sender,
            task_id=str(expected.task_id),
            request=request,
            exception=None,
        )
        # then
        self.assertTrue(
            TaskLog.objects.filter(
                task_id=expected.task_id, state=TaskLog.State.FAILURE
            ).exists()
        )
        self.assertTrue(mock_run_housekeeping_if_stale.called)
