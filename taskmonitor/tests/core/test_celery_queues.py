from unittest import mock

from django.core.cache import cache
from django.test import TestCase

from taskmonitor.core import celery_queues
from taskmonitor.core.celery_queues import CacheApi, QueuedTaskShort, local_cache

from ..factories import QueuedTaskRawFactory

CELERY_QUEUE_NAME = "test_task_monitor_celery"
MODULE_PATH = "taskmonitor.core.celery_queues"


@mock.patch(MODULE_PATH + ".TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT", 10)
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
        with mock.patch(MODULE_PATH + ".cache") as m:
            m.get.return_value = None
            result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], QueuedTaskShort.from_dict(raw_task_3))
        self.assertEqual(result[1], QueuedTaskShort.from_dict(raw_task_1))
        self.assertEqual(result[2], QueuedTaskShort.from_dict(raw_task_2))

    def test_should_retrieve_tasks_from_cache(self, mock_queue_base_name):
        # given
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        local_cache.set(tasks)
        # when
        result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(result, tasks)

    def test_should_retrieve_tasks_from_redis_when_no_cache(self, mock_queue_base_name):
        # given
        mock_queue_base_name.return_value = CELERY_QUEUE_NAME
        tasks = [QueuedTaskRawFactory()]
        celery_queues.add_tasks(CELERY_QUEUE_NAME, tasks)
        # when
        result = celery_queues.fetch_tasks()
        # then
        self.assertEqual(result[0], QueuedTaskShort.from_dict(tasks[0]))


@mock.patch(MODULE_PATH + ".TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT", 60)
class TestCacheAPi(TestCase):
    CACHE_KEY = "test-cache-api-cache-key"

    def setUp(self) -> None:
        cache.delete(self.CACHE_KEY)

    def test_should_store_and_fetch_from_cache(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY)
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        # when
        local_cache.set(tasks)
        result = local_cache.get()
        # then
        self.assertEqual(result.tasks, tasks)

    def test_should_raise_error_when_cache_returned_wrong_datatype(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY)
        cache.set(key=self.CACHE_KEY, value="abc")
        # when/then
        with self.assertRaises(TypeError):
            local_cache.get()

    def test_should_clear_cache(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY)
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        local_cache.set(tasks)
        # when
        local_cache.clear()
        # then
        self.assertIsNone(local_cache.get())

    def test_should_return_created_at(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY)
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        local_cache.set(tasks)
        data = local_cache.get()
        # when
        result = local_cache.created_at()
        # then
        self.assertEqual(result, data.created_at)

    def test_should_return_none_for_created_at_when_cache_invalid(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY)
        # when
        result = local_cache.created_at()
        # then
        self.assertIsNone(result)
