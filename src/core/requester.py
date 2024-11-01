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
    '''
    An asynchronous HTTP client with rate limiting, designed for controlled requests.

    Args:
        settings (ClientSettings): Settings for configuring the client instance.
        kwargs: Additional arguments to customize the AsyncClient.

    Attributes:
        _interval (float): The time interval to wait between requests for rate limiting.
    '''

    def __init__(
        self, settings: ClientSettings = default_settings, **kwargs
    ) -> None:
        '''
        Initializes an async HTTP client with rate limiting and custom settings.

        Args:
            settings (ClientSettings): Client configuration settings, including
                rate limiting parameters.
            kwargs: Additional parameters for the HTTP client.
        '''
        super().__init__(
            limits=Limits(max_connections=settings.max_connections),
            follow_redirects=settings.follow_redirects,
            timeout=settings.timeout,
            **kwargs,
        )
        self._interval: float = settings.interval

    @wraps(AsyncClient.get)
    async def get(self, url: str, **kwargs) -> Response:
        '''
        Performs a GET request, applying rate limiting and setting a user agent.

        Args:
            url (str): The URL to send the GET request to.
            kwargs: Optional additional arguments for the GET request.

        Returns:
            Response: The HTTP response object.
        '''
        kwargs.setdefault('headers', {})['User-Agent'] = get_random_user_agent()
        await sleep(self._interval)
        return await super().get(url=url, **kwargs)


class RequestStrategy(ABC):
    '''
    Abstract base class defining a strategy for handling HTTP requests.

    Attributes:
        context (RequestContext): The request context containing base URL and path details.
    '''

    context: RequestContext

    @abstractmethod
    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        '''
        Fetches data based on the implemented strategy.

        Args:
            context (RequestContext): The context with the necessary data for requests.

        Yields:
            HTTPResponse: Parsed HTTP response data.
        '''
        pass

    async def _send_requests(self, paths: Iterable[str] = None) -> None:
        '''
        Sends asynchronous requests, managed with rate limiting and concurrency.

        Args:
            paths (Iterable[str], optional): Specific paths for the requests. Defaults
                to None, in which case it uses context paths.
        '''
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
        '''
        Processes a single HTTP request within rate limits, with retries on failure.

        Args:
            client (RateLimitedClient): The rate-limited client for making requests.
            semaphore (Semaphore): Concurrency control semaphore.
            path (str): The specific request path.
        '''
        async with semaphore:
            response: Response = await client.get(path)
            await self._process_response(response)

    async def _process_response(self, response: Response) -> None:
        '''
        Processes and stores the HTTP response in a MongoDB collection.

        Args:
            response (Response): The HTTP response to process and store.
        '''
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
    '''
    A simple request strategy that fetches all URLs defined in the provided context.
    '''

    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        '''
        Executes fetch using the simple request strategy.

        Args:
            context (RequestContext): The context with URLs and settings for requests.

        Yields:
            HTTPResponse: Parsed HTTP response data.
        '''
        self.context = context
        await self._send_requests()

        return mongo_client.get_all_documents(context.collection)


class PaginatedRequestStrategy(RequestStrategy):
    '''
    A paginated request strategy that fetches multiple pages of data from specified paths.

    Args:
        number_of_pages (Callable[[str], int] | int): The number of pages to request,
            or a function to determine page count dynamically.
    '''

    def __init__(self, number_of_pages: Callable[[str], int] | int) -> None:
        '''
        Initializes the strategy with a fixed or dynamically calculated number of pages.

        Args:
            number_of_pages (Callable[[str], int] | int): Number of pages to request
                per path, or a function to calculate this value.
        '''
        self._number_of_pages = number_of_pages

    async def fetch(
        self, context: RequestContext
    ) -> Generator[HTTPResponse, None, None]:
        '''
        Executes fetch with pagination over all paths in the request context.

        Args:
            context (RequestContext): The request context with base URL and paths.

        Yields:
            HTTPResponse: Parsed HTTP response data.
        '''
        self.context = context

        for path in context.paths:
            await self._paginate(path)

        return mongo_client.get_all_documents(context.collection)

    async def _paginate(self, path: str) -> None:
        '''
        Paginates requests over the specified path by generating URLs for each page.

        Args:
            path (str): The base path for paginated requests.
        '''
        number_of_pages: int = await self._get_number_of_pages(path)

        paths: list[str] = [
            f'{path}?page={page}' for page in range(1, number_of_pages + 1)
        ]
        await self._send_requests(paths)

    async def _get_number_of_pages(self, path: str) -> int:
        '''
        Determines the number of pages to request for a specific path.

        Args:
            path (str): The path to determine pagination for.

        Returns:
            int: The number of pages to request.
        '''
        if callable(self._number_of_pages):
            return await self._number_of_pages(path)

        return self._number_of_pages
