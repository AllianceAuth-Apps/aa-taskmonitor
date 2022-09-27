import itertools
import json

import redis

from django.conf import settings

PRIORITY_SEP = "\x06\x16"
DEFAULT_PRIORITY_STEPS = range(10)


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def _queue_base_name() -> str:
    return getattr(settings, "CELERY_DEFAULT_QUEUE", "celery")


def _queue_names(base_name: str = None) -> list:
    """List of all queue names incl. the dedicated queue names for each priority."""
    if not base_name:
        base_name = _queue_base_name()
    names = [
        f"{base_name}{PRIORITY_SEP}{priority}" for priority in DEFAULT_PRIORITY_STEPS
    ]
    names = [base_name] + names
    return names


def queue_length() -> list:
    """Length of the celery queue."""
    r = _redis_client()
    return sum(r.llen(queue_name) for queue_name in _queue_names())


def _fetch_tasks_from_queue(redis_client, queue_name: str) -> list:
    tasks_raw = redis_client.lrange(queue_name, 0, -1)
    tasks = [json.loads(obj.decode("utf8")) for obj in tasks_raw]
    return reversed(tasks)


def fetch_tasks() -> list:
    """Fetch tasks in queue."""
    r = _redis_client()
    tasks_raw = [
        _fetch_tasks_from_queue(r, queue_name) for queue_name in _queue_names()
    ]
    return list(itertools.chain(*tasks_raw))
