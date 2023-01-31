import datetime as dt
import json
from typing import List
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from taskmonitor.core.celery_queues import QueuedTaskShort
from taskmonitor.models import QueuedTask, TaskLog

from .factories import QueuedTaskRawFactory, TaskLogFactory

MODELS_PATH = "taskmonitor.models"
MANAGERS_PATH = "taskmonitor.managers"


class TestTaskLog(TestCase):
    def test_should_convert_to_json(self):
        # given
        obj = TaskLogFactory()
        # when
        data = obj.asjson()
        # then
        obj_2 = json.loads(data)
        self.assertEqual(obj_2["task_name"], obj.task_name)
        self.assertEqual(obj_2["task_id"], str(obj.task_id))


class TestManagerCreateFromTask(TestCase):
    def test_should_create_from_succeeded_task(self):
        # given
        expected = TaskLogFactory.build(state=TaskLog.State.SUCCESS)
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
                args=expected.args,
                kwargs=expected.kwargs,
                result=expected.result,
            )
        # then
        self._assert_equal_objs(expected, result)

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
                args=expected.args,
                kwargs=expected.kwargs,
                result=expected.result,
            )
        # then
        self._assert_equal_objs(expected, result)

    def test_should_truncate_args(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, args=[1, [1, 2], 3]
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", True):
            result = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
            )
        # then
        self.assertListEqual(result.args, [1, [], 3])

    def test_should_not_truncate_args(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, args=[1, [1, 2], 3]
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", False):
            result = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
            )
        # then
        self.assertListEqual(result.args, [1, [1, 2], 3])

    def test_should_truncate_kwargs(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, kwargs={"b": 2, "a": {"aa": 1}}
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", True):
            result = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
            )
        # then
        self.assertDictEqual(result.kwargs, {"a": {}, "b": 2})

    def test_should_not_truncate_kwargs(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, kwargs={"a": {"aa": 1}}
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", False):
            result = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
            )
        # then
        self.assertDictEqual(result.kwargs, {"a": {"aa": 1}})

    def test_should_truncate_result(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, result=[1, [1, 2], 3]
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", True):
            obj = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
                result=expected.result,
            )
        # then
        self.assertListEqual(obj.result, [1, [], 3])

    def test_should_not_truncate_result(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, result=[1, [1, 2], 3]
        )
        # when
        with patch(MANAGERS_PATH + ".TASKMONITOR_TRUNCATE_NESTED_DATA", False):
            obj = TaskLog.objects.create_from_task(
                task_id=str(expected.task_id),
                task_name=expected.task_name,
                state=expected.state,
                priority=expected.priority,
                retries=expected.retries,
                received=expected.received,
                started=expected.started,
                args=expected.args,
                kwargs=expected.kwargs,
                result=expected.result,
            )
        # then
        self.assertListEqual(obj.result, [1, [1, 2], 3])

    def _assert_equal_objs(self, expected, result):
        field_names = {
            field.name for field in TaskLog._meta.fields if field.name != "id"
        }
        for field_name in field_names:
            with self.subTest(field_name=field_name):
                self.assertEqual(
                    getattr(expected, field_name), getattr(result, field_name)
                )


class TestCalcThroughput(TestCase):
    def test_should_calc_max(self):
        # given
        start = timezone.now().replace(second=0)
        TaskLogFactory(timestamp=start)
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=0, seconds=2))
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=0, seconds=3))
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=1, seconds=1))
        # when
        self.assertEqual(TaskLog.objects.all().max_throughput(), 3)

    def test_should_calc_avg(self):
        # given
        start = timezone.now().replace(second=0)
        TaskLogFactory(timestamp=start)
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=0, seconds=2))
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=0, seconds=3))
        TaskLogFactory(timestamp=start + dt.timedelta(minutes=1, seconds=1))
        # when
        self.assertEqual(TaskLog.objects.all().avg_throughput(), 2)


class TestQueuedTask(TestCase):
    def test_should_create_objects_from_dict(self):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        # when
        obj = QueuedTask.from_dict(queued_task_raw, 99)
        # then
        headers = queued_task_raw["headers"]
        self.assertEqual(obj.id, headers["id"])
        self.assertEqual(
            obj.name,
            headers["task"],
        )
        properties = queued_task_raw["properties"]
        self.assertEqual(
            obj.priority,
            properties["priority"],
        )
        self.assertEqual(obj.position, 99)

    def test_should_raise_error_when_dict_incomplete(self):
        # given
        queued_task_raw = {}
        # when
        with self.assertRaises(ValueError):
            QueuedTask.from_dict(queued_task_raw, 9)


