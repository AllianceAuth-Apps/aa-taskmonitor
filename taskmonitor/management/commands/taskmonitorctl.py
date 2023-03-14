from collections import Counter
from enum import Enum

import humanize

from django.core.management.base import BaseCommand, CommandError

from taskmonitor import __title__, app_settings
from taskmonitor.core import celery_queues
from taskmonitor.models import TaskLog

CACHE_TIMEOUT_SECONDS = 3600


class Token(str, Enum):
    """Argument token."""

    COMMAND = "command"
    TARGET = "target"


class UserCommand(str, Enum):
    """Command for users."""

    PURGE = "purge"
    INSPECT = "inspect"


class Target(str, Enum):
    """Target of a command."""

    LOGS = "logs"
    QUEUE = "queue"
    SETTINGS = "settings"


class Command(BaseCommand):
    help = f"Command utility for {__title__}."

    def run_from_argv(self, *args, **kwargs) -> None:
        """Workaround to handle exceptions in missing sub commands more gracefully."""
        try:
            super().run_from_argv(*args, **kwargs)
        except CommandError as ex:
            token = __name__.split(".")
            try:
                name = token[-1:].pop()
            except IndexError:
                name = "?"
            print(f"manage.py {name}: {ex}")

    def add_arguments(self, parser) -> None:
        subparsers = parser.add_subparsers(
            dest=Token.COMMAND.value,
            required=True,
            title="commands",
            help="available commands",
        )

        parser_purge = subparsers.add_parser(
            UserCommand.PURGE.value, help="Purge a target"
        )
        parser_purge.add_argument(
            Token.TARGET.value,
            type=str,
            choices=[Target.QUEUE.value],
            help="target to purge",
        )

        parser_inspect = subparsers.add_parser(
            UserCommand.INSPECT.value,
            help="Inspect a target, e.g. show information about it.",
        )
        parser_inspect.add_argument(
            Token.TARGET.value,
            type=str,
            choices=[Target.LOGS.value, Target.QUEUE.value, Target.SETTINGS.value],
            help="target to inspect",
        )
        parser_inspect.add_argument(
            "--force-calc",
            action="store_true",
            help="Fore re-calculation of values and update caches.",
        )

    def user_confirmed(self, question_text):
        user_input = input(f"{question_text} (y/N)?")
        if user_input.lower() != "y":
            self.stdout.write(self.style.WARNING("Aborted by user request."))
            exit(1)

    def purge_queue(self):
        num_entries = celery_queues.queue_length()
        if not num_entries:
            self.stdout.write(self.style.WARNING("Queue is empty. Aborted."))
            exit(1)
        self.user_confirmed(
            f"Are you sure you purge {num_entries:,} tasks from the queue?"
        )
        celery_queues.clear_tasks()
        self.stdout.write(f"Purged {num_entries:,} tasks from queue...")
        self.stdout.write(self.style.SUCCESS("Done."))

    def inspect_logs(self):
        log_count = TaskLog.objects.count()
        try:
            db_table_size = TaskLog.objects.db_table_size()
        except RuntimeError:
            table_size_str = "N/A"
            average_bytes_str = "N/A"
        else:
            table_size_str = humanize.naturalsize(db_table_size)
            average_bytes_str = (
                humanize.naturalsize(db_table_size / log_count) if log_count else "N/A"
            )
        output = {
            "Log count in DB": humanize.intword(log_count),
            "Table size in DB": table_size_str,
            "Average log size in DB": average_bytes_str,
        }
        max_length = max([len(o) for o in output.keys()])
        for label, value in output.items():
            self.stdout.write(f"{label:{max_length + 1}}: {value}")

    def inspect_queue(self):
        num_entries = celery_queues.queue_length()
        self.stdout.write(f"Current queue size: {num_entries:,}")
        self.stdout.write("Summary of queued tasks by app count in descending order:")
        app_in_tasks = (
            task.app_name for task in celery_queues._fetch_task_from_all_queues()
        )
        field_counts = Counter(app_in_tasks)
        field_counts_sorted = dict(
            sorted(field_counts.items(), key=lambda item: item[1], reverse=True)
        )
        max_length = (
            max([len(o) for o in field_counts_sorted.keys()])
            if field_counts_sorted
            else 0
        )
        for app_name, count in field_counts_sorted.items():
            self.stdout.write(f"  {app_name:{max_length}}: {count:,}")

    def inspect_settings(self):
        settings = sorted(
            [o for o in dir(app_settings) if not o.startswith("__") and o == o.upper()]
        )
        max_length = max([len(o) for o in settings])
        for setting_name in settings:
            value = getattr(app_settings, setting_name)
            self.stdout.write(f"{setting_name:{max_length + 1}}: {value}")

    def handle(self, *args, **options):
        command = options[Token.COMMAND.value]
        target = options[Token.TARGET.value]

        if command == UserCommand.PURGE:
            if target == Target.QUEUE:
                self.purge_queue()
            else:
                raise NotImplementedError()

        elif command == UserCommand.INSPECT:
            if target == Target.QUEUE:
                self.inspect_queue()
            elif target == Target.LOGS:
                self.inspect_logs()
            elif target == Target.SETTINGS:
                self.inspect_settings()
            else:
                raise NotImplementedError()

        else:
            raise NotImplementedError()
