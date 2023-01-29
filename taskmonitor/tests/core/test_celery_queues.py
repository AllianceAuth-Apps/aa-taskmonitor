from unittest import mock

from django.test import TestCase

from taskmonitor.core import celery_queues

from ..factories import QueuedTaskRawFactory
from .queue_helpers import clear_queue, push_tasks

CELERY_QUEUE_NAME = "test_task_monitor_celery"
MODULE_PATH = "taskmonitor.core.celery_queues"


@mock.patch(MODULE_PATH + ".queue_base_name")
class TestCore(TestCase):
    def setUp(self):
        clear_queue(CELERY_QUEUE_NAME)

    def tearDown(self):
        clear_queue(CELERY_QUEUE_NAME)

    def test_should_return_queue_length(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_tasks = [QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        push_tasks(CELERY_QUEUE_NAME, raw_tasks)
        # when/then
        self.assertEqual(celery_queues.queue_length(), 2)

    def test_should_fetch_tasks_in_correct_order(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_task_1 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_2 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_3 = QueuedTaskRawFactory(properties__priority=3)
        push_tasks(CELERY_QUEUE_NAME, [raw_task_1, raw_task_2, raw_task_3])
        # when
        result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], raw_task_3)
        self.assertEqual(result[1], raw_task_1)
        self.assertEqual(result[2], raw_task_2)
