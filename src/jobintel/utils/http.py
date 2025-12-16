"""HTTP client utilities with retry logic."""

import time
from typing import Any, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger

from ..config import config


def get_http_client(timeout: int | None = None) -> httpx.Client:
    """Get configured HTTP client.

    Args:
        timeout: Optional timeout override

    Returns:
        Configured httpx Client
    """
    return httpx.Client(
        timeout=timeout or config.http_timeout,
        follow_redirects=True,
        headers={
            "User-Agent": "JobIntel/0.1.0 (US Job Market Research; https://github.com/crussedev9/US-Job-Market-Intel)"
        },
    )


def get_async_http_client(timeout: int | None = None) -> httpx.AsyncClient:
    """Get configured async HTTP client.

    Args:
        timeout: Optional timeout override

    Returns:
        Configured httpx AsyncClient
    """
    return httpx.AsyncClient(
        timeout=timeout or config.http_timeout,
        follow_redirects=True,
        headers={
            "User-Agent": "JobIntel/0.1.0 (US Job Market Research; https://github.com/crussedev9/US-Job-Market-Intel)"
        },
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    reraise=True,
)
def fetch_with_retry(
    url: str,
    client: Optional[httpx.Client] = None,
    method: str = "GET",
    **kwargs: Any,
) -> httpx.Response:
    """Fetch URL with retry logic.

    Args:
        url: URL to fetch
        client: Optional HTTP client (creates new if None)
        method: HTTP method
        **kwargs: Additional arguments for request

    Returns:
        HTTP response

    Raises:
        httpx.HTTPStatusError: On HTTP error after retries
        httpx.TimeoutException: On timeout after retries
    """
    close_client = False
    if client is None:
        client = get_http_client()
        close_client = True

    try:
        logger.debug(f"Fetching {method} {url}")
        response = client.request(method, url, **kwargs)
        response.raise_for_status()

        # Rate limiting
        time.sleep(config.rate_limit_delay)

        return response

    finally:
        if close_client:
            client.close()


def fetch_json(url: str, client: Optional[httpx.Client] = None, **kwargs: Any) -> Any:
    """Fetch URL and parse JSON response.

    Args:
        url: URL to fetch
        client: Optional HTTP client
        **kwargs: Additional arguments for request

    Returns:
        Parsed JSON data

    Raises:
        httpx.HTTPStatusError: On HTTP error
        ValueError: On JSON parse error
    """
    response = fetch_with_retry(url, client=client, **kwargs)
    return response.json()
