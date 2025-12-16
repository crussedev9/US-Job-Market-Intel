"""Automatic discovery of Greenhouse/Lever job boards."""

import re
from datetime import datetime
from typing import Optional
from loguru import logger
import httpx

from ..schema.models import DiscoveredCompany
from ..utils.http import get_http_client
from .greenhouse import GreenhouseConnector
from .lever import LeverConnector


class CompanyDiscovery:
    """Discover Greenhouse and Lever job boards.

    Discovery methods:
    1. URL pattern detection from known careers pages
    2. Web search for company careers pages (requires external search API)
    3. Common subdomain enumeration (careers., jobs., etc.)
    """

    def __init__(self, client: Optional[httpx.Client] = None):
        """Initialize discovery.

        Args:
            client: Optional HTTP client
        """
        self.client = client or get_http_client()
        self._own_client = client is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_client:
            self.client.close()

    def discover_from_url(self, url: str) -> Optional[DiscoveredCompany]:
        """Discover ATS type from a given URL.

        Args:
            url: URL to analyze (careers page, company domain, etc.)

        Returns:
            DiscoveredCompany if detected, None otherwise
        """
        url_lower = url.lower()

        # Check for Greenhouse
        if GreenhouseConnector.is_greenhouse_url(url):
            board_token = GreenhouseConnector.detect_board_token(url)
            if board_token:
                return DiscoveredCompany(
                    company_name=board_token.replace("-", " ").title(),
                    company_domain=None,
                    careers_url=url,
                    ats_type="greenhouse",
                    discovery_method="url_pattern",
                    discovered_at=datetime.now(),
                    confidence=0.95,
                )

        # Check for Lever
        if LeverConnector.is_lever_url(url):
            company = LeverConnector.detect_company_identifier(url)
            if company:
                return DiscoveredCompany(
                    company_name=company.replace("-", " ").title(),
                    company_domain=None,
                    careers_url=url,
                    ats_type="lever",
                    discovery_method="url_pattern",
                    discovered_at=datetime.now(),
                    confidence=0.95,
                )

        return None

    def discover_from_domain(self, domain: str, company_name: str) -> Optional[DiscoveredCompany]:
        """Discover ATS by probing common careers page patterns.

        Args:
            domain: Company domain (e.g., "example.com")
            company_name: Company name for result

        Returns:
            DiscoveredCompany if found, None otherwise
        """
        # Clean domain
        domain = domain.lower().strip()
        if domain.startswith("http"):
            domain = re.sub(r"https?://", "", domain)
        domain = domain.rstrip("/")

        # Common careers page patterns
        patterns = [
            f"https://boards.greenhouse.io/{domain.replace('.', '')}",
            f"https://boards.greenhouse.io/{company_name.lower().replace(' ', '')}",
            f"https://jobs.lever.co/{domain.replace('.', '')}",
            f"https://jobs.lever.co/{company_name.lower().replace(' ', '')}",
            f"https://jobs.lever.co/{company_name.lower().replace(' ', '-')}",
        ]

        # Try each pattern
        for url in patterns:
            try:
                logger.debug(f"Probing {url}")
                response = self.client.get(url, timeout=5)

                if response.status_code == 200:
                    # Detected!
                    discovered = self.discover_from_url(url)
                    if discovered:
                        discovered.company_name = company_name
                        discovered.company_domain = domain
                        discovered.discovery_method = "subdomain_probe"
                        discovered.confidence = 0.85
                        logger.info(f"Discovered {discovered.ats_type} board for {company_name}: {url}")
                        return discovered

            except (httpx.HTTPError, Exception) as e:
                logger.debug(f"Failed to probe {url}: {e}")
                continue

        return None

    def verify_board(self, ats_type: str, identifier: str) -> bool:
        """Verify that a board exists and returns jobs.

        Args:
            ats_type: "greenhouse" or "lever"
            identifier: Board token or company identifier

        Returns:
            True if board is valid and accessible
        """
        try:
            if ats_type == "greenhouse":
                connector = GreenhouseConnector(client=self.client)
                jobs = connector.fetch_jobs(identifier)
                return len(jobs) > 0

            elif ats_type == "lever":
                connector = LeverConnector(client=self.client)
                jobs = connector.fetch_jobs(identifier)
                return len(jobs) > 0

            return False

        except Exception as e:
            logger.debug(f"Board verification failed for {ats_type}/{identifier}: {e}")
            return False

    def discover_batch(
        self, domains: list[tuple[str, str]]
    ) -> list[DiscoveredCompany]:
        """Discover boards for multiple companies.

        Args:
            domains: List of (domain, company_name) tuples

        Returns:
            List of discovered companies
        """
        discovered = []

        for domain, company_name in domains:
            result = self.discover_from_domain(domain, company_name)
            if result:
                discovered.append(result)

        logger.info(f"Discovered {len(discovered)} boards from {len(domains)} companies")
        return discovered
