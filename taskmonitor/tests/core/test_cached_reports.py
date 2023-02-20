import datetime as dt
from statistics import mean

from pytz import utc

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


class TestQueueLengthOverTime(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_should_create_queue_report(self):
        # given
        start_dt = dt.datetime(2023, 1, 1, 12, 0, tzinfo=utc)
        TaskLogFactory(
            received=start_dt,
            started=start_dt,
            timestamp=start_dt + dt.timedelta(seconds=5),
            current_queue_length=30,
        )
        TaskLogFactory(
            received=start_dt + dt.timedelta(seconds=5),
            started=start_dt + dt.timedelta(seconds=5),
            timestamp=start_dt + dt.timedelta(seconds=10),
            current_queue_length=10,
        )
        start_dt += dt.timedelta(minutes=1)
        TaskLogFactory(
            received=start_dt,
            started=start_dt,
            timestamp=start_dt + dt.timedelta(seconds=5),
            current_queue_length=50,
        )
        TaskLogFactory(
            received=start_dt + dt.timedelta(seconds=5),
            started=start_dt + dt.timedelta(seconds=5),
            timestamp=start_dt + dt.timedelta(seconds=10),
            current_queue_length=30,
        )
        report = cached_reports.QueueLengthOverTime()
        # when
        result = report._calc_data()
        # then
        series = result[0]
        self.assertEqual(series["name"], "length")
        data = series["data"]
        expected = [(1672574400000, 20), (1672574460000, 40)]
        self.assertEqual(data, expected)

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


class TestTruncateMinute(TestCase):
    @staticmethod
    def _to_data(list) -> list:
        return [{"x": obj[0], "y": obj[1]} for obj in list]

    def test_should_calc_mean(self):
        # given
        start_dt = dt.datetime(2023, 1, 1, 12, 0, tzinfo=utc)
        data = self._to_data(
            [
                (start_dt, 1),
                (start_dt, 3),
                (start_dt + dt.timedelta(minutes=2), 3),
                (start_dt + dt.timedelta(minutes=1), 3),
                (start_dt + dt.timedelta(minutes=1), 6),
            ]
        )
        # when
        result = cached_reports._CachedReport._truncate_minute(mean, data)
        # then
        expected = [(1672574400000, 2), (1672574460000, 4), (1672574520000, 3)]
        self.assertListEqual(result, expected)

    def test_should_calc_sum(self):
        # given
        start_dt = dt.datetime(2023, 1, 1, 12, 0, tzinfo=utc)
        data = self._to_data(
            [
                (start_dt, 1),
                (start_dt, 3),
                (start_dt + dt.timedelta(minutes=1), 3),
                (start_dt + dt.timedelta(minutes=1), 6),
                (start_dt + dt.timedelta(minutes=2), 3),
            ]
        )
        # when
        result = cached_reports._CachedReport._truncate_minute(sum, data)
        # then
        expected = [(1672574400000, 4), (1672574460000, 9), (1672574520000, 3)]
        self.assertListEqual(result, expected)
