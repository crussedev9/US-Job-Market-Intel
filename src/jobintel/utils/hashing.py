"""Hashing utilities for stable key generation."""

import hashlib
from typing import Any


def generate_hash(data: str | list[str]) -> str:
    """Generate deterministic SHA256 hash from data.

    Args:
        data: String or list of strings to hash

    Returns:
        Hex digest of hash (64 chars)
    """
    if isinstance(data, list):
        data = "|".join(str(x) for x in data)

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def generate_job_key(source: str, company_name: str, source_job_id: str, title: str) -> str:
    """Generate stable job key for deduplication.

    Format: {source}_{company_hash[:8]}_{job_id_hash[:8]}

    Args:
        source: Data source (greenhouse, lever)
        company_name: Company name
        source_job_id: Original job ID from source
        title: Job title

    Returns:
        Deterministic job key
    """
    company_norm = company_name.lower().strip()
    job_id_norm = str(source_job_id).strip()
    title_norm = title.lower().strip()

    # Hash components for stability
    company_hash = generate_hash(company_norm)[:8]
    job_hash = generate_hash([job_id_norm, title_norm])[:8]

    return f"{source}_{company_hash}_{job_hash}"


def generate_company_id(company_name: str, domain: str | None = None) -> str:
    """Generate stable company ID.

    Args:
        company_name: Company name
        domain: Optional company domain for better uniqueness

    Returns:
        Deterministic company ID (16 char hash)
    """
    if domain:
        key = f"{company_name.lower().strip()}|{domain.lower().strip()}"
    else:
        key = company_name.lower().strip()

    return generate_hash(key)[:16]
