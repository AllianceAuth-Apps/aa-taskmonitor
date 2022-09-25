from django.test import TestCase

from taskmonitor.core import celery_queues


class TestCore(TestCase):
    def test_dummy(self):
        x = celery_queues.fetch_celery_queue_length()
        print(x)
