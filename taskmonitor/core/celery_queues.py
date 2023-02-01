"""API for working with celery task queue."""

import concurrent.futures
import datetime as dt
import functools
import itertools
import json
from collections import defaultdict
from typing import List, NamedTuple, Optional

import redis

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from taskmonitor import __title__
from taskmonitor.app_settings import TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT
from taskmonitor.helpers import extract_app_name

PRIORITY_SEP = "\x06\x16"
DEFAULT_PRIORITY_STEPS = range(10)
QUEUED_TASKS_CACHE_KEY = "queued-tasks-cache-key"

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class QueuedTaskShort(NamedTuple):
    """DTO for queued tasks, optimized for size."""

    app_name: str
    id: int
    name: str
    priority: int

    @classmethod
    def from_dict(cls, obj: dict) -> "QueuedTaskShort":
        """Create QueuedTaskShort from raw task dict."""
        if "headers" not in obj:
            raise ValueError("headers missing in obj")
        headers = obj["headers"]
        properties = obj["properties"] if "properties" in obj else {}
        task_name = headers["task"]
        return cls(
            app_name=extract_app_name(task_name),
            id=headers["id"],
            name=task_name,
            priority=properties.get("priority"),
        )


class QueuedTaskCacheEntry(NamedTuple):
    """Wrapper for storing queued tasks in cache with additional data."""

    tasks: List[QueuedTaskShort]
    created_at: dt.datetime


class CacheApi:
    """API for working with the cache for queued tasks."""

    def get(self) -> Optional[QueuedTaskCacheEntry]:
        """Retrieve content of cache or None if cache is expired or invalid."""
        return cache.get(QUEUED_TASKS_CACHE_KEY)

    def set(self, tasks: List[QueuedTaskShort]) -> QueuedTaskCacheEntry:
        """Store given tasks in cache."""
        data = QueuedTaskCacheEntry(tasks=tasks, created_at=timezone.now())
        cache.set(
            QUEUED_TASKS_CACHE_KEY,
            data,
            timeout=TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT,
        )
        return data

    def clear(self):
        """Clear the cache."""
        cache.delete(QUEUED_TASKS_CACHE_KEY)

    def created_at(self) -> Optional[dt.datetime]:
        """Return date when cache was created or None when cache is invalid."""
        data = self.get()
        if data is None:
            return None
        return data.created_at


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def default_queue_name() -> str:
    """Default name of celery queue in AA."""
    return getattr(settings, "CELERY_DEFAULT_QUEUE", "celery")


def _redis_queue_names(queue_name: str = None) -> List[str]:
    """List of all queue names on Redis incl. the dedicated queue names for each priority."""
    if not queue_name:
        queue_name = default_queue_name()
    names = [
        f"{queue_name}{PRIORITY_SEP}{priority}" for priority in DEFAULT_PRIORITY_STEPS
    ]
    names = [queue_name] + names
    return names


def queue_length() -> int:
    """Length of the celery queue."""
    r = _redis_client()
    return sum(r.llen(name) for name in _redis_queue_names())


def fetch_tasks() -> List[QueuedTaskShort]:
    """Fetch tasks from queues
    and return as ordered list with oldest task in first position.
    """
    data = local_cache.get()
    if data is None:
        logger.debug("Cache is stale. Fetching new tasks from queue.")
        tasks = _fetch_task_from_all_queues()
        local_cache.set(tasks)
    else:
        tasks = data.tasks
        logger.debug("Returning tasks from cache.")
    return tasks


def _fetch_task_from_all_queues() -> List[QueuedTaskShort]:
    """Coordinate fetching tasks from all priority queues."""
    _fetch_func = functools.partial(_fetch_tasks_from_redis, _redis_client())
    redis_queue_names = _redis_queue_names()
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(redis_queue_names)
    ) as executor:
        tasks_raw = executor.map(_fetch_func, redis_queue_names)
    return list(itertools.chain(*tasks_raw))


def _fetch_tasks_from_redis(
    r: redis.Redis, redis_queue_name: str
) -> List[QueuedTaskShort]:
    """Fetch tasks from redis."""
    tasks = []
    for obj_encoded in r.lrange(redis_queue_name, 0, -1):
        obj = json.loads(obj_encoded.decode("utf8"))
        try:
            tasks.append(QueuedTaskShort.from_dict(obj))
        except ValueError:
            pass
    return reversed(tasks)


def clear_tasks(queue_name: str = None):
    """Clear tasks from all queues."""
    r = _redis_client()
    for redis_queue_name in _redis_queue_names(queue_name):
        r.delete(redis_queue_name)
    local_cache.clear()


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


local_cache = CacheApi()
