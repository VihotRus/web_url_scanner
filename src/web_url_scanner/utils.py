"""Utils module."""

from urllib.parse import urlparse

from bs4 import BeautifulSoup, SoupStrainer


def get_home_page(url: str):
    parsed = urlparse(url)
    home_page = f"{parsed.scheme}://{parsed.netloc}"
    return home_page


def get_domain(url:str):
    parsed = urlparse(url)
    return parsed.netloc


def get_links(content: str):
    links = []
    for link in BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer('a')):
        try:
            links.append(link['href'])
        except KeyError:
            # ignore if there is no link
            pass
    return links
