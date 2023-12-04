"""An Alliance Auth app for monitoring celery tasks."""

# pylint: disable = invalid-name
default_app_config = "taskmonitor.apps.TaskMonitorConfig"

__version__ = "0.21.0a6"
__title__ = "Task Monitor"

# [ ] Integrate statistics caching with reports caching updates
# [ ] Link directly from statistics to task logs
