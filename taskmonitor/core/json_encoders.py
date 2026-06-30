import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class UniversalJSONEncoder(json.JSONEncoder):
    """A JSON encoder that handles custom classes, datetimes, sets, Decimals,
    and falls back to str() for anything else it can't natively encode.
    """

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, (set, frozenset)):
            return list(obj)

        if hasattr(obj, "__dict__") and not callable(obj):
            return obj.__dict__

        if isinstance(obj, Decimal) or isinstance(obj, UUID):
            return str(obj)

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
