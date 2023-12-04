import datetime as dt
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from taskmonitor import tasks
from taskmonitor.core import cached_reports
from taskmonitor.models import TaskLog, TaskStatistic

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


@patch(TASKS_PATH + ".TaskStatistic", wraps=TaskStatistic)
@patch(TASKS_PATH + ".cached_reports", wraps=cached_reports)
@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestRefreshCachedData(TestCase):
    def test_should_refresh_cached_data(self, mock_cached_reports, mock_TaskStatistic):
        # given
        TaskLogFactory()
        TaskLogFactory()
        # when
        tasks.refresh_cached_data.delay()
        # then
        self.assertEqual(mock_cached_reports.report.call_count, 18)
        self.assertTrue(mock_TaskStatistic.objects.refresh_cache.called)
