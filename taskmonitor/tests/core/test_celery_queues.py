import json
from collections import defaultdict
from unittest import mock

import redis

from django.conf import settings
from django.test import TestCase

from taskmonitor.core import celery_queues

from ..factories import QueuedTaskRawFactory

CELERY_QUEUE_NAME = "test_task_monitor_celery"
MODULE_PATH = "taskmonitor.core.celery_queues"


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


@mock.patch(MODULE_PATH + "._queue_base_name")
class TestCore(TestCase):
    def setUp(self):
        self.r = _redis_client()
        self._clear_queue()

    def tearDown(self):
        self._clear_queue()

    def _clear_queue(self):
        for queue_name in celery_queues._queue_names(CELERY_QUEUE_NAME):
            self.r.delete(queue_name)

    def _push_tasks(self, raw_tasks):
        tasks_by_priority = defaultdict(list)
        for task in raw_tasks:
            priority = task["properties"]["priority"]
            tasks_by_priority[priority].append(task)
        for priority, tasks in tasks_by_priority.items():
            raw_tasks_str = [json.dumps(obj) for obj in tasks]
            queue_name = f"{CELERY_QUEUE_NAME}{celery_queues.PRIORITY_SEP}{priority}"
            self.r.lpush(queue_name, *raw_tasks_str)

    def test_should_return_queue_length(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_tasks = [QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        self._push_tasks(raw_tasks)
        # when/then
        self.assertEqual(celery_queues.queue_length(), 2)

    def test_should_fetch_tasks_in_correct_order(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_task_1 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_2 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_3 = QueuedTaskRawFactory(properties__priority=3)
        self._push_tasks([raw_task_1, raw_task_2, raw_task_3])
        # when
        result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], raw_task_3)
        self.assertEqual(result[1], raw_task_1)
        self.assertEqual(result[2], raw_task_2)
