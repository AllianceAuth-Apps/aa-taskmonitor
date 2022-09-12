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
        result = cached_reports._calc_data()
        # then
        oldest = min(log_1.timestamp, log_2.timestamp, log_3.timestamp)
        self.assertEqual(result["oldest_date"], oldest)
        newest = max(log_1.timestamp, log_2.timestamp, log_3.timestamp)
        self.assertEqual(result["youngest_date"], newest)
        self.assertEqual(result["total_runs"], 3)

    def test_should_create_empty_report(self):
        # when
        result = cached_reports._calc_data()
        # then
        self.assertTrue(result)
