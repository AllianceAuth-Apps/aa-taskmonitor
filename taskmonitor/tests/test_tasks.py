import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from taskmonitor.models import TaskLog
from taskmonitor.tasks import delete_stale_tasklogs

from .factories import TaskLogFactory

TASKS_PATH = "taskmonitor.tasks"


@patch(TASKS_PATH + ".TASKMONITOR_DATA_MAX_AGE", 3)
class TestTasks(TestCase):
    def test_should_delete_stale_entries_only(self):
        # given
        current_dt = timezone.now()
        stale_entry = TaskLogFactory(
            timestamp=current_dt - dt.timedelta(hours=3, seconds=1)
        )
        current_entry = TaskLogFactory(timestamp=current_dt)
        # when
        with self.assertRaises(Exception):
            delete_stale_tasklogs()
        # then
        self.assertFalse(TaskLog.objects.filter(pk=stale_entry.pk).exists())
        self.assertTrue(TaskLog.objects.filter(pk=current_entry.pk).exists())
