def from_task_name(task_name: str) -> str:
    """Return the app name from a typical task name, if possible.
    Otherwise return an empty string.
    """
    parts = task_name.split(".")
    try:
        idx = parts.index("tasks")
    except ValueError:
        if len(parts) == 2:
            return parts[0]
        return ""
    return parts[idx - 1] if idx > 0 else ""
