from django.test import TestCase

from taskmonitor.core.list_queryset import ListAsQuerySet
from taskmonitor.models import QueuedTask
from taskmonitor.tests.factories import QueuedTaskFactory


class TestListAsQuerySet(TestCase):
    def test_all(self):
        # given
        data = [
            QueuedTaskFactory.build(),
            QueuedTaskFactory.build(),
            QueuedTaskFactory.build(),
        ]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.all()
        # then
        self.assertEqual(result, data)

    def test_count(self):
        # given
        data = [QueuedTaskFactory.build(), QueuedTaskFactory.build()]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when/then
        self.assertEqual(qs.count(), 2)

    def test_filter_no_params(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="one")
        t2 = QueuedTaskFactory.build(app_name="alpha", name="two")
        t3 = QueuedTaskFactory.build(app_name="alpha", name="three")
        data = [t1, t2, t3]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.filter()
        self.assertEqual(result, data)

    def test_filter_single_kwargs(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="one")
        t2 = QueuedTaskFactory.build(app_name="alpha", name="two")
        t3 = QueuedTaskFactory.build(app_name="alpha", name="three")
        data = [t1, t2, t3]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.filter(name="two")
        self.assertEqual(result, [t2])

    def test_filter_multiple_kwargs(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="1", priority=2)
        t2 = QueuedTaskFactory.build(app_name="alpha", name="2", priority=3)
        t3 = QueuedTaskFactory.build(app_name="alpha", name="3", priority=3)
        data = [t1, t2, t3]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.filter(app_name="alpha", priority=3)
        self.assertEqual(result, [t2, t3])

    def test_filter_kwargs_with_contains(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="joe_1")
        t2 = QueuedTaskFactory.build(app_name="alpha", name="joe_2")
        t3 = QueuedTaskFactory.build(app_name="alpha", name="Joe")
        data = [t1, t2, t3]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.filter(name__contains="joe")
        self.assertEqual(result, [t1, t2])

    def test_filter_kwargs_with_icontains(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="joe_1")
        t2 = QueuedTaskFactory.build(app_name="alpha", name="Joe_2")
        t3 = QueuedTaskFactory.build(app_name="alpha", name="bob")
        data = [t1, t2, t3]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when
        result = qs.filter(name__icontains="joe")
        self.assertEqual(result, [t1, t2])

    def test_should_raise_error_when_lookup_is_unknown(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="joe_1")
        data = [t1]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when/then
        with self.assertRaises(NotImplementedError):
            qs.filter(name__unknown="joe")

    def test_should_raise_error_when_filter_is_invalid(self):
        # given
        t1 = QueuedTaskFactory.build(app_name="alpha", name="joe_1")
        data = [t1]
        qs = ListAsQuerySet(data, model=QueuedTask)
        # when/then
        with self.assertRaises(ValueError):
            qs.filter(name__exact__illegal="joe")
