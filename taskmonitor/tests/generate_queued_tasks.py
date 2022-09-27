# flake8: noqa
"""Script for adding lots of tasks to the queue for testing."""

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
from example.tasks import my_task

MAX_ENTRIES = 1_000

print(f"Adding {MAX_ENTRIES:,} tasks to the queue...")
for _ in range(MAX_ENTRIES):
    my_task.delay()
print("DONE!")
