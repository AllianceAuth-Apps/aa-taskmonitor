from collections import defaultdict
from typing import Any, Optional


class TaskRecords:
    """Storing key/value pairs for tasks."""

    def __init__(self) -> None:
        self._data = defaultdict(dict)

    def set(self, task_id: str, key: str, value: Any):
        self._data[str(task_id)][str(key)] = value

    def get(self, task_id: str, key: str) -> Optional[Any]:
        """Returns the value."""
        try:
            return self._data[str(task_id)][str(key)]
        except KeyError:
            return None

    def delete(self, task_id: str, key: str) -> None:
        """Removes the data from the store."""
        try:
            del self._data[str(task_id)][str(key)]
        except KeyError:
            pass

    def fetch(self, task_id: str, key: str) -> Optional[Any]:
        """Fetches the value and removes it from the store."""
        value = self.get(task_id, key)
        self.delete(task_id, key)
        return value
