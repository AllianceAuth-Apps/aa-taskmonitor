from typing import Optional

from django.contrib import admin
from django.shortcuts import redirect
from django.utils import html

from .models import TaskLog, TaskReport


@admin.register(TaskReport)
class TaskReportAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect("taskmonitor:admin_taskmonitor_reports")


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("taskmonitor/admin.css",)}

    list_display = (
        "timestamp",
        "task_name",
        "priority",
        "_state",
        "_runtime",
        "_exception",
    )
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

    @admin.display(ordering="runtime")
    def _runtime(self, obj) -> Optional[str]:
        return f"{obj.runtime:.1f}" if obj.runtime else None

    @admin.display(ordering="state")
    def _state(self, obj) -> str:
        css_class_map = {
            TaskLog.State.RETRY: "state-retry",
            TaskLog.State.FAILURE: "state-failure",
        }
        css_class = css_class_map.get(obj.state, "")
        return html.format_html(
            '<span class="{}">{}</span>', css_class, obj.get_state_display()
        )

    @admin.display(ordering="exception")
    def _exception(self, obj) -> str:
        return obj.exception
        # if obj.exception:
        #     return html.format_html(
        #         '<span class="truncate" title="{}">{}</span>',
        #         obj.exception,
        #         obj.exception,
        #     )
        # return ""

    @admin.action(description="Delete selected entries (NO CONFIRMATION!")
    def delete_selected_2(self, request, queryset):
        entries_count = queryset.count()
        queryset._raw_delete(queryset.db)
        self.message_user(request, f"Deleted {entries_count} entries.")
