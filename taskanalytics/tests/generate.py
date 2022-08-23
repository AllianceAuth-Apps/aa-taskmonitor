# flake8: noqa
"""Script for creating generated notifications for testing."""

import os
import sys
from pathlib import Path

myauth_dir = Path(__file__).parent.parent.parent.parent / "myauth"
sys.path.insert(0, str(myauth_dir))

import django
from django.apps import apps

# init and setup django project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings.local")
django.setup()

"""MAIN"""
from taskanalytics.models import TaskLogEntry
from taskanalytics.tests.factories import TaskLogEntryFactory

MAX_ENTRIES = 1_000

print(f"Generating {MAX_ENTRIES:,} task log entry...")
objs = TaskLogEntryFactory.build_batch(size=MAX_ENTRIES)
print("Storing...")
TaskLogEntry.objects.bulk_create(objs, batch_size=500, ignore_conflicts=True)
print("DONE!")
