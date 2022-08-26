from app_utils.django import clean_setting

TASKANALYTICS_DATA_MAX_AGE = clean_setting("TASKANALYTICS_DATA_MAX_AGE", 24)
"""Max age of logs in hours. Older logs be deleted automatically."""

TASKANALYTICS_HOUSEKEEPING_FREQUENCY = clean_setting(
    "TASKANALYTICS_HOUSEKEEPING_FREQUENCY", 15
)
"""Frequency of house keeping runs in minutes."""

TASKANALYTICS_REPORTS_MAX_AGE = clean_setting("TASKANALYTICS_REPORTS_MAX_AGE", 15)
"""Max age of reports in minutes."""

TASKANALYTICS_REPORTS_MAX_TOP = clean_setting("TASKANALYTICS_REPORTS_MAX_TOP", 20)
"""Max items to show in the top reports. e.g. 10 will shop the top ten items."""
