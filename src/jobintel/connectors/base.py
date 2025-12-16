"""Base connector interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx
from loguru import logger

from ..utils.http import get_http_client


class BaseConnector(ABC):
    """Base class for job board connectors."""

    def __init__(self, client: Optional[httpx.Client] = None):
        """Initialize connector.

        Args:
            client: Optional HTTP client (creates new if None)
        """
        self.client = client or get_http_client()
        self._own_client = client is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_client:
            self.client.close()

    @abstractmethod
    def fetch_jobs(self, company_identifier: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch jobs for a company.

        Args:
            company_identifier: Company identifier (board token, domain, etc.)
            **kwargs: Additional connector-specific parameters

        Returns:
            List of raw job records

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        pass

    @abstractmethod
    def get_job_url(self, company_identifier: str, job_id: str) -> str:
        """Get public URL for a job posting.

        Args:
            company_identifier: Company identifier
            job_id: Job ID

        Returns:
            Public job URL
        """
        pass

    def log_fetch_result(self, company_identifier: str, job_count: int) -> None:
        """Log fetch result.

        Args:
            company_identifier: Company identifier
            job_count: Number of jobs fetched
        """
        logger.info(
            f"{self.__class__.__name__}: Fetched {job_count} jobs for {company_identifier}"
        )
