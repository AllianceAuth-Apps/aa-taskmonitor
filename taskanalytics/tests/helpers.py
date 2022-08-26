from dataclasses import dataclass

from taskanalytics.models import TaskLog


@dataclass
class RequestStub:
    id: str
    retries: int
    parent_id: str = None


@dataclass
class SenderStub:
    name: str
    request: RequestStub
    priority: int

    @classmethod
    def create_from_obj(cls, obj: TaskLog):
        request = RequestStub(
            parent_id=obj.parent_id,
            retries=obj.retries,
            id=str(obj.task_id),
        )
        return cls(name=obj.task_name, request=request, priority=obj.priority)
