from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from taskanalytics.core.task_records import TaskRecords


class TestTaskRecords(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_store_and_retrieve_data(self):
        # given
        records = TaskRecords()
        value = timezone.now()
        # when
        records.set("abc", "alpha", value)
        result = records.get("abc", "alpha")
        # then
        self.assertEqual(result, value)

    def test_should_delete_data(self):
        # given
        records = TaskRecords()
        value = timezone.now()
        # when
        records.set("abc", "alpha", value)
        result = records.fetch("abc", "alpha")
        # then
        self.assertEqual(result, value)
        self.assertIsNone(records.get("abc", "alpha"))
