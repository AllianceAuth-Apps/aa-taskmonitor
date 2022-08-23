from dataclasses import dataclass
from unittest.mock import patch

from django.test import TestCase

from taskanalytics.core import TASK_RECEIVED, TASK_STARTED, TaskRecords
from taskanalytics.models import TaskLogEntry

from .factories import TaskLogEntryFactory

MODELS_PATH = "taskanalytics.models"


@dataclass
class RequestStub:
    id: str
    retries: int
    task: str
    parent_id: str = None


@dataclass
class SenderStub:
    request: RequestStub
    priority: int

    @classmethod
    def create_from_obj(cls, obj: TaskLogEntry):
        request = RequestStub(
            parent_id=obj.parent_id,
            retries=obj.retries,
            task=obj.task_name,
            id=obj.task_id,
        )
        return cls(request=request, priority=obj.priority)


class TestManagerCreateFromTask(TestCase):
    def test_should_create_from_succeeded_task(self):
        # given
        expected = TaskLogEntryFactory.build(state=TaskLogEntry.State.SUCCESS)
        sender = SenderStub.create_from_obj(expected)
        records = TaskRecords()
        records.set(expected.task_id, TASK_RECEIVED, expected.received)
        records.set(expected.task_id, TASK_STARTED, expected.started)
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLogEntry.objects.create_from_task(
                state=expected.state, records=records, sender=sender
            )
        # then
        self._assert_equal_objs(expected, result)

    def test_should_create_from_failed_task(self):
        # given
        expected = TaskLogEntryFactory.build(
            state=TaskLogEntry.State.FAILURE, exception=None, traceback=None
        )
        sender = SenderStub.create_from_obj(expected)
        other_task = TaskLogEntryFactory()
        sender.request.id = other_task.task_id  # now different from expected
        records = TaskRecords()
        records.set(expected.task_id, TASK_RECEIVED, expected.received)
        records.set(expected.task_id, TASK_STARTED, expected.started)
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLogEntry.objects.create_from_task(
                state=expected.state,
                records=records,
                sender=sender,
                task_id=expected.task_id,
            )
        # then
        self._assert_equal_objs(expected, result)

    def test_should_create_from_retried_task(self):
        # given
        expected = TaskLogEntryFactory.build(
            state=TaskLogEntry.State.RETRY, exception=None, traceback=None
        )
        sender = SenderStub.create_from_obj(expected)
        sender_no_request = SenderStub.create_from_obj(expected)
        sender_no_request.request = None
        records = TaskRecords()
        records.set(expected.task_id, TASK_RECEIVED, expected.received)
        records.set(expected.task_id, TASK_STARTED, expected.started)
        # when
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = expected.timestamp
            result = TaskLogEntry.objects.create_from_task(
                state=expected.state,
                records=records,
                sender=sender_no_request,
                request=sender.request,
            )
        # then
        self._assert_equal_objs(expected, result)

    def _assert_equal_objs(self, expected, result):
        field_names = {
            field.name for field in TaskLogEntry._meta.fields if field.name != "id"
        }
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(expected, field_name), getattr(result, field_name)
                )
