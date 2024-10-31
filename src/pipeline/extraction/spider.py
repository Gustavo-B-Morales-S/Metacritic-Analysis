# Native Libraries
from typing import Callable, Generator, Literal

# Thirdy-Party Libraries
from selectolax.parser import HTMLParser

# Local Modules
from src.core.contracts import HTTPResponse
from src.core.requester import PaginatedRequestStrategy, RequestStrategy
from src.core.tools.s3 import s3_client
from src.entrypoint import fetch
from src.pipeline.extraction.parsers.games_parser import parse_games_data
from src.pipeline.extraction.parsers.movies_parser import parse_movies_data
from src.pipeline.extraction.parsers.utils import get_html_parser

BASE_URL: str = 'https://www.metacritic.com'

SELECTORS: dict[str, str] = {
    'pages': '.c-navigationPagination_pages',
    'cards': '.c-finderProductCard a',
}

PARSERS: dict[str, Callable] = {
    'game': parse_games_data,
    'movie': parse_movies_data,
}


def extract_paths(section: Literal['game', 'movie', 'tv']) -> list[str]:
    """Extract paths from Metacritic's browse page."""
    url: str = f'{BASE_URL}/browse/{section}/'
    page: HTMLParser = get_html_parser(url=url)

    total_pages: list[str] = page.css_first(SELECTORS['pages']).text().split()
    request_strategy: RequestStrategy = PaginatedRequestStrategy(int(max(total_pages)))

    paths: list[str] = [
        node.attributes['href']
        for response in fetch(
            base_url=url, request_strategy=request_strategy, collection='paths'
        )
        for node in (get_html_parser(response=response).css(SELECTORS['cards']))
    ]

    return paths


def metacritic_spider(section: Literal['movie', 'game']) -> None:
    responses: Generator[HTTPResponse, None, None] = fetch(
        paths=extract_paths(section=section),
        collection='contents',
        base_url=BASE_URL,
    )
    json_like: dict[str, str] = PARSERS[section](responses)

    file_path: str = s3_client.get_file_path(
        layer='raw', file_name=f'metacritic_{section}', file_extension='json'
    )
    s3_client.upload_json(file_path=file_path, json_like=json_like)
