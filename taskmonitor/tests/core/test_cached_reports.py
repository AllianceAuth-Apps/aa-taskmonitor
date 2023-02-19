from django.core.cache import cache
from django.test import TestCase

from taskmonitor.core import cached_reports
from taskmonitor.models import TaskLog

from ..factories import TaskLogFactory


class TestCachedReports(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_create_reports(self):
        # given
        log_1 = TaskLogFactory(state=TaskLog.State.SUCCESS)
        log_2 = TaskLogFactory(state=TaskLog.State.FAILURE)
        log_3 = TaskLogFactory(state=TaskLog.State.RETRY)
        # when
        result = cached_reports.report_data("basic_information")
        # then
        oldest = min(log_1.timestamp, log_2.timestamp, log_3.timestamp)
        self.assertEqual(result["oldest_date"], oldest)
        newest = max(log_1.timestamp, log_2.timestamp, log_3.timestamp)
        self.assertEqual(result["youngest_date"], newest)
        self.assertEqual(result["total_runs"], 3)

    # def test_should_create_empty_report(self):
    #     # when
    #     result = cached_reports.report_data("basic_information")
    #     # then
    #     self.assertTrue(result)

    def test_should_create_queue_report(self):
        # given
        TaskLogFactory(state=TaskLog.State.SUCCESS)
        TaskLogFactory(state=TaskLog.State.FAILURE)
        TaskLogFactory(state=TaskLog.State.RETRY)
        report = cached_reports.QueueLengthOverTime()
        # when
        report._calc_data()

    def test_should_work_with_null_values(self):
        # given
        TaskLogFactory(state=TaskLog.State.FAILURE)
        log = TaskLogFactory(state=TaskLog.State.SUCCESS, current_queue_length=None)
        self.assertIsNone(log.current_queue_length)
        report = cached_reports.QueueLengthOverTime()
        # when
        report._calc_data()

    def test_should_work_without_data(self):
        # given
        report = cached_reports.QueueLengthOverTime()
        # when
        report._calc_data()
