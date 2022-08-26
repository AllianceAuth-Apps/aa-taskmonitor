from unittest.mock import patch

from django.test import TestCase

from taskmonitor.models import TaskLog

from .factories import SenderStub, TaskLogFactory

MODELS_PATH = "taskmonitor.models"


class TestManagerCreateFromTask(TestCase):
    def test_should_create_from_succeeded_task(self):
        # given
        expected = TaskLogFactory.build(state=TaskLog.State.SUCCESS, priority=3)
        sender = SenderStub.create_from_obj(expected)
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLog.objects.create_from_task(
                state=expected.state,
                sender=sender,
                received=expected.received,
                started=expected.started,
            )
        # then
        self._assert_equal_objs(expected, result)

    def test_should_create_from_failed_task(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        other_task = TaskLogFactory.build()
        sender.request.id = str(other_task.task_id)  # now different from expected
        expected_task_id = str(expected.task_id)
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLog.objects.create_from_task(
                state=expected.state,
                sender=sender,
                task_id=expected_task_id,
                received=expected.received,
                started=expected.started,
            )
        # then
        self._assert_equal_objs(expected, result)

    def test_should_create_from_retried_task(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.RETRY, exception="", traceback=""
        )
        sender = SenderStub.create_from_obj(expected)
        sender_no_request = SenderStub.create_from_obj(expected)
        sender_no_request.request = None
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLog.objects.create_from_task(
                state=expected.state,
                sender=sender_no_request,
                request=sender.request,
                received=expected.received,
                started=expected.started,
            )
        # then
        self._assert_equal_objs(expected, result)

    def _assert_equal_objs(self, expected, result):
        field_names = {
            field.name for field in TaskLog._meta.fields if field.name != "id"
        }
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(expected, field_name), getattr(result, field_name)
                )
