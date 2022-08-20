from django.contrib import admin

from .models import TaskLog


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "task_name", "state", "runtime", "app_name")
    ordering = ["-timestamp"]
    list_filter = ("state", "timestamp", "app_name", "task_name")
    search_fields = ("task_name", "app_name", "task_id")

    def has_add_permission(self, *args, **kwargs) -> bool:
        return False

    def has_change_permission(self, *args, **kwargs):
        return False
