from unittest.mock import patch

from django.test import TestCase

from taskmonitor.models import TaskLog

from .factories import TaskLogFactory

MODELS_PATH = "taskmonitor.models"


class TestManagerCreateFromTask(TestCase):
    def test_should_create_from_failed_task(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.FAILURE, exception="", traceback=""
        )
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
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
