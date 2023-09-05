import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from taskmonitor.models import TaskLog
from taskmonitor.tasks import delete_stale_tasklogs

from .factories import TaskLogFactory

TASKS_PATH = "taskmonitor.tasks"


class TestTasks(TestCase):
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
            delete_stale_tasklogs()
        # then
        self.assertEqual(TaskLog.objects.count(), 1)
        self.assertTrue(TaskLog.objects.filter(pk=current_entry.pk).exists())
        self.assertEqual(spy_TaskLog.objects.filter.call_count, 2)
