import datetime as dt
from random import choice, randint

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
        app_name + ".tasks." + "_".join(faker.words(3)) for _ in range(randint(3, 20))
    ]


class TaskLogEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskLogEntry

    app_name = factory.LazyAttribute(lambda o: choice(list(fake_tasks.keys())))
    retries = 0
    received = factory.fuzzy.FuzzyDateTime(timezone.now() - dt.timedelta(minutes=5))
    started = factory.LazyAttribute(
        lambda o: factory.fuzzy.FuzzyDateTime(start_dt=o.received).fuzz()
    )
    state = TaskLogEntry.State.SUCCESS
    task_id = factory.Faker("uuid4")
    task_name = factory.LazyAttribute(lambda o: choice(fake_tasks[o.app_name]))
    timestamp = factory.LazyAttribute(
        lambda o: factory.fuzzy.FuzzyDateTime(
            start_dt=o.started, end_dt=o.started + dt.timedelta(seconds=60)
        ).fuzz()
    )
