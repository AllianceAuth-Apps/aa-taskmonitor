from django.apps import AppConfig


class TaskAnalyticsConfig(AppConfig):
    name = "taskanalytics"
    label = "taskanalytics"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import taskanalytics.signals  # noqa: F401
