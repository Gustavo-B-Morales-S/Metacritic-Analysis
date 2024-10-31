# Native Libraries
from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Generator, Iterable

# Third-Party Libraries
from httpx import AsyncClient, HTTPStatusError, Limits, RequestError, Response
from loguru import logger
from trio import Semaphore, open_nursery, sleep
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Local Modules
from src.core.agents import get_random_user_agent
from src.core.contracts import HTTPResponse, RequestContext
from src.core.settings import ClientSettings, default_settings
from src.core.tools.mongodb import mongo_client


class RateLimitedClient(AsyncClient):
    def __init__(
        self, settings: ClientSettings = default_settings, **kwargs
    ) -> None:
        """Initializes an async HTTP client with rate-limiting and custom settings."""
        super().__init__(
            limits=Limits(max_connections=settings.max_connections),
            follow_redirects=settings.follow_redirects,
            timeout=settings.timeout,
            **kwargs,
        )
        self._interval: float = settings.interval

    @wraps(AsyncClient.get)
    async def get(self, url: str, **kwargs) -> Response:
        """Performs a GET request, applying rate limiting with a user agent header."""
        kwargs.setdefault('headers', {})['User-Agent'] = get_random_user_agent()
        await sleep(self._interval)
        return await super().get(url=url, **kwargs)


class RequestStrategy(ABC):
    """Abstract base class defining a strategy for handling HTTP requests."""
    context: RequestContext

    @abstractmethod
    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        """Fetches data based on the implemented strategy."""
        pass

    async def _send_requests(self, paths: Iterable[str] = None) -> None:
        """Sends asynchronous requests, using a rate-limited client and concurrency."""
        logger.info(f'Sending {len(paths or self.context.paths)} requests.')

        async with RateLimitedClient(base_url=self.context.base_url) as client:
            async with open_nursery() as nursery:
                semaphore: Semaphore = Semaphore(
                    default_settings.max_concurrent_requests
                )

                for path in paths or self.context.paths:
                    nursery.start_soon(
                        self._process_request, client, semaphore, path
                    )

    @retry(
        retry=retry_if_exception_type((HTTPStatusError, RequestError)),
        stop=stop_after_attempt(default_settings.max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _process_request(
        self, client: RateLimitedClient, semaphore: Semaphore, path: str
    ) -> None:
        """Processes an individual request within rate limits and retries on failure."""
        async with semaphore:
            response: Response = await client.get(path)
            await self._process_response(response)

    async def _process_response(self, response: Response) -> None:
        """Processes and stores the HTTP response in MongoDB."""
        logger.info(
            f'Received response {response.status_code} from: {response.url}.'
        )
        mongo_client.insert_document(
            document=HTTPResponse(
                status_code=response.status_code,
                content=response.text,
                url=response.url,
            ),
            collection=self.context.collection,
        )


class SimpleRequestStrategy(RequestStrategy):
    """A simple request strategy that fetches all URLs in the provided context."""

    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        """Executes fetch using the simple request strategy."""
        self.context = context
        await self._send_requests()

        return mongo_client.get_all_documents(context.collection)


class PaginatedRequestStrategy(RequestStrategy):
    """A paginated request strategy that fetches multiple pages of data."""

    def __init__(self, number_of_pages: Callable[[str], int] | int) -> None:
        """Initializes strategy with either a fixed number or a function to get pages."""
        self._number_of_pages = number_of_pages

    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        """Executes fetch with pagination across all paths in the context."""
        self.context = context

        for path in context.paths:
            await self._paginate(path)

        return mongo_client.get_all_documents(context.collection)

    async def _paginate(self, path: str) -> None:
        """Paginates requests over the specified path."""
        number_of_pages: int = await self._get_number_of_pages(path)

        paths: list[str] = [
            f'{path}?page={page}' for page in range(1, number_of_pages + 1)
        ]
        await self._send_requests(paths)

    async def _get_number_of_pages(self, path: str) -> int:
        """Determines the number of pages for a given path, using the specified method."""
        if callable(self._number_of_pages):
            return await self._number_of_pages(path)

        return self._number_of_pages
