from django.test import TestCase

from taskmonitor.helpers import extract_app_name, truncate_args, truncate_kwargs


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


class TestTruncateArgs(TestCase):
    def test_should_copy_unnested_list(self):
        # when
        result = truncate_args([1, "alpha", 3])
        # then
        self.assertListEqual(result, [1, "alpha", 3])

    def test_should_truncate_nested_list(self):
        # when
        result = truncate_args([1, [1, 2], 3])
        # then
        self.assertListEqual(result, [1, [None], 3])

    def test_should_truncate_nested_dict(self):
        # when
        result = truncate_args([1, {"alpha": 1}, 3])
        # then
        self.assertListEqual(result, [1, {"": None}, 3])

    def test_should_truncate_tuple(self):
        # when
        result = truncate_args([1, (1, 2), 3])
        # then
        self.assertListEqual(result, [1, [None], 3])

    def test_should_truncate_mix(self):
        # when
        result = truncate_args([1, [1, 2], {"alpha": 1}, (1, 2), 3])
        # then
        self.assertListEqual(result, [1, [None], {"": None}, [None], 3])


class TestTruncateKwargs(TestCase):
    def test_should_copy_unnested_dict(self):
        # when
        result = truncate_kwargs({"a": 1, "b": "blue"})
        # then
        self.assertDictEqual(result, {"a": 1, "b": "blue"})

    def test_should_truncate_nested_lists(self):
        # when
        result = truncate_kwargs({"a": [1, 2, 3]})
        # then
        self.assertDictEqual(result, {"a": [None]})

    def test_should_truncate_nested_dict(self):
        # when
        result = truncate_kwargs({"a": {"aa": 1, "ab": 2}})
        # then
        self.assertDictEqual(result, {"a": {"": None}})

    def test_should_truncate_mixed(self):
        # when
        result = truncate_kwargs({"a": 1, "b": {"ba": 1}, "c": [1, 2]})
        # then
        self.assertDictEqual(result, {"a": 1, "b": {"": None}, "c": [None]})
