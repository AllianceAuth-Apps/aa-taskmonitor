"""Definition of ListQuerySet."""

from dataclasses import dataclass
from typing import Any

from django.db.models import QuerySet


class QuerySetQueryStub:
    """A stub to implement the query property."""

    def __init__(self) -> None:
        self.select_related = None
        self.order_by = []


@dataclass
class _FilterObj:
    """A filter object."""

    field: str
    lookup: str
    value: str

    def is_matching(self, obj: Any) -> bool:
        """Return True, when obj is matching this filter, else False."""
        obj_value = str(getattr(obj, self.field))
        if self.lookup == "exact":
            return self.value == obj_value

        if self.lookup == "contains":
            return self.value in obj_value

        if self.lookup == "icontains":
            return self.value.lower() in obj_value.lower()

        raise NotImplementedError(f"Unknown lookup: {self.lookup}")

    @classmethod
    def create(cls, key: str, value: Any) -> "_FilterObj":
        """Create new filter from key/value pair."""
        parts = key.split("__")

        if len(parts) == 1:
            field = key
            lookup = "exact"

        elif len(parts) == 2:
            field, lookup = parts

        else:
            raise ValueError(f"Invalid key in filter: {key}")

        return cls(field=field, lookup=lookup, value=str(value))


class ListAsQuerySet(list):
    """Masquerade a list as QuerySet."""

    def __init__(self, *args, model, distinct=False, **kwargs):
        self.model = model
        self.query = QuerySetQueryStub()
        self.distinct_enabled = distinct
        super().__init__(*args, **kwargs)
        self._id_mapper = {str(obj.id): n for n, obj in enumerate(self)}
        self._list_size = len(self)

    def all(self) -> QuerySet:
        """:private:"""
        return self

    def count(self):
        """:private:"""
        return self._list_size

    def _clone(self):
        return self

    def distinct(self):
        """:private:"""
        return ListAsQuerySet(list(set(self)), model=self.model, distinct=True)

    def first(self):
        """:private:"""
        return self[0] if self else None

    def filter(self, *args, **kwargs):
        """:private:"""
        if args:
            raise NotImplementedError(
                f"filter with positional args not supported: {args=} {kwargs=}"
            )

        if not kwargs:
            return self

        filter_objs = [_FilterObj.create(key, value) for key, value in kwargs.items()]

        new_list = [
            obj
            for obj in self
            if all(filter_obj.is_matching(obj) for filter_obj in filter_objs)
        ]

        return ListAsQuerySet(new_list, model=self.model)

    def get(self, *args, **kwargs):
        """:private:"""
        try:
            return self[self._id_mapper[str(kwargs["id"])]]
        except KeyError:
            raise self.model.DoesNotExist from None

    def none(self) -> QuerySet:
        """:private:"""
        return ListAsQuerySet([], model=self.model)

    def order_by(self, *args, **kwargs):
        """:private:"""
        if kwargs:
            raise NotImplementedError("order with kw args not supported.")
        if args:
            for prop in reversed(args):
                if prop[0:1] == "-":
                    reverse = True
                    prop_2 = prop[1:]
                else:
                    reverse = False
                    prop_2 = prop
                # pylint: disable = cell-var-from-loop
                self.sort(key=lambda d: getattr(d, prop_2), reverse=reverse)
        return self

    def values(self, *args):
        """:private:"""
        result = [
            {k: v for k, v in obj.__dict__.items() if not args or k in args}
            for obj in self
        ]
        return result

    def values_list(self, *args, **kwargs):
        """:private:"""
        items = [tuple(obj.values()) for obj in self.values(*args)]
        if kwargs.get("flat"):
            items = [obj[0] for obj in items]
            if self.distinct_enabled:
                return list(dict.fromkeys(items))
            return items
        return items
