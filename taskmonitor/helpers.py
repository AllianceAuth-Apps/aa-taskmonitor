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


def truncate_args(args: list) -> list:
    """Truncate nested elements and return as new list.

    Dicts will be replaced by `{"": None}`

    Lists, tuple and sets wil be replaced by `[None]`
    """
    args_new = []
    for item in args:
        if isinstance(item, dict):
            args_new.append({"": None})
        elif isinstance(item, (list, tuple, set)):
            args_new.append([None])
        else:
            args_new.append(item)
    return args_new


def truncate_kwargs(kwargs: dict) -> dict:
    """Truncate nested elements and return as new dict.

    Will keep first and second dict nesting in tact and truncate 3rd nesting.

    Example:
    `{"a": {"aa": {"aaa": 1}}}`-> `{"a": {"aa": {"": None}}}`
    """
    kwargs_new = {}
    for key, value in kwargs.items():
        if isinstance(value, dict):
            value_new = {}
            for k, v in value.items():
                if isinstance(v, dict):
                    v_new = {"": None}
                elif isinstance(v, (list, tuple, set)):
                    v_new = [None]
                else:
                    v_new = v
                value_new[k] = v_new
        elif isinstance(value, (list, tuple, set)):
            value_new = truncate_args(value)
        else:
            value_new = value
        kwargs_new[key] = value_new
    return kwargs_new
