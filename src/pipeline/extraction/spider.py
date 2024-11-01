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
    '''
    Extracts paths for items in a given section from Metacritic's browse page.

    This function retrieves all available pages in the specified section and
    gathers the URLs of individual item cards, such as games, movies, or TV shows.
    It uses pagination to ensure that paths from multiple pages are collected.

    Args:
        section (Literal['game', 'movie', 'tv']): The category of items to
            extract paths for, such as 'game', 'movie', or 'tv'.

    Returns:
        list[str]: A list of URL paths for each item in the specified section.

    Example:
        To extract game paths from Metacritic's game section:

            game_paths = extract_paths('game')
    '''
    url: str = f'{BASE_URL}/browse/{section}/'
    page: HTMLParser = get_html_parser(url=url)

    total_pages: list[str] = page.css_first(SELECTORS['pages']).text().split()
    request_strategy: RequestStrategy = PaginatedRequestStrategy(int(max(total_pages)))

    paths: list[str] = [
        node.attributes['href']
        for response in fetch(
            base_url=url, request_strategy=request_strategy, collection='paths'
        )
        for node in get_html_parser(response=response).css(SELECTORS['cards'])
    ]

    return paths


def extract_data(section: Literal['movie', 'game'], paths: list[str]) -> None:
    '''
    Collects and stores JSON data from Metacritic for items in the specified section.

    This function fetches the content for each item in the paths list from Metacritic,
    parses the data using the appropriate parser, and then uploads the parsed data
    as a JSON file to an S3 bucket.

    Args:
        section (Literal['movie', 'game']): The category of items to scrape,
            either 'movie' or 'game'.
        paths (list[str]): A list of URL paths to fetch data for within the specified
            section.
    '''
    responses: Generator[HTTPResponse, None, None] = fetch(
        paths=paths,
        collection='contents',
        base_url=BASE_URL,
    )
    json_like: dict[str, str] = PARSERS[section](responses)

    file_path: str = s3_client.get_file_path(
        layer='raw', file_name=f'metacritic_{section}', file_extension='json'
    )
    s3_client.upload_json(file_path=file_path, json_like=json_like)
