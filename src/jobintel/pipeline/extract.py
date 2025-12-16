"""Extraction stage: pull raw job data from sources."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from loguru import logger

from ..config import config
from ..connectors import GreenhouseConnector, LeverConnector
from ..schema.models import CompanySeed


def extract_jobs(
    companies: list[CompanySeed],
    run_date: date,
    max_companies: int | None = None,
) -> dict[str, Any]:
    """Extract jobs from all companies.

    Args:
        companies: List of company seeds
        run_date: Run date for this extraction
        max_companies: Optional limit on number of companies

    Returns:
        Summary dict with extraction stats
    """
    stats = {
        "run_date": run_date.isoformat(),
        "companies_processed": 0,
        "companies_failed": 0,
        "total_jobs": 0,
        "greenhouse_jobs": 0,
        "lever_jobs": 0,
    }

    # Limit companies if specified
    if max_companies:
        companies = companies[:max_companies]

    logger.info(f"Extracting jobs from {len(companies)} companies for {run_date}")

    # Process each company
    for company in companies:
        try:
            jobs = _extract_company_jobs(company, run_date)
            stats["companies_processed"] += 1
            stats["total_jobs"] += len(jobs)

            # Track by source
            if company.ats_type == "greenhouse":
                stats["greenhouse_jobs"] += len(jobs)
            elif company.ats_type == "lever":
                stats["lever_jobs"] += len(jobs)

        except Exception as e:
            logger.error(f"Failed to extract jobs for {company.company_name}: {e}")
            stats["companies_failed"] += 1

    logger.info(
        f"Extraction complete: {stats['total_jobs']} jobs from {stats['companies_processed']} companies"
    )
    return stats


def _extract_company_jobs(company: CompanySeed, run_date: date) -> list[dict[str, Any]]:
    """Extract jobs for a single company.

    Args:
        company: Company seed
        run_date: Run date

    Returns:
        List of raw job records
    """
    # Determine connector
    if company.ats_type == "greenhouse":
        connector = GreenhouseConnector()
        identifier = _extract_identifier_from_url(company.careers_url, "greenhouse")
        jobs = connector.fetch_jobs(identifier)
        source = "greenhouse"

    elif company.ats_type == "lever":
        connector = LeverConnector()
        identifier = _extract_identifier_from_url(company.careers_url, "lever")
        jobs = connector.fetch_jobs(identifier)
        source = "lever"

    else:
        logger.warning(f"Unknown ATS type for {company.company_name}: {company.ats_type}")
        return []

    # Save raw data
    if jobs:
        _save_raw_jobs(company.company_name, source, identifier, jobs, run_date)

    return jobs


def _extract_identifier_from_url(careers_url: str | None, ats_type: str) -> str:
    """Extract board token/company identifier from careers URL.

    Args:
        careers_url: Careers page URL
        ats_type: ATS type (greenhouse or lever)

    Returns:
        Identifier string

    Raises:
        ValueError: If identifier cannot be extracted
    """
    if not careers_url:
        raise ValueError("No careers URL provided")

    if ats_type == "greenhouse":
        from ..connectors.greenhouse import GreenhouseConnector

        identifier = GreenhouseConnector.detect_board_token(careers_url)
        if not identifier:
            raise ValueError(f"Cannot extract Greenhouse board token from {careers_url}")

    elif ats_type == "lever":
        from ..connectors.lever import LeverConnector

        identifier = LeverConnector.detect_company_identifier(careers_url)
        if not identifier:
            raise ValueError(f"Cannot extract Lever company identifier from {careers_url}")

    else:
        raise ValueError(f"Unknown ATS type: {ats_type}")

    return identifier


def _save_raw_jobs(
    company_name: str,
    source: str,
    identifier: str,
    jobs: list[dict[str, Any]],
    run_date: date,
) -> None:
    """Save raw job data to JSON files.

    Args:
        company_name: Company name
        source: Source type (greenhouse or lever)
        identifier: Board token or company identifier
        jobs: Raw job records
        run_date: Run date
    """
    # Create directory structure: data/raw/{run_date}/{source}/{identifier}/
    from ..utils.hashing import generate_company_id

    company_id = generate_company_id(company_name)
    output_dir = config.raw_dir / run_date.isoformat() / source / company_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save jobs to JSON
    output_file = output_dir / "jobs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "company_name": company_name,
                "source": source,
                "identifier": identifier,
                "extracted_at": datetime.now().isoformat(),
                "job_count": len(jobs),
                "jobs": jobs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    logger.debug(f"Saved {len(jobs)} raw jobs to {output_file}")