def make_dto_list(objs) -> List[QueuedTaskShort]:
    """Convert list of raw tasks into task DTOs."""
    return [QueuedTaskShort.from_dict(obj) for obj in objs]


@patch("taskmonitor.managers.celery_queues")
class TestQueuedTaskManager(TestCase):
    def test_all(self, mock_celery_queues):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [queued_task_raw, QueuedTaskRawFactory()]
        )
        # when
        qs = QueuedTask.objects.all()
        # then
        self.assertEqual(len(qs), 2)
        self.assertEqual(qs[0].id, queued_task_raw["headers"]["id"])

    def test_count(self, mock_celery_queues):
        # given
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        )
        # when/then
        self.assertEqual(QueuedTask.objects.count(), 2)

    def test_get(self, mock_celery_queues):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
                queued_task_raw,
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
            ]
        )
        # when
        obj = QueuedTask.objects.get(id=queued_task_raw["headers"]["id"])
        # then
        self.assertEqual(obj.name, queued_task_raw["headers"]["task"])

    def test_first(self, mock_celery_queues):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [queued_task_raw, QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        )
        # when
        obj = QueuedTask.objects.first()
        # then
        self.assertEqual(obj.name, queued_task_raw["headers"]["task"])

    def test_order_by_asc(self, mock_celery_queues):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="alpha")
        mock_celery_queues.fetch_tasks.return_value = make_dto_list([raw_1, raw_2])
        # when
        qs = QueuedTask.objects.order_by("name")
        # then
        task_ids = [obj.id for obj in qs]
        self.assertEqual(task_ids, raw_task_ids([raw_2, raw_1]))

    def test_order_by_desc(self, mock_celery_queues):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="alpha")
        mock_celery_queues.fetch_tasks.return_value = make_dto_list([raw_2, raw_1])
        # when
        qs = QueuedTask.objects.order_by("-name")
        # then
        task_ids = [obj.id for obj in qs]
        self.assertEqual(task_ids, raw_task_ids([raw_1, raw_2]))

    def test_order_by_multi(self, mock_celery_queues):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=7)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=1)
        raw_3 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=4)
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [raw_1, raw_2, raw_3]
        )
        # when
        qs = QueuedTask.objects.order_by("name", "priority")
        # then
        task_ids = [obj.id for obj in qs]
        self.assertEqual(task_ids, raw_task_ids([raw_3, raw_2, raw_1]))

    def test_filter(self, mock_celery_queues):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="bravo")
        raw_3 = QueuedTaskRawFactory(headers__task="alpha")
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [raw_1, raw_2, raw_3]
        )
        # when
        qs = QueuedTask.objects.filter(name="alpha")
        # then
        task_ids = [obj.id for obj in qs]
        self.assertEqual(task_ids, raw_task_ids([raw_3]))

    def test_values(self, mock_celery_queues):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=5)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=5)
        mock_celery_queues.fetch_tasks.return_value = make_dto_list([raw_1, raw_2])
        # when
        result = QueuedTask.objects.values("name", "priority")
        # then
        self.assertEqual(
            result, [{"name": "alpha", "priority": 5}, {"name": "bravo", "priority": 5}]
        )

    def test_values_list_1(self, mock_celery_queues):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=5)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=5)
        mock_celery_queues.fetch_tasks.return_value = make_dto_list([raw_1, raw_2])
        # when
        result = QueuedTask.objects.values_list("name", "priority")
        # then
        self.assertEqual(result, [("alpha", 5), ("bravo", 5)])

    def test_values_list_2(self, mock_celery_queues):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha")
        raw_2 = QueuedTaskRawFactory(headers__task="bravo")
        mock_celery_queues.fetch_tasks.return_value = make_dto_list([raw_1, raw_2])
        # when
        result = QueuedTask.objects.values_list("name", flat=True)
        # then
        self.assertEqual(result, ["alpha", "bravo"])


def raw_task_ids(lst):
    return [obj["headers"]["id"] for obj in lst]
