from django.test import TestCase

from taskanalytics.core.store_tasklogs import TaskRecords, extract_app_name


class TestExtractAppName(TestCase):
    def test_can_extract_from_normal_task_name(self):
        # when
        result = extract_app_name("alpha.tasks.task_name")
        # then
        self.assertEqual(result, "alpha")

    def test_can_extract_from_long_task_name(self):
        # when
        result = extract_app_name("omega.alpha.tasks.task_name")
        # then
        self.assertEqual(result, "alpha")

    def test_can_extract_from_extra_long_task_name(self):
        # when
        result = extract_app_name("echo.omega.alpha.tasks.task_name")
        # then
        self.assertEqual(result, "alpha")

    def test_can_extract_from_custom_task_name(self):
        # when
        result = extract_app_name("alpha.task_name")
        # then
        self.assertEqual(result, "alpha")

    def test_should_return_empty_string_if_no_match_1(self):
        # when
        result = extract_app_name("dummy")
        # then
        self.assertEqual(result, "")

    def test_should_return_empty_string_if_no_match_2(self):
        # when
        result = extract_app_name("tasks.dummy")
        # then
        self.assertEqual(result, "")


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
