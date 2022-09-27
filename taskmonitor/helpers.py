import itertools


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def extract_app_name(task_name: str) -> str:
    """Extract the app name from a typical task name."""
    parts = task_name.split(".")
    try:
        idx = parts.index("tasks")
    except ValueError:
        if len(parts) == 2:
            return parts[0]
        else:
            return ""
    return parts[idx - 1] if idx > 0 else ""


def next_number(key: str = None) -> int:
    """Generate a sequence of numbers starting at 1.

    Args:
        key: key to generate sequence for.
    """
    if key is None:
        key = "_general"
    try:
        return next_number._counter[key].__next__()
    except AttributeError:
        next_number._counter = dict()
    except KeyError:
        pass
    next_number._counter[key] = itertools.count(start=1)
    return next_number._counter[key].__next__()
