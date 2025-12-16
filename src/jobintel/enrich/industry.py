"""Industry tagging based on company and job attributes."""

from typing import Optional
import yaml
from pathlib import Path
from loguru import logger

from ..config import config
from ..utils.text import clean_text


# Default industry mapping rules
DEFAULT_INDUSTRY_MAPPING = {
    "Technology": [
        "software",
        "saas",
        "cloud",
        "ai",
        "machine learning",
        "data",
        "tech",
        "platform",
        "api",
    ],
    "Financial Services": [
        "fintech",
        "banking",
        "finance",
        "investment",
        "trading",
        "payments",
        "credit",
    ],
    "Healthcare": [
        "health",
        "medical",
        "healthcare",
        "biotech",
        "pharma",
        "clinical",
        "patient",
    ],
    "E-commerce/Retail": [
        "ecommerce",
        "e-commerce",
        "retail",
        "marketplace",
        "shopping",
        "consumer",
    ],
    "Media/Entertainment": [
        "media",
        "entertainment",
        "gaming",
        "streaming",
        "content",
        "publishing",
    ],
    "Education": [
        "education",
        "edtech",
        "learning",
        "university",
        "school",
        "training",
    ],
    "Real Estate": [
        "real estate",
        "proptech",
        "property",
        "housing",
        "construction",
    ],
    "Transportation/Logistics": [
        "transportation",
        "logistics",
        "delivery",
        "shipping",
        "supply chain",
        "mobility",
    ],
    "Energy": [
        "energy",
        "renewable",
        "solar",
        "climate",
        "sustainability",
        "utilities",
    ],
    "Professional Services": [
        "consulting",
        "legal",
        "accounting",
        "advisory",
        "professional services",
    ],
}


def load_industry_mapping(mapping_file: Path | None = None) -> dict[str, list[str]]:
    """Load industry mapping from YAML file.

    Args:
        mapping_file: Path to mapping YAML file

    Returns:
        Dict mapping industry to keyword list
    """
    if mapping_file is None:
        mapping_file = config.seeds_dir / "industry_mapping.yml"

    if not mapping_file.exists():
        logger.warning(f"Industry mapping file not found: {mapping_file}, using defaults")
        return DEFAULT_INDUSTRY_MAPPING

    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping_data = yaml.safe_load(f)
            logger.info(f"Loaded industry mapping from {mapping_file}")
            return mapping_data.get("industries", DEFAULT_INDUSTRY_MAPPING)
    except Exception as e:
        logger.error(f"Failed to load industry mapping from {mapping_file}: {e}")
        return DEFAULT_INDUSTRY_MAPPING


def tag_industry(
    company_name: str,
    company_domain: str | None = None,
    description: str | None = None,
    industry_mapping: dict[str, list[str]] | None = None,
) -> tuple[Optional[str], float]:
    """Tag industry based on company name, domain, and job description.

    Args:
        company_name: Company name
        company_domain: Company domain
        description: Job description
        industry_mapping: Optional industry mapping (loads default if None)

    Returns:
        Tuple of (industry_tag, confidence_score)
    """
    if industry_mapping is None:
        industry_mapping = load_industry_mapping()

    # Combine signals
    signals = []
    if company_name:
        signals.append(clean_text(company_name, lowercase=True))
    if company_domain:
        signals.append(clean_text(company_domain, lowercase=True))
    if description:
        # Only use first 1000 chars of description
        signals.append(clean_text(description[:1000], lowercase=True))

    combined = " ".join(signals)

    # Score industries
    scores = {}
    for industry, keywords in industry_mapping.items():
        score = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Higher weight for company name/domain matches
            if company_name and keyword_lower in company_name.lower():
                score += 5
            if company_domain and keyword_lower in company_domain.lower():
                score += 5
            # Lower weight for description matches
            if description and keyword_lower in description[:1000].lower():
                score += 1

        if score > 0:
            scores[industry] = score

    # Return highest scoring industry
    if scores:
        best_industry = max(scores, key=scores.get)
        max_score = scores[best_industry]

        # Calculate confidence (normalize to 0-1)
        confidence = min(max_score / 10.0, 1.0)

        return best_industry, confidence

    return None, 0.0


def enrich_industry(jobs: list, industry_mapping: dict[str, list[str]] | None = None) -> list:
    """Enrich job records with industry tags.

    Args:
        jobs: List of JobRecord objects
        industry_mapping: Optional industry mapping

    Returns:
        Jobs list with industry_tag populated
    """
    if industry_mapping is None:
        industry_mapping = load_industry_mapping()

    logger.info(f"Tagging industries for {len(jobs)} jobs")

    for job in jobs:
        if not job.industry_tag:  # Only tag if not already set
            industry, confidence = tag_industry(
                job.company_name,
                job.company_domain,
                job.description,
                industry_mapping=industry_mapping,
            )
            job.industry_tag = industry

    tagged_count = sum(1 for job in jobs if job.industry_tag)
    logger.info(f"Tagged {tagged_count}/{len(jobs)} jobs with industries")

    return jobs
