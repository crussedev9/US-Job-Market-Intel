"""Greenhouse job board connector."""

from typing import Any, Optional
import httpx
from loguru import logger

from .base import BaseConnector
from ..utils.http import fetch_json


class GreenhouseConnector(BaseConnector):
    """Connector for Greenhouse job boards.

    Greenhouse provides a public API at:
    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs

    No authentication required for public job listings.
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, client: Optional[httpx.Client] = None):
        """Initialize Greenhouse connector.

        Args:
            client: Optional HTTP client
        """
        super().__init__(client)

    def fetch_jobs(self, board_token: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch jobs from Greenhouse board.

        Args:
            board_token: Greenhouse board token (e.g., "openai")
            **kwargs: Additional parameters (content=true for full descriptions)

        Returns:
            List of raw job records

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # Build URL
        url = f"{self.BASE_URL}/{board_token}/jobs"

        # Add content parameter for full job descriptions
        params = {"content": "true"}
        params.update(kwargs)

        try:
            data = fetch_json(url, client=self.client, params=params)

            # Extract jobs array
            jobs = data.get("jobs", []) if isinstance(data, dict) else []

            self.log_fetch_result(board_token, len(jobs))
            return jobs

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Greenhouse board not found: {board_token}")
                return []
            raise

    def fetch_job_detail(self, board_token: str, job_id: str) -> Optional[dict[str, Any]]:
        """Fetch detailed job information.

        Args:
            board_token: Greenhouse board token
            job_id: Job ID

        Returns:
            Job detail dict or None if not found
        """
        url = f"{self.BASE_URL}/{board_token}/jobs/{job_id}"

        try:
            return fetch_json(url, client=self.client)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Greenhouse job not found: {board_token}/{job_id}")
                return None
            raise

    def get_job_url(self, board_token: str, job_id: str) -> str:
        """Get public URL for Greenhouse job posting.

        Args:
            board_token: Greenhouse board token
            job_id: Job ID

        Returns:
            Public job URL
        """
        return f"https://boards.greenhouse.io/{board_token}/jobs/{job_id}"

    @staticmethod
    def detect_board_token(careers_url: str) -> Optional[str]:
        """Detect Greenhouse board token from careers URL.

        Args:
            careers_url: Careers page URL

        Returns:
            Board token or None
        """
        import re

        # Pattern: https://boards.greenhouse.io/{board_token}
        pattern = r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)"
        match = re.search(pattern, careers_url)

        return match.group(1) if match else None

    @staticmethod
    def is_greenhouse_url(url: str) -> bool:
        """Check if URL is a Greenhouse careers page.

        Args:
            url: URL to check

        Returns:
            True if Greenhouse URL
        """
        return "boards.greenhouse.io" in url.lower()
