# Standard Library Imports
from typing import Callable, Generator, Iterable
from abc import ABC, abstractmethod
from functools import wraps

# Third-Party Imports
from httpx import AsyncClient, HTTPStatusError, Limits, RequestError, Response
from trio import Semaphore, open_nursery, sleep
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Local Imports
from src.core.settings import ClientSettings, default_settings
from src.core.contracts import HTTPResponse, RequestContext
from src.core.agents import get_random_user_agent
from src.core.tools.mongodb import mongo_client


class RateLimitedClient(AsyncClient):
    """Asynchronous HTTP client with built-in rate limiting.

    Extends httpx.AsyncClient to add rate limiting and automatic User-Agent rotation.

    Args:
        settings (ClientSettings): Configuration settings for the client
        **kwargs: Additional arguments passed to AsyncClient
    """

    def __init__(self, settings: ClientSettings = default_settings, **kwargs) -> None:
        """Initialize with rate limiting settings."""
        super().__init__(
            limits=Limits(max_connections=settings.max_connections),
            follow_redirects=settings.follow_redirects,
            timeout=settings.timeout,
            **kwargs,
        )
        self._interval: float = settings.interval

    @wraps(AsyncClient.get)
    async def get(self, url: str, **kwargs) -> Response:
        """Send GET request with rate limiting and random User-Agent.

        Args:
            url: Target URL
            **kwargs: Additional request parameters

        Returns:
            httpx.Response: The HTTP response
        """
        kwargs.setdefault('headers', {})['User-Agent'] = get_random_user_agent()
        await sleep(self._interval)
        return await super().get(url=url, **kwargs)


class RequestStrategy(ABC):
    """Abstract base class for HTTP request strategies."""

    context: RequestContext

    @abstractmethod
    async def fetch(self, context: RequestContext) -> Generator[HTTPResponse, None, None]:
        """Fetch data according to the implemented strategy.

        Args:
            context: Request configuration context

        Yields:
            HTTPResponse objects with parsed data
        """
        pass

    async def _send_requests(self, paths: Iterable[str] = None) -> None:
        """Send batch of requests with rate limiting and concurrency control.

        Args:
            paths: Optional specific paths to request (defaults to context.paths)
        """
        target_paths = paths or self.context.paths
        logger.info(f'Sending {len(target_paths)} requests')

        async with RateLimitedClient(base_url=self.context.base_url) as client:
            async with open_nursery() as nursery:
                semaphore = Semaphore(default_settings.max_concurrent_requests)

                for path in target_paths:
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
        """Process single request with retry logic.

        Args:
            client: Configured HTTP client
            semaphore: Concurrency control
            path: Target path for request
        """
        async with semaphore:
            response = await client.get(path)
            await self._process_response(response)

    async def _process_response(self, response: Response) -> None:
        """Process and store response in MongoDB.

        Args:
            response: HTTP response to process
        """
        logger.info(f'Received {response.status_code} from: {response.url}')

        mongo_client.insert_document(
            document=HTTPResponse(
                status_code=response.status_code,
                content=response.text,
                url=str(response.url),
            ),
            collection=self.context.collection,
        )


class SimpleRequestStrategy(RequestStrategy):
    """Strategy for simple sequential requests."""

    async def fetch(self, context: RequestContext) -> Generator[HTTPResponse, None, None]:
        """Fetch all URLs in context sequentially.

        Args:
            context: Request configuration

        Yields:
            All documents from the MongoDB collection
        """
        self.context = context
        await self._send_requests()
        return mongo_client.get_all_documents(context.collection)


class PaginatedRequestStrategy(RequestStrategy):
    """Strategy for paginated API requests."""

    def __init__(self, number_of_pages: Callable[[str], int] | int) -> None:
        """Initialize with page count configuration.

        Args:
            number_of_pages: Either fixed number or callable that returns page count
        """
        self._number_of_pages = number_of_pages

    async def fetch(self, context: RequestContext) -> Generator[HTTPResponse, None, None]:
        """Fetch all pages for each path in context.

        Args:
            context: Request configuration

        Yields:
            All documents from the MongoDB collection
        """
        self.context = context

        for path in context.paths:
            await self._paginate(path)

        return mongo_client.get_all_documents(context.collection)

    async def _paginate(self, path: str) -> None:
        """Generate and request all pages for a given path.

        Args:
            path: Base path to paginate
        """
        number_of_pages = await self._get_number_of_pages(path)
        paths = [f'{path}?page={page}' for page in range(1, number_of_pages + 1)]
        await self._send_requests(paths)

    async def _get_number_of_pages(self, path: str) -> int:
        """Determine number of pages to request.

        Args:
            path: Path to check

        Returns:
            Number of pages to request
        """
        if callable(self._number_of_pages):
            return await self._number_of_pages(path)
        return self._number_of_pages
