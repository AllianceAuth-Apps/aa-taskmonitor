from django.test import TestCase

from taskmonitor.core import celery_queues


class TestCore(TestCase):
    def test_queue_length(self):
        x = celery_queues.queue_length()
        print(x)

    def test_fetch_queue(self):
        x = celery_queues.fetch_tasks()
        print(x)
