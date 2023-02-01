from django.urls import path

from . import views

app_name = "taskmonitor"

urlpatterns = [
    path(
        "admin_taskmonitor_download_csv",
        views.admin_taskmonitor_download_csv,
        name="admin_taskmonitor_download_csv",
    ),
    path(
        "admin_taskmonitor_reports",
        views.admin_taskmonitor_reports,
        name="admin_taskmonitor_reports",
    ),
    path(
        "admin_taskmonitor_reports_clear_cache",
        views.admin_taskmonitor_reports_clear_cache,
        name="admin_taskmonitor_reports_clear_cache",
    ),
    path(
        "admin_taskmonitor_reports_recalculation",
        views.admin_taskmonitor_reports_recalculation,
        name="admin_taskmonitor_reports_recalculation",
    ),
    path(
        "admin_taskmonitor_report_data/<str:report_name>",
        views.admin_taskmonitor_report_data,
        name="admin_taskmonitor_report_data",
    ),
    path(
        "admin_queued_task_purge",
        views.admin_queued_task_purge,
        name="admin_queued_task_purge",
    ),
    path(
        "admin_queued_task_clear_cache",
        views.admin_queued_task_clear_cache,
        name="admin_queued_task_clear_cache",
    ),
]
