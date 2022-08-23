from django.urls import path

from . import views

app_name = "taskanalytics"

urlpatterns = [
    path(
        "admin_taskanalytics_download_csv",
        views.admin_taskanalytics_download_csv,
        name="admin_taskanalytics_download_csv",
    ),
    path(
        "admin_taskanalytics_reports",
        views.admin_taskanalytics_reports,
        name="admin_taskanalytics_reports",
    ),
]
