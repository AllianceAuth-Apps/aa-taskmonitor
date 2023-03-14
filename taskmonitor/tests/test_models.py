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


class TestTaskLogQuerySet(TestCase):
    def test_should_return_oldest_date(self):
        # given
        log_1 = TaskLogFactory()
        log_2 = TaskLogFactory(received=log_1.received - dt.timedelta(hours=1))
        # when
        result = TaskLog.objects.oldest_date()
        # then
        self.assertEqual(result, log_2.timestamp)

    def test_should_return_none_when_no_logs_for_oldest_data(self):
        # when
        result = TaskLog.objects.oldest_date()
        # then
        self.assertIsNone(result)

    def test_should_return_newest_date(self):
        # given
        log_1 = TaskLogFactory()
        TaskLogFactory(received=log_1.received - dt.timedelta(hours=1))
        # when
        result = TaskLog.objects.newest_date()
        # then
        self.assertEqual(result, log_1.timestamp)

    def test_should_return_none_when_no_logs_for_newest_data(self):
        # when
        result = TaskLog.objects.newest_date()
        # then
        self.assertIsNone(result)


class TestManagerCreateFromTask(TestCase):
    def test_should_create_from_succeeded_task(self):
        # given
        expected = TaskLogFactory.build(
            state=TaskLog.State.SUCCESS, current_queue_length=42
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
                current_queue_length=42,
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
            field.name
            for field in TaskLog._meta.fields
            if field.name not in {"id", "current_queue_length"}
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


class TestQueuedTaskManager(TestCase):
    @patch("taskmonitor.managers.celery_queues", spec=True)
    def test_get_queryset_should_fetch_from_celery_queues(self, mock_celery_queues):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        mock_celery_queues.queue_length.return_value = 2
        mock_celery_queues.fetch_tasks.return_value = make_dto_list(
            [queued_task_raw, QueuedTaskRawFactory()]
        )
        # when
        qs = QueuedTask.objects.all()
        # then
        self.assertEqual(len(qs), 2)
        self.assertEqual(qs[0].id, queued_task_raw["headers"]["id"])

    def test_should_support_all(self):
        # given
        tasks = make_dto_list([QueuedTaskRawFactory(), QueuedTaskRawFactory()])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when/then
        result = qs.all()
        self.assertEqual(qs, result)

    def test_should_support_count(self):
        # given
        tasks = make_dto_list([QueuedTaskRawFactory(), QueuedTaskRawFactory()])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when/then
        self.assertEqual(qs.count(), 2)

    def test_should_support_get(self):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        tasks = make_dto_list(
            [
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
                queued_task_raw,
                QueuedTaskRawFactory(),
                QueuedTaskRawFactory(),
            ]
        )
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        obj = qs.get(id=queued_task_raw["headers"]["id"])
        # then
        self.assertEqual(obj.name, queued_task_raw["headers"]["task"])

    def test_should_support_first(self):
        # given
        queued_task_raw = QueuedTaskRawFactory()
        tasks = make_dto_list(
            [queued_task_raw, QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        )
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        obj = qs.first()
        # then
        self.assertEqual(obj.name, queued_task_raw["headers"]["task"])

    def test_should_support_order_by_asc(self):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="alpha")
        tasks = make_dto_list([raw_1, raw_2])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.order_by("name")
        # then
        task_ids = [obj.id for obj in result]
        self.assertEqual(task_ids, raw_task_ids([raw_2, raw_1]))

    def test_should_support_order_by_desc(self):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="alpha")
        tasks = make_dto_list([raw_2, raw_1])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.order_by("-name")
        # then
        task_ids = [obj.id for obj in result]
        self.assertEqual(task_ids, raw_task_ids([raw_1, raw_2]))

    def test_order_by_multi(self):
        # given
        self.maxDiff = None
        raw_1 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=7)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=1)
        raw_3 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=4)
        tasks = make_dto_list([raw_1, raw_2, raw_3])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.order_by("name", "priority")
        # then
        task_ids = [obj.id for obj in result]
        self.assertEqual(task_ids, raw_task_ids([raw_3, raw_2, raw_1]))

    def test_should_support_filter(self):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="bravo")
        raw_3 = QueuedTaskRawFactory(headers__task="alpha")
        tasks = make_dto_list([raw_1, raw_2, raw_3])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.filter(name="alpha")
        # then
        task_ids = [obj.id for obj in result]
        self.assertEqual(task_ids, raw_task_ids([raw_3]))

    def test_should_raise_error_when_filter_with_unsupported_params(self):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="bravo")
        raw_2 = QueuedTaskRawFactory(headers__task="bravo")
        raw_3 = QueuedTaskRawFactory(headers__task="alpha")
        tasks = make_dto_list([raw_1, raw_2, raw_3])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.filter(name="alpha")
        # then
        task_ids = [obj.id for obj in result]
        self.assertEqual(task_ids, raw_task_ids([raw_3]))

    def test_should_support_values(self):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=5)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=5)
        tasks = make_dto_list([raw_1, raw_2])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.values("name", "priority")
        # then
        self.assertEqual(
            result, [{"name": "alpha", "priority": 5}, {"name": "bravo", "priority": 5}]
        )

    def test_should_support_values_list(self):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha", properties__priority=5)
        raw_2 = QueuedTaskRawFactory(headers__task="bravo", properties__priority=5)
        tasks = make_dto_list([raw_1, raw_2])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.values_list("name", "priority")
        # then
        self.assertEqual(result, [("alpha", 5), ("bravo", 5)])

    def test_should_support_flat_values_list(self):
        # given
        raw_1 = QueuedTaskRawFactory(headers__task="alpha")
        raw_2 = QueuedTaskRawFactory(headers__task="bravo")
        tasks = make_dto_list([raw_1, raw_2])
        qs = QueuedTask.objects.from_dto_list(tasks)
        # when
        result = qs.values_list("name", flat=True)
        # then
        self.assertEqual(result, ["alpha", "bravo"])

    @patch("taskmonitor.managers.TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT", 100)
    @patch("taskmonitor.managers.celery_queues", spec=True)
    def test_get_queryset_should_return_empty_list_when_over_limit(
        self, mock_celery_queues
    ):
        # given
        mock_celery_queues.queue_length.return_value = 101
        # when
        qs = QueuedTask.objects.all()
        # then
        self.assertEqual(len(qs), 0)


def raw_task_ids(lst):
    return [obj["headers"]["id"] for obj in lst]
