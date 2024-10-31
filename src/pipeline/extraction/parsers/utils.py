# Third-Party Libraries
import httpx
from httpx import Response
from selectolax.parser import HTMLParser

# Local Modules
from src.core.agents import get_random_user_agent


headers: dict[str, str] = {'User-Agent': get_random_user_agent()}

def get_html_parser(url: str = None, response: str = None) -> HTMLParser:
    """Fetches HTML content from a given URL or HTTP Response object"""

    if url:
        response: Response = httpx.get(url, headers=headers)
        return HTMLParser(response.content)

    return HTMLParser(response.content)
