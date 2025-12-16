"""Skills extraction from job descriptions."""

import re
from typing import Optional
import yaml
from pathlib import Path
from loguru import logger

from ..config import config
from ..utils.text import clean_text


# Default skills list (curated)
DEFAULT_SKILLS = {
    "programming_languages": [
        "Python",
        "JavaScript",
        "TypeScript",
        "Java",
        "C++",
        "C#",
        "Go",
        "Rust",
        "Ruby",
        "PHP",
        "Swift",
        "Kotlin",
        "Scala",
        "R",
        "SQL",
    ],
    "cloud_platforms": [
        "AWS",
        "Azure",
        "GCP",
        "Google Cloud",
        "Kubernetes",
        "Docker",
        "Terraform",
        "CloudFormation",
    ],
    "data_tools": [
        "Spark",
        "Hadoop",
        "Airflow",
        "dbt",
        "Snowflake",
        "BigQuery",
        "Redshift",
        "Databricks",
        "Kafka",
        "Flink",
    ],
    "ml_ai": [
        "TensorFlow",
        "PyTorch",
        "scikit-learn",
        "Keras",
        "LangChain",
        "Hugging Face",
        "OpenAI",
        "LLM",
        "GPT",
        "Computer Vision",
        "NLP",
    ],
    "bi_tools": [
        "Tableau",
        "Power BI",
        "Looker",
        "Qlik",
        "Metabase",
        "Mode",
    ],
    "sales_tools": [
        "Salesforce",
        "HubSpot",
        "Outreach",
        "SalesLoft",
        "Gong",
    ],
    "collaboration": [
        "Slack",
        "Jira",
        "Confluence",
        "Notion",
        "Asana",
        "Monday",
    ],
    "frameworks": [
        "React",
        "Angular",
        "Vue",
        "Django",
        "Flask",
        "FastAPI",
        "Spring",
        "Rails",
        "Node.js",
        ".NET",
    ],
}


def load_skills_list(skills_file: Path | None = None) -> dict[str, list[str]]:
    """Load skills list from YAML file.

    Args:
        skills_file: Path to skills YAML file

    Returns:
        Dict mapping skill category to skill list
    """
    if skills_file is None:
        skills_file = config.seeds_dir / "skills.yml"

    if not skills_file.exists():
        logger.warning(f"Skills file not found: {skills_file}, using defaults")
        return DEFAULT_SKILLS

    try:
        with open(skills_file, "r", encoding="utf-8") as f:
            skills_data = yaml.safe_load(f)
            logger.info(f"Loaded skills from {skills_file}")
            return skills_data.get("skills", DEFAULT_SKILLS)
    except Exception as e:
        logger.error(f"Failed to load skills from {skills_file}: {e}")
        return DEFAULT_SKILLS


def _flatten_skills(skills_dict: dict[str, list[str]]) -> list[str]:
    """Flatten skills dict to list.

    Args:
        skills_dict: Skills organized by category

    Returns:
        Flat list of all skills
    """
    skills = []
    for category_skills in skills_dict.values():
        skills.extend(category_skills)
    return skills


def extract_skills(
    text: str,
    skills_list: dict[str, list[str]] | None = None,
    case_sensitive: bool = False,
) -> list[str]:
    """Extract skills from text.

    Args:
        text: Text to extract skills from (job description)
        skills_list: Optional skills list (loads default if None)
        case_sensitive: Whether to match case-sensitively

    Returns:
        List of extracted skills
    """
    if skills_list is None:
        skills_list = load_skills_list()

    # Flatten skills
    all_skills = _flatten_skills(skills_list)

    # Clean text
    text_clean = clean_text(text)

    # Extract skills
    found_skills = set()

    for skill in all_skills:
        # Create pattern (word boundary for better matching)
        if case_sensitive:
            pattern = rf"\b{re.escape(skill)}\b"
            flags = 0
        else:
            pattern = rf"\b{re.escape(skill)}\b"
            flags = re.IGNORECASE

        if re.search(pattern, text_clean, flags=flags):
            found_skills.add(skill)

    return sorted(found_skills)


def enrich_skills(jobs: list, skills_list: dict[str, list[str]] | None = None) -> list:
    """Enrich job records with extracted skills.

    Args:
        jobs: List of JobRecord objects
        skills_list: Optional skills list

    Returns:
        Jobs list with skills populated
    """
    if skills_list is None:
        skills_list = load_skills_list()

    logger.info(f"Extracting skills for {len(jobs)} jobs")

    for job in jobs:
        if not job.skills:  # Only extract if not already set
            # Extract from title + description
            combined_text = f"{job.title} {job.description}"
            job.skills = extract_skills(combined_text, skills_list=skills_list)

    jobs_with_skills = sum(1 for job in jobs if job.skills)
    logger.info(f"Extracted skills for {jobs_with_skills}/{len(jobs)} jobs")

    return jobs
