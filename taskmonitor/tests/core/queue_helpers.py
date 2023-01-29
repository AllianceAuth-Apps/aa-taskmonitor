import json
from collections import defaultdict

import redis

from django.conf import settings

from taskmonitor.core import celery_queues


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def clear_queue(queue_name: str):
    """Clear the task queue."""
    r = _redis_client()
    for queue_name in celery_queues._queue_names(queue_name):
        r.delete(queue_name)


def push_tasks(queue_name: str, raw_tasks: list):
    """Push tasks to task queue."""
    r = _redis_client()
    tasks_by_priority = defaultdict(list)
    for task in raw_tasks:
        priority = task["properties"]["priority"]
        tasks_by_priority[priority].append(task)
    for priority, tasks in tasks_by_priority.items():
        raw_tasks_str = [json.dumps(obj) for obj in tasks]
        queue_name_raw = f"{queue_name}{celery_queues.PRIORITY_SEP}{priority}"
        r.lpush(queue_name_raw, *raw_tasks_str)
    del tasks_by_priority
