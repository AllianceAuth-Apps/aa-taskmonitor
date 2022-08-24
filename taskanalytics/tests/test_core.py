from django.test import TestCase

from taskanalytics.core.tasklogs import TaskRecords


class TestTaskRecords(TestCase):
    def test_should_store_and_retrieve_data(self):
        # given
        records = TaskRecords()
        # when
        records.set("abc", "alpha", 5)
        result = records.get("abc", "alpha")
        # then
        self.assertEqual(result, 5)

    def test_should_delete_data(self):
        # given
        records = TaskRecords()
        # when
        records.set("abc", "alpha", 5)
        result = records.fetch("abc", "alpha")
        # then
        self.assertEqual(result, 5)
        self.assertIsNone(records.get("abc", "alpha"))
