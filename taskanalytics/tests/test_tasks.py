import datetime as dt
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from taskanalytics.models import TaskLog
from taskanalytics.tasks import delete_stale_tasklogs

from .factories import TaskLogFactory

TASKS_PATH = "taskanalytics.tasks"


@patch(TASKS_PATH + ".TASKANALYTICS_DATA_MAX_AGE", 3)
class TestTasks(TestCase):
    def test_should_delete_stale_entries_only(self):
        # given
        stale_entry = TaskLogFactory(
            timestamp=timezone.now() - dt.timedelta(days=3, seconds=1)
        )
        current_entry = TaskLogFactory(timestamp=timezone.now())
        # when
        delete_stale_tasklogs()
        # then
        self.assertFalse(TaskLog.objects.filter(pk=stale_entry.pk).exists())
        self.assertTrue(TaskLog.objects.filter(pk=current_entry.pk).exists())
