import itertools
import json

import redis

from django.conf import settings

PRIORITY_SEP = "\x06\x16"
DEFAULT_PRIORITY_STEPS = range(10)


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def _queue_names() -> list:
    """List of all queue names incl. the dedicated queue names for each priority."""
    base_name = getattr(settings, "CELERY_DEFAULT_QUEUE", "celery")
    names = [
        f"{base_name}{PRIORITY_SEP}{priority}" for priority in DEFAULT_PRIORITY_STEPS
    ]
    names = [base_name] + names
    return names


def queue_length() -> list:
    """Length of the celery queue."""
    r = _redis_client()
    return sum(r.llen(queue_name) for queue_name in _queue_names())


def fetch_tasks() -> list:
    """Fetch tasks in queue."""
    r = _redis_client()
    elements_raw = list(
        itertools.chain(
            *[reversed(r.lrange(queue_name, 0, -1)) for queue_name in _queue_names()]
        )
    )
    return [json.loads(obj.decode("utf8")) for obj in elements_raw]
