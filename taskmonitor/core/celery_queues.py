import itertools
import json

import redis

from django.conf import settings

PRIORITY_SEP = "\x06\x16"
DEFAULT_PRIORITY_STEPS = range(10)


def _redis_client():
    """Fetch the Redis client for the celery broker."""
    return redis.from_url(settings.BROKER_URL)


def _queue_names() -> list:
    """List of all queue names incl. the dedicated queue names for each priority."""
    base_name = getattr(settings, "CELERY_DEFAULT_QUEUE", "celery")
    names = [
        f"{base_name}{PRIORITY_SEP}{priority}" for priority in DEFAULT_PRIORITY_STEPS
    ]
    names = [base_name] + names
    return names


def queue_length() -> list:
    """Length of the celery queue."""
    r = _redis_client()
    return sum(r.llen(queue_name) for queue_name in _queue_names())


def fetch_tasks() -> list:
    """Fetch tasks in queue."""
    r = _redis_client()
    elements_raw = list(
        itertools.chain(*[r.lrange(queue_name, 0, -1) for queue_name in _queue_names()])
    )
    result = [json.loads(obj.decode("utf8")) for obj in elements_raw]
    result.reverse()
    return result


#     {
#         "body": "W1tdLCB7fSwgeyJjYWxsYmFja3MiOiBudWxsLCAiZXJyYmFja3MiOiBudWxsLCAiY2hhaW4iOiBudWxsLCAiY2hvcmQiOiBudWxsfV0=",
#         "content-encoding": "utf-8",
#         "content-type": "application/json",
#         "headers": {
#             "lang": "py",
#             "task": "taskmonitor.tasks.run_housekeeping",
#             "id": "7b2416f0-1ff5-4c77-8403-8aafac05b298",
#             "shadow": None,
#             "eta": None,
#             "expires": None,
#             "group": None,
#             "group_index": None,
#             "retries": 0,
#             "timelimit": [None, None],
#             "root_id": "7b2416f0-1ff5-4c77-8403-8aafac05b298",
#             "parent_id": None,
#             "argsrepr": "()",
#             "kwargsrepr": "{}",
#             "origin": "gen9996@bji74-PC",
#             "ignore_result": False,
#         },
#         "properties": {
#             "correlation_id": "7b2416f0-1ff5-4c77-8403-8aafac05b298",
#             "reply_to": "853ed4b4-2c52-32cd-be57-4086564ac31e",
#             "delivery_mode": 2,
#             "delivery_info": {"exchange": "", "routing_key": "celery"},
#             "priority": 0,
#             "body_encoding": "base64",
#             "delivery_tag": "84f0b41d-c8fc-4dab-88e8-a89afddb1deb",
#         },
#     }
# ]
