import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from taskanalytics.models import TaskLogEntry
from taskanalytics.tasks import run_housekeeping

from .factories import TaskLogEntryFactory

TASKS_PATH = "taskanalytics.tasks"


@patch(TASKS_PATH + ".TASKANALYTICS_LOGS_AGE", 3)
class TestTasks(TestCase):
    def test_should_delete_stale_entries_only(self):
        # given
        stale_entry = TaskLogEntryFactory(
            timestamp=timezone.now() - dt.timedelta(days=3, seconds=1)
        )
        current_entry = TaskLogEntryFactory(timestamp=timezone.now())
        # when
        run_housekeeping()
        # then
        self.assertFalse(TaskLogEntry.objects.filter(pk=stale_entry.pk).exists())
        self.assertTrue(TaskLogEntry.objects.filter(pk=current_entry.pk).exists())
