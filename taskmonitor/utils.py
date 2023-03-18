from typing import Callable

from django.core.cache import cache


def cached_queryset(queryset_func: Callable, key, timeout):
    return cache.get_or_set(key, queryset_func, timeout)
