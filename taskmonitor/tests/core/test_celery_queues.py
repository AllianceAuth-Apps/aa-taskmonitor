from unittest import mock

from django.test import TestCase

from taskmonitor.core import celery_queues
from taskmonitor.core.celery_queues import QueuedTaskShort

from ..factories import QueuedTaskRawFactory

CELERY_QUEUE_NAME = "test_task_monitor_celery"
MODULE_PATH = "taskmonitor.core.celery_queues"


@mock.patch(MODULE_PATH + ".default_queue_name")
class TestCeleryQueues(TestCase):
    def setUp(self):
        celery_queues.clear_tasks(CELERY_QUEUE_NAME)

    def tearDown(self):
        celery_queues.clear_tasks(CELERY_QUEUE_NAME)

    def test_should_return_queue_length(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_tasks = [QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        celery_queues.add_tasks(CELERY_QUEUE_NAME, raw_tasks)
        # when/then
        self.assertEqual(celery_queues.queue_length(), 2)

    def test_should_clear_queue(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_tasks = [QueuedTaskRawFactory(), QueuedTaskRawFactory()]
        celery_queues.add_tasks(CELERY_QUEUE_NAME, raw_tasks)
        # when
        celery_queues.clear_tasks()
        # then
        self.assertEqual(celery_queues.queue_length(), 0)

    def test_should_fetch_tasks_in_correct_order(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        raw_task_1 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_2 = QueuedTaskRawFactory(properties__priority=4)
        raw_task_3 = QueuedTaskRawFactory(properties__priority=3)
        celery_queues.add_tasks(CELERY_QUEUE_NAME, [raw_task_1, raw_task_2, raw_task_3])
        # when
        result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], QueuedTaskShort.from_dict(raw_task_3))
        self.assertEqual(result[1], QueuedTaskShort.from_dict(raw_task_1))
        self.assertEqual(result[2], QueuedTaskShort.from_dict(raw_task_2))
