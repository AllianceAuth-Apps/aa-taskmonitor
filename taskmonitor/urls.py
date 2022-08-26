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
]
