"""WEB URL data reader module."""

import asyncio
import logging
from urllib.parse import urljoin

import httpx

from web_url_scanner.entities import WriteBrokenURL, WriteURL
from web_url_scanner.exceptions import URLReaderError
from web_url_scanner.utils import get_domain, get_home_page, get_links

# max depth of URL scanning
MAX_DEPTH = 5

NUM_OF_PARALLEL_TASKS = 20
GET_ITEM_TIMEOUT = 5


class URLScanner:

    """Class responsible for getting URL responses, parse links and write them into write queues."""

    def __init__(
            self,
            write_link_queue: asyncio.Queue[WriteURL],
            write_broken_link_queue: asyncio.Queue[WriteBrokenURL]
    ):
        self._log = logging.getLogger(__name__)
        # user-agent header is needed to prevent blocking on some of the sites
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/133.0.0.0 Safari/537.36",
            "accept": "application/json",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,es-US;q=0.6,es;q=0.5,it-IT;q=0.4,it;q=0.3"
        }
        self._write_link_queue = write_link_queue
        self._write_broken_link_queue = write_broken_link_queue

    async def scan_url(self, url: str):
        """Scan a given URL for other URLS and their depth"""
        visited_urls = set()
        depth = 0
        home_page = get_home_page(url)
        home_domain = get_domain(home_page)
        queue = asyncio.Queue()
        queue.put_nowait((home_page, depth))
        tasks = [
            asyncio.create_task(self._scan_worker(queue, visited_urls, home_page, home_domain))
            for _ in range(NUM_OF_PARALLEL_TASKS)
        ]
        await queue.join()
        for task in tasks:
            task.cancel()

    async def _scan_worker(
            self, queue: asyncio.Queue[tuple[str, int]], visited_urls: set, home_page: str, home_domain: str
    ):
        async with httpx.AsyncClient(http2=True) as client:
            while True:
                url, depth = await queue.get()

                if depth > MAX_DEPTH or url in visited_urls:
                    queue.task_done()
                    continue

                visited_urls.add(url)

                try:
                    response_url, response_content = await self._get_response(client, url)
                    write_url = WriteURL(str(response_url), depth)
                    self._log.info("Received %s", write_url)
                    await self._write_link_queue.put(write_url)
                except URLReaderError:
                    write_url_broken = WriteBrokenURL(url)
                    self._log.warning("Received broken %s", write_url_broken)
                    await self._write_broken_link_queue.put(write_url_broken)
                    queue.task_done()
                    continue

                # add response URL to visited urls as it might be different compared to given url from a queue
                visited_urls.add(str(response_url))
                response_domain = response_url.netloc.decode()
                # verify domain for response URL as we may be redirected to another website
                if not self._verify_domain(home_domain, response_domain):
                    queue.task_done()
                    continue

                links = get_links(response_content)
                for link in links:
                    # join relative links
                    joined_link = urljoin(home_page, link)
                    link_domain = get_domain(joined_link)
                    # don't add links from another domains to a queue
                    if self._verify_domain(home_domain, link_domain):
                        # queue.append((joined_link, depth + 1))
                        await queue.put((joined_link, depth + 1))
                queue.task_done()

    async def _get_response(self, client: httpx.AsyncClient, url: str) -> tuple[httpx.URL, str]:
        """Get the response for the given URL.

        Allow to follow redirects and return redirected URL with response content only if domain is the same.

        Args:
            client (httpx.AsyncClient): opened httpx AsyncClient.
            url (str): The URL to get the response for.

        Returns:
            tuple with URL and response content.
        """
        try:
            response = await client.get(url, headers=self._headers, follow_redirects=True)
        except httpx.RequestError as err:
            self._log.error("Fail to get response for %s: %s", url, err)
            raise URLReaderError(f"Fail to get response for {url}")
        if response.status_code != 200:
            self._log.error(
                "Fail to get response for %s with status code %s",
                url, response.status_code
            )
            raise URLReaderError(f"Response status code is not OK for URL {url}")
        return response.url, response.text

    @staticmethod
    def _verify_domain(home_domain: str, verify_domain: str) -> bool:
        return home_domain == verify_domain
