# Native Libraries
from typing import Generator, Iterable, List, Literal

# Thirdy-Party Libraries
from trio import run

# Local Modules
from src.core.contracts import HTTPResponse
from src.core.requester import (
    RequestContext,
    RequestStrategy,
    SimpleRequestStrategy,
)


def fetch(
    base_url: str,
    collection: Literal['paths', 'contents'],
    *,
    paths: Iterable[str] | List[Literal['/']] = ['/'],
    request_strategy: RequestStrategy = SimpleRequestStrategy(),
) -> Generator[HTTPResponse, None, None]:
    '''
    Fetches multiple HTTP responses asynchronously based on the specified
    request strategy.

    This function performs asynchronous HTTP requests to multiple paths
    under the given `base_url` and stores the responses in a specified MongoDB
    collection. It uses the provided request strategy to determine how
    requests are handled.

    Args:
        base_url (str): The base URL for all HTTP requests.
        collection (Literal['paths', 'contents']): The MongoDB collection name
            where responses will be stored. Options include 'paths' and 'contents'.
        paths (Iterable[str] | List[Literal['/']], optional): The endpoint paths
            for requests. Defaults to ['/'] if not specified.
        request_strategy (RequestStrategy, optional): The strategy used for
            managing HTTP requests, e.g., `SimpleRequestStrategy` or
            `PaginatedRequestStrategy`. Defaults to `SimpleRequestStrategy`.

    Returns:
        Generator[HTTPResponse, None, None]: A generator that yields `HTTPResponse`
        objects containing the status, content, and URL of each response.

    '''
    context: RequestContext = RequestContext(
        collection=collection,
        base_url=base_url,
        paths=paths,
    )
    return run(request_strategy.fetch, context)
