"""Role family classification."""

from typing import Optional
import yaml
from pathlib import Path
from loguru import logger

from ..config import config
from ..utils.text import clean_text


# Default role taxonomy
DEFAULT_ROLE_FAMILIES = {
    "Tech/Engineering": [
        "software engineer",
        "engineer",
        "developer",
        "architect",
        "sre",
        "devops",
        "backend",
        "frontend",
        "full stack",
        "infrastructure",
        "security engineer",
        "cloud engineer",
    ],
    "Data/AI": [
        "data scientist",
        "data engineer",
        "data analyst",
        "machine learning",
        "ml engineer",
        "ai engineer",
        "analytics",
        "business intelligence",
        "bi analyst",
    ],
    "Product/Design": [
        "product manager",
        "product owner",
        "designer",
        "ux",
        "ui",
        "product designer",
        "design lead",
        "design manager",
    ],
    "Sales": [
        "sales",
        "account executive",
        "business development",
        "bdr",
        "sdr",
        "sales rep",
        "account manager",
    ],
    "Marketing": [
        "marketing",
        "growth",
        "content",
        "social media",
        "brand",
        "demand generation",
        "digital marketing",
        "marketing manager",
    ],
    "Customer Success": [
        "customer success",
        "customer support",
        "support engineer",
        "solutions engineer",
        "technical account manager",
    ],
    "Finance": [
        "finance",
        "accounting",
        "controller",
        "accountant",
        "financial analyst",
        "fp&a",
    ],
    "HR/Talent": [
        "recruiter",
        "talent",
        "hr",
        "human resources",
        "people ops",
        "people partner",
    ],
    "Operations/Strategy": [
        "operations",
        "strategy",
        "program manager",
        "project manager",
        "business ops",
        "chief of staff",
    ],
    "Legal/Compliance": [
        "legal",
        "counsel",
        "lawyer",
        "compliance",
        "paralegal",
        "attorney",
    ],
}


def load_role_taxonomy(taxonomy_file: Path | None = None) -> dict[str, list[str]]:
    """Load role taxonomy from YAML file.

    Args:
        taxonomy_file: Path to taxonomy YAML file

    Returns:
        Dict mapping role family to keyword list
    """
    if taxonomy_file is None:
        taxonomy_file = config.seeds_dir / "role_taxonomy.yml"

    if not taxonomy_file.exists():
        logger.warning(f"Taxonomy file not found: {taxonomy_file}, using defaults")
        return DEFAULT_ROLE_FAMILIES

    try:
        with open(taxonomy_file, "r", encoding="utf-8") as f:
            taxonomy = yaml.safe_load(f)
            logger.info(f"Loaded role taxonomy from {taxonomy_file}")
            return taxonomy.get("role_families", DEFAULT_ROLE_FAMILIES)
    except Exception as e:
        logger.error(f"Failed to load taxonomy from {taxonomy_file}: {e}")
        return DEFAULT_ROLE_FAMILIES


def classify_role_family(
    title: str,
    description: str | None = None,
    taxonomy: dict[str, list[str]] | None = None,
) -> Optional[str]:
    """Classify job into role family based on title and description.

    Args:
        title: Job title
        description: Job description
        taxonomy: Optional role taxonomy (loads default if None)

    Returns:
        Role family name or None
    """
    if taxonomy is None:
        taxonomy = load_role_taxonomy()

    # Clean and lowercase text
    title_lower = clean_text(title, lowercase=True)
    desc_lower = clean_text(description or "", lowercase=True)

    # Combine title and first 500 chars of description
    combined = f"{title_lower} {desc_lower[:500]}"

    # Score each role family
    scores = {}
    for family, keywords in taxonomy.items():
        score = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Higher weight for title matches
            if keyword_lower in title_lower:
                score += 10
            # Lower weight for description matches
            if keyword_lower in desc_lower:
                score += 1

        if score > 0:
            scores[family] = score

    # Return highest scoring family
    if scores:
        best_family = max(scores, key=scores.get)
        return best_family

    return None


def enrich_role_family(jobs: list, taxonomy: dict[str, list[str]] | None = None) -> list:
    """Enrich job records with role_family classification.

    Args:
        jobs: List of JobRecord objects
        taxonomy: Optional role taxonomy

    Returns:
        Jobs list with role_family populated
    """
    if taxonomy is None:
        taxonomy = load_role_taxonomy()

    logger.info(f"Classifying role families for {len(jobs)} jobs")

    for job in jobs:
        if not job.role_family:  # Only classify if not already set
            job.role_family = classify_role_family(
                job.title,
                job.description,
                taxonomy=taxonomy,
            )

    classified_count = sum(1 for job in jobs if job.role_family)
    logger.info(f"Classified {classified_count}/{len(jobs)} jobs into role families")

    return jobs
