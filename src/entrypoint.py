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
    """Fetch multiple HTTP asynchronous requests using a specified request strategy."""
    context: RequestContext = RequestContext(
        collection=collection,
        base_url=base_url,
        paths=paths,
    )
    return run(request_strategy.fetch, context)
