import json
from typing import Optional

from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.utils import html, safestring, timezone
from django.utils.translation import gettext_lazy as _

from app_utils.admin import FieldFilterCountsDb, FieldFilterCountsMemory

from .app_settings import (
    TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT,
    TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT,
)
from .core import celery_queues
from .models import QueuedTask, TaskLog, TaskReport


class QueuedTaskAppsListFilter(FieldFilterCountsMemory):
    """Filter by app name and show name with counts."""

    title = _("app name")
    parameter_name = "app_name"
    field_name = "app_name"


class QueuedTaskTasksListFilter(FieldFilterCountsMemory):
    """Filter by task name and show name with counts."""

    title = _("task name")
    parameter_name = "task_name"
    field_name = "name"


@admin.register(QueuedTask)
class QueuedTaskAdmin(admin.ModelAdmin):
    list_display = (
        "position",
        "id",
        "name",
        "priority",
        "app_name",
    )
    list_display_links = None
    list_filter = (QueuedTaskAppsListFilter, "priority", QueuedTaskTasksListFilter)
    ordering = ["position"]

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        cache_created_at = celery_queues.tasks_cache.created_at() or timezone.now()
        objs_count = celery_queues.queue_length()
        context = {
            "title": "Currently queued tasks",
            "cache_created_at": cache_created_at,
            "task_count": objs_count,
            "cache_timeout": TASKMONITOR_QUEUED_TASKS_CACHE_TIMEOUT,
            "is_below_limit": objs_count < TASKMONITOR_QUEUED_TASKS_ADMIN_LIMIT,
        }
        extra_context.update(context)
        return super().changelist_view(request, extra_context)


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


class TaskLogAppsListFilter(FieldFilterCountsDb):
    """Filter by app name and show name with counts."""

    title = _("app name")
    parameter_name = "app"
    field_name = "app_name"


class TaskLogStatesListFilter(FieldFilterCountsDb):
    """Filter by app name and show name with counts."""

    title = _("state")
    parameter_name = "state"
    field_name = "state"


class TaskLogTasksListFilter(FieldFilterCountsDb):
    """Filter by app name and show name with counts."""

    title = _("task name")
    parameter_name = "task"
    field_name = "task_name"


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("taskmonitor/css/admin.css",)}

    list_display = (
        "_timestamp",
        "task_name",
        "_params",
        "priority",
        "_state",
        "_runtime",
        "_exception",
    )
    list_filter = (
        TaskLogStatesListFilter,
        "timestamp",
        TaskLogAppsListFilter,
        "priority",
        # TaskLogTasksListFilter,
    )
    search_fields = ("task_name", "app_name", "task_id")
    actions = ["delete_selected_2"]
    show_full_result_count = False
    fields = (
        "task_id",
        "task_name",
        "timestamp",
        "_args",
        "_kwargs",
        "_result",
        "retries",
        "priority",
        "state",
        "runtime",
        "app_name",
        "_exception",
        "parent_id",
        "received",
        "started",
        "_traceback",
    )

    def has_add_permission(self, *args, **kwargs) -> bool:
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_readonly_fields(self, request, obj):
        try:
            field = [f for f in obj._meta.fields if f.name == "kwargs"]
            if len(field) > 0:
                field = field[0]
                field.help_text = "some special help text"
        except Exception:
            pass
        return self.readonly_fields

    def _params(self, obj):
        if obj.args and not obj.args:
            return html.format_html("<code>{}</code>", json.dumps(obj.args))
        if not obj.args and obj.kwargs:
            return html.format_html(
                "<code>{}</code>", json.dumps(obj.kwargs, sort_keys=True)
            )
        if obj.args and obj.kwargs:
            return html.format_html(
                "<code>{}<br>{}</code>",
                json.dumps(obj.args),
                json.dumps(obj.kwargs, sort_keys=True),
            )
        return None

    @admin.display(description="Exception")
    def _exception(self, obj) -> str:
        return html.format_html("<code>{}</code>", obj.exception)

    @admin.display(ordering="runtime")
    def _runtime(self, obj) -> Optional[str]:
        return f"{obj.runtime:.1f}" if obj.runtime else None

    @admin.display(ordering="state")
    def _state(self, obj: TaskLog) -> str:
        css_class_map = {
            TaskLog.State.RETRY: "state-retry",
            TaskLog.State.FAILURE: "text-danger",
        }
        css_class = css_class_map.get(obj.state, "")
        return html.format_html(
            '<span class="{}">{}</span>', css_class, obj.get_state_display()
        )

    @admin.display(ordering="timestamp")
    def _timestamp(self, obj: TaskLog) -> str:
        return obj.timestamp_formatted

    @admin.action(description="Delete selected entries (NO CONFIRMATION!")
    def delete_selected_2(self, request, queryset):
        entries_count = queryset.count()
        queryset._raw_delete(queryset.db)
        self.message_user(request, f"Deleted {entries_count} entries.")

    @admin.display(description="Result")
    def _result(self, obj):
        if obj.state == TaskLog.State.SUCCESS:
            return format_html_data(obj.result)
        return "-"

    @admin.display(description="Args")
    def _args(self, obj):
        return format_html_data(obj.args)

    @admin.display(description="Kwargs")
    def _kwargs(self, obj):
        return format_html_data(obj.kwargs)

    @admin.display(description="Traceback")
    def _traceback(self, obj):
        return format_html_lines(obj.traceback)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = get_object_or_404(TaskLog, pk=object_id)
        extra_context["tasklog_text"] = obj.astext()
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


def format_html_lines(text) -> str:
    return safestring.mark_safe(
        "<br>".join(
            [html.format_html("<code>{}</code>", line) for line in text.splitlines()]
        )
    )


def format_html_data(data) -> str:
    return html.format_html(
        "<code>{}</code>", json.dumps(data, sort_keys=True, indent=4)
    )
