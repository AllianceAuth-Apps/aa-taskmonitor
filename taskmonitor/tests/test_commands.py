from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from taskmonitor.core.celery_queues import QueuedTaskShort

from .factories import QueuedTaskRawFactory, TaskLogFactory

MODULE_PATH = "taskmonitor.management.commands"


class TestCommands(TestCase):
    def test_should_inspect_filled_logs(self):
        # given
        TaskLogFactory()
        out = StringIO()
        # when
        call_command("taskmonitorctl", "inspect", "logs", stdout=out)

    def test_should_inspect_empty_logs(self):
        # given
        out = StringIO()
        # when
        call_command("taskmonitorctl", "inspect", "logs", stdout=out)

    def test_should_inspect_empty_queue(self):
        # given
        out = StringIO()
        # when
        with patch(MODULE_PATH + ".taskmonitorctl.celery_queues", spec=True) as m:
            m.queue_length.return_value = 0
            m._fetch_task_from_all_queues.return_value = []
            call_command("taskmonitorctl", "inspect", "queue", stdout=out)

    def test_should_inspect_filled_queue(self):
        # given
        out = StringIO()
        task = QueuedTaskShort.from_dict(QueuedTaskRawFactory())
        # when
        with patch(MODULE_PATH + ".taskmonitorctl.celery_queues", spec=True) as m:
            m.queue_length.return_value = 1
            m._fetch_task_from_all_queues.return_value = [task]
            call_command("taskmonitorctl", "inspect", "queue", stdout=out)

    def test_should_inspect_settings(self):
        # given
        out = StringIO()
        # when
        call_command("taskmonitorctl", "inspect", "settings", stdout=out)

    @patch(MODULE_PATH + ".taskmonitorctl.celery_queues", spec=True)
    def test_should_purge_empty_queue(self, mock_celery_queues):
        # given
        mock_celery_queues.queue_length.return_value = 0
        out = StringIO()
        # when
        with self.assertRaises(SystemExit):
            call_command("taskmonitorctl", "purge", "queue", stdout=out)
        # then
        self.assertFalse(mock_celery_queues.clear_tasks.called)

    @patch(MODULE_PATH + ".taskmonitorctl.celery_queues", spec=True)
    def test_should_purge_filled_queue(self, mock_celery_queues):
        # given
        mock_celery_queues.queue_length.return_value = 1
        out = StringIO()
        # when
        with patch(
            MODULE_PATH + ".taskmonitorctl.Command.user_confirmed", spec=True
        ) as m:
            m.return_value = None
            call_command("taskmonitorctl", "purge", "queue", stdout=out)
        # then
        self.assertTrue(mock_celery_queues.clear_tasks.called)
