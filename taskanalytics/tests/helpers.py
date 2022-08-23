from dataclasses import dataclass

from taskanalytics.models import TaskLog


@dataclass
class RequestStub:
    id: str
    retries: int
    task: str
    parent_id: str = None


@dataclass
class SenderStub:
    request: RequestStub
    priority: int

    @classmethod
    def create_from_obj(cls, obj: TaskLog):
        request = RequestStub(
            parent_id=obj.parent_id,
            retries=obj.retries,
            task=obj.task_name,
            id=str(obj.task_id),
        )
        return cls(request=request, priority=obj.priority)
