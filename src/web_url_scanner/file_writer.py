"""File manager module."""

import asyncio
import csv
import os
from pathlib import Path

from web_url_scanner.entities import WriteBrokenURL, WriteURL

FILE_DIR = "data"
WRITE_URL_FILENAME = "URL_TIMESTAMP.csv"
WRITE_BROKEN_URL_FILENAME = "BROKEN_URL_TIMESTAMP.csv"


class FileWriter:
    def __init__(
        self,
        write_link_queue: asyncio.Queue[WriteURL],
        write_broken_link_queue: asyncio.Queue[WriteBrokenURL],
    ):
        self._data_dir = FILE_DIR
        # Ensure data directory exists
        os.makedirs(self._data_dir, exist_ok=True)

        self._write_url_filepath = os.path.join(self._data_dir, WRITE_URL_FILENAME)
        self._write_broken_url_file_path = os.path.join(
            self._data_dir, WRITE_BROKEN_URL_FILENAME
        )
        # create files
        self._create_url_file_with_headers_if_not_exists(self._write_url_filepath)
        self._create_broken_url_file_with_headers_if_not_exists(
            self._write_broken_url_file_path
        )
        # queues
        self._write_link_queue = write_link_queue
        self._write_broken_link_queue = write_broken_link_queue

    def _create_url_file_with_headers_if_not_exists(self, filepath):
        # Create CSV file with a headers if it doesn't exist
        if not os.path.exists(self._write_url_filepath):
            with open(filepath, mode="w", newline="", encoding="utf-8") as _file:
                writer = csv.writer(_file)
                writer.writerow(["URL", "Depth", "Timestamp"])

    def _create_broken_url_file_with_headers_if_not_exists(self, filepath):
        # Create CSV file with a headers if it doesn't exist
        if not os.path.exists(self._write_broken_url_file_path):
            with open(filepath, mode="w", newline="", encoding="utf-8") as _file:
                writer = csv.writer(_file)
                writer.writerow(["URL", "Timestamp"])

    async def write_url_file(self):
        """Reads from the queue and appends (url, timestamp) to the write URL CSV file."""
        while True:
            write_url = await self._write_link_queue.get()
            with open(
                self._write_url_filepath, mode="a", newline="", encoding="utf-8"
            ) as _file:
                writer = csv.writer(_file)
                writer.writerow(
                    [write_url.url, write_url.depth, write_url.read_timestamp]
                )

            self._write_link_queue.task_done()

    async def write_broken_url_file(self):
        """Reads from the queue and appends (url, timestamp) to the broken URL CSV file."""
        while True:
            write_broken_url = await self._write_broken_link_queue.get()
            with open(
                self._write_broken_url_file_path, mode="a", newline="", encoding="utf-8"
            ) as _file:
                writer = csv.writer(_file)
                writer.writerow([write_broken_url.url, write_broken_url.read_timestamp])

            self._write_broken_link_queue.task_done()
