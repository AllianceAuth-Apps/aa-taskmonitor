from django.contrib import admin

from .models import TaskLogEntry


@admin.register(TaskLogEntry)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "task_name",
        "priority",
        "state",
        "runtime",
        "app_name",
    )
    ordering = ["-timestamp"]
    list_filter = ("state", "timestamp", "app_name", "task_name")
    search_fields = ("task_name", "app_name", "task_id")
    actions = ["delete_selected_2"]

    def has_add_permission(self, *args, **kwargs) -> bool:
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    @admin.action(description="Delete selected entries (NO CONFIRMATION!")
    def delete_selected_2(self, request, queryset):
        entries_count = queryset.count()
        queryset._raw_delete(queryset.db)
        self.message_user(request, f"Deleted {entries_count} entries.")
