"""Lever job board connector."""

from typing import Any, Optional
import httpx
from loguru import logger

from .base import BaseConnector
from ..utils.http import fetch_json


class LeverConnector(BaseConnector):
    """Connector for Lever job boards.

    Lever provides a public API at:
    https://api.lever.co/v0/postings/{company}?mode=json

    No authentication required for public job listings.
    """

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, client: Optional[httpx.Client] = None):
        """Initialize Lever connector.

        Args:
            client: Optional HTTP client
        """
        super().__init__(client)

    def fetch_jobs(self, company: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch jobs from Lever postings API.

        Args:
            company: Lever company identifier (e.g., "netflix")
            **kwargs: Additional parameters

        Returns:
            List of raw job records

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        # Build URL
        url = f"{self.BASE_URL}/{company}"

        # Parameters
        params = {"mode": "json"}
        params.update(kwargs)

        try:
            jobs = fetch_json(url, client=self.client, params=params)

            # Response is directly an array
            if not isinstance(jobs, list):
                logger.warning(f"Unexpected Lever response format for {company}")
                return []

            self.log_fetch_result(company, len(jobs))
            return jobs

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Lever company not found: {company}")
                return []
            raise

    def get_job_url(self, company: str, job_id: str) -> str:
        """Get public URL for Lever job posting.

        Args:
            company: Lever company identifier
            job_id: Job ID (posting ID)

        Returns:
            Public job URL
        """
        return f"https://jobs.lever.co/{company}/{job_id}"

    @staticmethod
    def detect_company_identifier(careers_url: str) -> Optional[str]:
        """Detect Lever company identifier from careers URL.

        Args:
            careers_url: Careers page URL

        Returns:
            Company identifier or None
        """
        import re

        # Pattern: https://jobs.lever.co/{company}
        pattern = r"jobs\.lever\.co/([a-zA-Z0-9_-]+)"
        match = re.search(pattern, careers_url)

        return match.group(1) if match else None

    @staticmethod
    def is_lever_url(url: str) -> bool:
        """Check if URL is a Lever careers page.

        Args:
            url: URL to check

        Returns:
            True if Lever URL
        """
        return "jobs.lever.co" in url.lower() or "lever.co" in url.lower()
