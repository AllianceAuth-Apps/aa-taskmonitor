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


def dict_sort_keys(d: dict) -> dict:
    """Return a copy of this dictionary with sorted keys."""
    return dict(sorted(d.items(), key=lambda x: x[0].lower()))


def truncate_args(args: list) -> list:
    """Truncate nested elements and return as new list.

    Dicts will be replaced by `{}`

    Lists, tuple and sets wil be replaced by `[]`
    """
    return [_replace_nested_element(item) for item in args]


def truncate_kwargs(kwargs: dict) -> dict:
    """Truncate nested values and return as new dict.

    Example:
    `{"a": {"aa": 1, ...}, "b": [1, 2, ...]}`-> `{"a": {}, "b": []}`
    """
    return {key: _replace_nested_element(value) for key, value in kwargs.items()}


def _replace_nested_element(value):
    if isinstance(value, dict):
        return dict()
    elif isinstance(value, (list, tuple, set)):
        return list()
    return value


def truncate_result(value):
    """Truncate nested items in results and return as new value."""
    if isinstance(value, dict):
        return truncate_kwargs(value)
    elif isinstance(value, (list, tuple, set)):
        return truncate_args(value)
    return value
