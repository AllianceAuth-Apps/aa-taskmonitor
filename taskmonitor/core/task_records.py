"""A global key/value store for task related data.

The django cache is used as data storage to enable persistence and thread safety.
"""

from typing import Any, Optional

from django.core.cache import cache

from ..app_settings import TASKMONITOR_DATA_MAX_AGE

CACHE_KEY = "TASKMONITOR_RECORDS"


def set(task_id: str, key: str, value: Any):
    """Set a key/value for a task."""
    timeout = TASKMONITOR_DATA_MAX_AGE * 3600
    cache.set(_build_key(task_id, key), value, timeout=timeout)


def get(task_id: str, key: str) -> Optional[Any]:
    """Returns the value for a task and key."""
    return cache.get(_build_key(task_id, key))


def delete(task_id: str, key: str) -> None:
    """Remove a key for a task."""
    cache.delete(_build_key(task_id, key))


def fetch(task_id: str, key: str) -> Optional[Any]:
    """Fetch the value and removes it's key for task."""
    value = get(task_id, key)
    delete(task_id, key)
    return value


def _build_key(task_id, key: str) -> str:
    return f"{CACHE_KEY}_{task_id}_{key}"
