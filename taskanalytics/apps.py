from django.apps import AppConfig

from . import __title__, __version__


class TaskAnalyticsConfig(AppConfig):
    name = "taskanalytics"
    label = "taskanalytics"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = f"{__title__} v{__version__}"

    def ready(self):
        import taskanalytics.signals  # noqa: F401
