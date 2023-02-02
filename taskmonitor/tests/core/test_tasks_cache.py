from django.core.cache import cache
from django.test import TestCase

from taskmonitor.core.tasks_cache import CacheApi, QueuedTaskShort

from ..factories import QueuedTaskRawFactory


class TestCacheAPi(TestCase):
    CACHE_KEY = "test-cache-api-cache-key"

    def setUp(self) -> None:
        cache.delete(self.CACHE_KEY)

    def test_should_store_and_fetch_from_cache(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY, 60)
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
        local_cache = CacheApi(self.CACHE_KEY, 60)
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        local_cache.set(tasks)
        data = local_cache.get()
        # when
        result = local_cache.created_at()
        # then
        self.assertEqual(result, data.created_at)

    def test_should_return_none_for_created_at_when_cache_invalid(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY, 60)
        # when
        result = local_cache.created_at()
        # then
        self.assertIsNone(result)

    def test_should_disable_cache(self):
        # given
        local_cache = CacheApi(self.CACHE_KEY, 0)
        tasks = [QueuedTaskShort.from_dict(QueuedTaskRawFactory())]
        local_cache.set(tasks)
        # when
        result = local_cache.get()
        # then
        self.assertIsNone(result)
