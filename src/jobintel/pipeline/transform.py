"""Transform stage: normalize raw data to canonical schema."""

from datetime import date, datetime
from typing import Any, Optional
from loguru import logger

from ..schema.models import JobRecord
from ..utils.hashing import generate_job_key, generate_company_id
from ..utils.locations_us import parse_us_location
from ..utils.text import clean_text


def transform_to_canonical(
    raw_jobs: list[dict[str, Any]],
    company_name: str,
    source: str,
    run_date: date,
    strict_us: bool = True,
) -> tuple[list[JobRecord], list[dict[str, Any]]]:
    """Transform raw job records to canonical schema.

    Args:
        raw_jobs: Raw job records from connector
        company_name: Company name
        source: Source type (greenhouse or lever)
        run_date: Run date
        strict_us: If True, reject ambiguous non-US locations

    Returns:
        Tuple of (valid_jobs, rejected_jobs)
    """
    valid_jobs = []
    rejected_jobs = []

    logger.info(f"Transforming {len(raw_jobs)} raw jobs from {source}/{company_name}")

    for raw_job in raw_jobs:
        try:
            if source == "greenhouse":
                job = _transform_greenhouse_job(raw_job, company_name, run_date, strict_us)
            elif source == "lever":
                job = _transform_lever_job(raw_job, company_name, run_date, strict_us)
            else:
                logger.warning(f"Unknown source: {source}")
                continue

            if job:
                valid_jobs.append(job)
            else:
                # Rejected (non-US or missing required fields)
                rejected_jobs.append(
                    {
                        "company_name": company_name,
                        "source": source,
                        "source_job_id": _extract_job_id(raw_job, source),
                        "reason": "Failed US location validation",
                        "raw_location": _extract_location(raw_job, source),
                    }
                )

        except Exception as e:
            logger.error(f"Failed to transform job {raw_job.get('id', 'unknown')}: {e}")
            rejected_jobs.append(
                {
                    "company_name": company_name,
                    "source": source,
                    "source_job_id": _extract_job_id(raw_job, source),
                    "reason": f"Transform error: {str(e)}",
                }
            )

    logger.info(
        f"Transformation complete: {len(valid_jobs)} valid, {len(rejected_jobs)} rejected"
    )
    return valid_jobs, rejected_jobs


def _transform_greenhouse_job(
    raw_job: dict[str, Any],
    company_name: str,
    run_date: date,
    strict_us: bool,
) -> Optional[JobRecord]:
    """Transform Greenhouse job to canonical schema.

    Args:
        raw_job: Raw Greenhouse job record
        company_name: Company name
        run_date: Run date
        strict_us: Strict US filtering

    Returns:
        JobRecord or None if rejected
    """
    # Extract fields
    job_id = str(raw_job["id"])
    title = raw_job.get("title", "")
    content = raw_job.get("content", "") or raw_job.get("description", "")

    # Location (Greenhouse provides location object)
    location_obj = raw_job.get("location", {})
    location_raw = location_obj.get("name", "") if location_obj else ""

    # Parse location
    parsed_loc = parse_us_location(location_raw, strict=strict_us)

    # Enforce US-only
    if not parsed_loc.is_us:
        return None

    # Build canonical record
    company_id = generate_company_id(company_name)
    job_key = generate_job_key("greenhouse", company_name, job_id, title)

    # Extract metadata
    metadata = raw_job.get("metadata", [])
    department = _find_metadata_value(metadata, "department")

    return JobRecord(
        source="greenhouse",
        source_job_id=job_id,
        job_url=raw_job.get("absolute_url", f"https://boards.greenhouse.io/jobs/{job_id}"),
        company_name=company_name,
        company_domain=None,
        company_id=company_id,
        title=title,
        description=clean_text(content),
        department=department,
        employment_type=_find_metadata_value(metadata, "employment_type"),
        seniority=None,
        location_raw=location_raw,
        city=parsed_loc.city,
        state=parsed_loc.state,
        postal_code=parsed_loc.postal_code,
        msa=None,
        is_remote=parsed_loc.is_remote,
        country="US",
        date_posted=_parse_date(raw_job.get("updated_at")),
        date_scraped=datetime.now(),
        role_family=None,
        skills=[],
        industry_tag=None,
        run_date=run_date,
        job_key=job_key,
    )


def _transform_lever_job(
    raw_job: dict[str, Any],
    company_name: str,
    run_date: date,
    strict_us: bool,
) -> Optional[JobRecord]:
    """Transform Lever job to canonical schema.

    Args:
        raw_job: Raw Lever job record
        company_name: Company name
        run_date: Run date
        strict_us: Strict US filtering

    Returns:
        JobRecord or None if rejected
    """
    # Extract fields
    job_id = str(raw_job["id"])
    title = raw_job.get("text", "")
    description = raw_job.get("description", "") or raw_job.get("descriptionPlain", "")

    # Location (Lever provides location string)
    location_raw = raw_job.get("categories", {}).get("location", "") or ""

    # Parse location
    parsed_loc = parse_us_location(location_raw, strict=strict_us)

    # Enforce US-only
    if not parsed_loc.is_us:
        return None

    # Build canonical record
    company_id = generate_company_id(company_name)
    job_key = generate_job_key("lever", company_name, job_id, title)

    categories = raw_job.get("categories", {})

    return JobRecord(
        source="lever",
        source_job_id=job_id,
        job_url=raw_job.get("hostedUrl", f"https://jobs.lever.co/{job_id}"),
        company_name=company_name,
        company_domain=None,
        company_id=company_id,
        title=title,
        description=clean_text(description),
        department=categories.get("department"),
        employment_type=categories.get("commitment"),
        seniority=None,
        location_raw=location_raw,
        city=parsed_loc.city,
        state=parsed_loc.state,
        postal_code=parsed_loc.postal_code,
        msa=None,
        is_remote=parsed_loc.is_remote,
        country="US",
        date_posted=_parse_date(raw_job.get("createdAt")),
        date_scraped=datetime.now(),
        role_family=None,
        skills=[],
        industry_tag=None,
        run_date=run_date,
        job_key=job_key,
    )


def _extract_job_id(raw_job: dict[str, Any], source: str) -> str:
    """Extract job ID from raw record."""
    return str(raw_job.get("id", "unknown"))


def _extract_location(raw_job: dict[str, Any], source: str) -> str:
    """Extract location from raw record."""
    if source == "greenhouse":
        location_obj = raw_job.get("location", {})
        return location_obj.get("name", "") if location_obj else ""
    elif source == "lever":
        return raw_job.get("categories", {}).get("location", "")
    return ""


def _find_metadata_value(metadata: list[dict[str, Any]], key: str) -> Optional[str]:
    """Find value in Greenhouse metadata array.

    Args:
        metadata: Metadata array
        key: Key to find

    Returns:
        Value or None
    """
    for item in metadata:
        if item.get("name") == key:
            return item.get("value")
    return None


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string to date object.

    Args:
        date_str: ISO date string

    Returns:
        date object or None
    """
    if not date_str:
        return None

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.date()
    except (ValueError, AttributeError):
        return None
