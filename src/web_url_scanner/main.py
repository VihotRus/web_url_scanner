"""Main module."""

import asyncio

from web_url_scanner.file_writer import FileWriter
from web_url_scanner.url_scanner import URLScanner

NUM_OF_WORKERS = 5
GET_ITEM_TIMEOUT = 5
INPUT_FILE = "input.txt"


async def worker(url_queue: asyncio.Queue[str], url_scanner: URLScanner):
    while url_queue:
        try:
            url = await asyncio.wait_for(url_queue.get(), timeout=GET_ITEM_TIMEOUT)
        except asyncio.TimeoutError:
            continue

        await url_scanner.scan_url(url)
        url_queue.task_done()


async def main():
    url_queue = asyncio.Queue()
    write_link_queue = asyncio.Queue()
    write_broken_link_queue = asyncio.Queue()
    with open(INPUT_FILE, "r", encoding="utf-8") as input_file:
        urls = input_file.readlines()
        for url in urls:
            url_queue.put_nowait(url)
    url_scanner = URLScanner(
        write_link_queue=write_link_queue,
        write_broken_link_queue=write_broken_link_queue,
    )
    file_writer = FileWriter(
        write_link_queue=write_link_queue,
        write_broken_link_queue=write_broken_link_queue,
    )

    scanner_tasks = [
        asyncio.create_task(worker(url_queue, url_scanner))
        for i in range(NUM_OF_WORKERS)
    ]
    file_writer_tasks = [
        asyncio.create_task(file_writer.write_url_file()),
        asyncio.create_task(file_writer.write_broken_url_file()),
    ]

    await asyncio.gather(
        url_queue.join(), write_link_queue.join(), write_broken_link_queue.join()
    )

    for task in scanner_tasks:
        task.cancel()

    for task in file_writer_tasks:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
