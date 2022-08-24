from app_utils.django import clean_setting

TASKANALYTICS_LOGS_AGE = clean_setting("TASKANALYTICS_LOGS_AGE", 24)
"""Age of logs in hours. Older logs be automatically deleted by house keeping."""

TASKANALYTICS_HOUSEKEEPING_FREQUENCY = clean_setting(
    "TASKANALYTICS_HOUSEKEEPING_FREQUENCY", 60
)
"""Frequency of house keeping runs in minutes."""
