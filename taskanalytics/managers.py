import csv
import zipfile
from pathlib import Path

from django.db import models
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from app_utils.logging import LoggerAddTag

from . import __title__

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def file_to_zip(source_file: Path, destination: Path) -> Path:
    """Create a zip archive from a file."""
    destination.mkdir(parents=True, exist_ok=True)
    zip_file = (destination / source_file.name).with_suffix(".zip")
    with zipfile.ZipFile(
        file=zip_file, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as my_zip:
        my_zip.write(filename=source_file, arcname=source_file.name)
    logger.info("Created export file: %s", zip_file)
    return zip_file


class TaskLogManager(models.Manager):
    def export_to_csv(self, destination: str) -> Path:
        logger.info("Exporting CSV file with %s objects", f"{self.count():,}")
        destination = Path(destination)
        csv_file = self.write_to_file(destination)
        return file_to_zip(csv_file, destination)

    def write_to_file(self, destination: Path) -> Path:
        """Write export data to CSV file.

        Returns full path to CSV file.
        """
        dt_string = timezone.now().strftime("%Y%m%d%H%M%S")
        output_file = destination / f"taskanalytics_{dt_string}.csv"
        with output_file.open("w", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=["task_id", "task_name", "state", "timestamp"]
            )
            writer.writeheader()
            chunk_size = 1000
            for obj in self.iterator(chunk_size=chunk_size):
                row = {
                    "task_id": obj.task_id,
                    "task_name": obj.task_name,
                    "state": obj.state,
                    "timestamp": obj.timestamp.isoformat(),
                }
                writer.writerow(row)
        return output_file
