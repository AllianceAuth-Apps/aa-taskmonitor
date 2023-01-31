"""API for working with celery task queue."""

import concurrent.futures
import functools
import itertools
import json
from collections import defaultdict

import redis

from django.conf import settings

PRIORITY_SEP = "\x06\x16"
DEFAULT_PRIORITY_STEPS = range(10)


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def default_queue_name() -> str:
    """Default name of celery queue in AA."""
    return getattr(settings, "CELERY_DEFAULT_QUEUE", "celery")


def _redis_queue_names(queue_name: str = None) -> list:
    """List of all queue names on Redis incl. the dedicated queue names for each priority."""
    if not queue_name:
        queue_name = default_queue_name()
    names = [
        f"{queue_name}{PRIORITY_SEP}{priority}" for priority in DEFAULT_PRIORITY_STEPS
    ]
    names = [queue_name] + names
    return names


def queue_length() -> list:
    """Length of the celery queue."""
    r = _redis_client()
    return sum(r.llen(name) for name in _redis_queue_names())


def _fetch_tasks_from_queue(r: redis.Redis, redis_queue_name: str) -> list:
    """Fetch tasks from given queue and return ordered
    with oldest task in first position.
    """
    tasks_raw = reversed(r.lrange(redis_queue_name, 0, -1))
    tasks = [json.loads(obj.decode("utf8")) for obj in tasks_raw]
    del tasks_raw
    return tasks


def fetch_tasks() -> list:
    """Fetch all tasks from queues and return as combined list."""
    _fetch_func = functools.partial(_fetch_tasks_from_queue, _redis_client())
    redis_queue_names = _redis_queue_names()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(redis_queue_names)
    ) as executor:
        tasks_raw = executor.map(_fetch_func, redis_queue_names)
    tasks = list(itertools.chain(*tasks_raw))
    return tasks


def clear_tasks(queue_name: str = None):
    """Clear tasks from all queues."""
    r = _redis_client()
    for redis_queue_name in _redis_queue_names(queue_name):
        r.delete(redis_queue_name)


def add_tasks(queue_name: str, raw_tasks: list):
    """Push fake tasks to task queue."""
    r = _redis_client()
    if not queue_name:
        queue_name = default_queue_name()
    tasks_by_priority = defaultdict(list)
    for task in raw_tasks:
        priority = task["properties"]["priority"]
        tasks_by_priority[priority].append(task)
    for priority, tasks in tasks_by_priority.items():
        raw_tasks_str = [json.dumps(obj) for obj in tasks]
        queue_name_raw = f"{queue_name}{PRIORITY_SEP}{priority}"
        r.lpush(queue_name_raw, *raw_tasks_str)
    del tasks_by_priority
