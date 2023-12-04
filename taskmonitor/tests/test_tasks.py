import datetime as dt
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from taskmonitor import tasks
from taskmonitor.models import TaskLog

from .factories import TaskLogFactory

TASKS_PATH = "taskmonitor.tasks"


class TestDeleteStaleTasklogs(TestCase):
    @patch(TASKS_PATH + ".TaskLog", wraps=TaskLog)
    def test_should_delete_stale_entries_only(self, spy_TaskLog):
        # given
        current_dt = timezone.now()
        TaskLogFactory(timestamp=current_dt - dt.timedelta(hours=3, seconds=1))
        TaskLogFactory(timestamp=current_dt - dt.timedelta(hours=3, seconds=1))
        TaskLogFactory(timestamp=current_dt - dt.timedelta(hours=3, seconds=1))
        current_entry = TaskLogFactory(timestamp=current_dt)
        # when
        with patch(TASKS_PATH + ".TASKMONITOR_DELETE_STALE_BATCH_SIZE", 2), patch(
            TASKS_PATH + ".TASKMONITOR_DATA_MAX_AGE", 3
        ):
            tasks.delete_stale_tasklogs()
        # then
        self.assertEqual(TaskLog.objects.count(), 1)
        self.assertTrue(TaskLog.objects.filter(pk=current_entry.pk).exists())
        self.assertEqual(spy_TaskLog.objects.filter.call_count, 2)


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRefreshCachedData(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        TaskLogFactory()
        TaskLogFactory()

    @patch(TASKS_PATH + ".refresh_statistics_cache")
    @patch(TASKS_PATH + ".refresh_single_report_cache")
    def test_should_refresh_cached_data(
        self, mock_refresh_single_report_cache, mock_refresh_statistics_cache
    ):
        # when
        tasks.refresh_cached_data()
        # then
        self.assertEqual(mock_refresh_single_report_cache.apply_async.call_count, 18)
        self.assertTrue(mock_refresh_statistics_cache.apply_async.called)

    @patch(TASKS_PATH + ".cached_reports", spec=True)
    def test_should_refresh_reports_cache(self, mock_cached_report):
        # when
        tasks.refresh_single_report_cache("dummy")
        # then
        self.assertTrue(mock_cached_report.report.return_value.refresh_cache.called)

    @patch(TASKS_PATH + ".TaskStatistic")
    def test_should_refresh_statistics_cache(self, mock_TaskStatistic):
        # when
        tasks.refresh_statistics_cache()
        # then
        self.assertTrue(mock_TaskStatistic.objects.refresh_cache.called)
