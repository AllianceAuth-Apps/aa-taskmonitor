from dataclasses import dataclass
from unittest.mock import patch

from django.test import TestCase

from taskanalytics.core import TaskRecords
from taskanalytics.models import TaskLogEntry
from taskanalytics.signals import TASK_RECEIVED, TASK_STARTED, store_task_info

from .factories import TaskLogEntryFactory

SIGNALS_PATH = "taskanalytics.signals"


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


class TestSignals(TestCase):
    def test_should_create_from_succeeded_task(self):
        # given
        template = TaskLogEntryFactory.build(state=TaskLogEntry.State.SUCCESS)
        sender = SenderStub.create_from_obj(template)
        records = TaskRecords()
        records.set(template.task_id, TASK_RECEIVED, template.received)
        records.set(template.task_id, TASK_STARTED, template.started)
        # when
        with patch(SIGNALS_PATH + ".timezone.now") as mock_now:
            mock_now.return_value = template.timestamp
            obj = store_task_info(
                state=TaskLogEntry.State.SUCCESS, records=records, sender=sender
            )
        # then
        field_names = {
            field.name for field in TaskLogEntry._meta.fields if field.name != "id"
        }
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(template, field_name), getattr(obj, field_name)
                )
