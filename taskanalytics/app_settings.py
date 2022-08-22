from app_utils.django import clean_setting

TASKANALYTICS_LOGS_AGE = clean_setting("TASKANALYTICS_LOGS_AGE", 48)
"""Age of logs in hours. Older logs be automatically deleted by house keeping."""

TASKANALYTICS_HOUSEKEEPING_FREQUENCY = clean_setting(
    "TASKANALYTICS_HOUSEKEEPING_FREQUENCY", 120
)
"""Frequency of house keeping runs in minutes."""
