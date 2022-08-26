from typing import Any, Optional

from django.core.cache import cache

from ..app_settings import TASKANALYTICS_DATA_MAX_AGE

CACHE_KEY = "TASKANALYTICS_RECORDS"


class TaskRecords:
    """Storing key/value pairs for tasks."""

    def __init__(self) -> None:
        pass

    def set(self, task_id: str, key: str, value: Any):
        timeout = TASKANALYTICS_DATA_MAX_AGE * 3600
        cache.set(self._build_key(task_id, key), value, timeout=timeout)

    def get(self, task_id: str, key: str) -> Optional[Any]:
        """Returns the value."""
        return cache.get(self._build_key(task_id, key))

    def delete(self, task_id: str, key: str) -> None:
        """Removes the data from the store."""
        cache.delete(self._build_key(task_id, key))

    def fetch(self, task_id: str, key: str) -> Optional[Any]:
        """Fetches the value and removes it from the store."""
        value = self.get(task_id, key)
        self.delete(task_id, key)
        return value

    def _build_key(self, task_id, key: str) -> str:
        return f"{CACHE_KEY}_{task_id}_{key}"
