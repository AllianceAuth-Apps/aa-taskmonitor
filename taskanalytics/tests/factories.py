import datetime as dt
from random import choice, choices, randint

import factory
import factory.fuzzy
from factory.faker import faker

from django.utils import timezone

from taskanalytics.models import TaskLogEntry

# generate fake apps and task names
faker = faker.Faker()
fake_tasks = {}
for app_name in {faker.first_name().lower() for _ in range(10)}:
    fake_tasks[app_name] = [
        app_name + ".tasks." + "_".join(faker.words(3)).lower()
        for _ in range(randint(3, 20))
    ]


class TaskLogEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskLogEntry

    app_name = factory.fuzzy.FuzzyChoice(fake_tasks.keys())
    received = factory.fuzzy.FuzzyDateTime(timezone.now() - dt.timedelta(minutes=5))
    started = factory.LazyAttribute(
        lambda o: factory.fuzzy.FuzzyDateTime(start_dt=o.received).fuzz()
    )
    task_id = factory.Faker("uuid4")
    task_name = factory.LazyAttribute(lambda o: choice(fake_tasks[o.app_name]))

    @factory.lazy_attribute
    def runtime(self):
        return (self.timestamp - self.started).total_seconds()

    @factory.lazy_attribute
    def priority(self):
        return choices(
            population=[1, 2, 3, 4, 5, 6, 7, 8, 9],
            weights=[5, 5, 10, 20, 100, 20, 10, 5, 5],
        )[0]

    @factory.lazy_attribute
    def retries(self):
        return choices(
            population=[0, 1, 2, 3],
            weights=[80, 10, 5, 5],
        )[0]

    @factory.lazy_attribute
    def state(self):
        return choices(
            population=[
                TaskLogEntry.State.SUCCESS,
                TaskLogEntry.State.RETRY,
                TaskLogEntry.State.FAILURE,
            ],
            weights=[80, 15, 5],
        )[0]

    @factory.lazy_attribute
    def exception(self):
        if self.state == TaskLogEntry.State.SUCCESS:
            return None
        return faker.sentence()

    @factory.lazy_attribute
    def traceback(self):
        if self.state == TaskLogEntry.State.SUCCESS:
            return None
        return faker.paragraph()

    @factory.lazy_attribute
    def timestamp(self):
        max_duration = choices(
            population=[0.5, 1, 10, 30, 120],
            weights=[75, 10, 5, 5, 5],
        )[0]
        start_dt = self.started + dt.timedelta(seconds=0.1)
        return factory.fuzzy.FuzzyDateTime(
            start_dt=start_dt,
            end_dt=start_dt + dt.timedelta(seconds=max_duration),
        ).fuzz()
