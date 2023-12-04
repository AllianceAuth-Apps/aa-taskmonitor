"""An Alliance Auth app for monitoring celery tasks."""

# pylint: disable = invalid-name
default_app_config = "taskmonitor.apps.TaskMonitorConfig"

__version__ = "0.21.0a8"
__title__ = "Task Monitor"

# [x] Integrate statistics caching with reports caching updates
# [x] Link directly from statistics to task logs
