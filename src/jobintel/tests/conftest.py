"""Pytest fixtures for testing."""

import pytest
from datetime import date, datetime


@pytest.fixture
def sample_greenhouse_job():
    """Sample Greenhouse job record."""
    return {
        "id": 12345,
        "title": "Senior Data Engineer",
        "content": "We are looking for an experienced data engineer...",
        "location": {"name": "San Francisco, CA"},
        "absolute_url": "https://boards.greenhouse.io/company/jobs/12345",
        "updated_at": "2025-01-15T10:00:00Z",
        "metadata": [
            {"name": "department", "value": "Engineering"},
            {"name": "employment_type", "value": "Full-time"},
        ],
    }


@pytest.fixture
def sample_lever_job():
    """Sample Lever job record."""
    return {
        "id": "abc-123",
        "text": "Product Manager",
        "description": "Join our product team to build amazing products...",
        "descriptionPlain": "Join our product team to build amazing products...",
        "categories": {
            "location": "New York, NY",
            "department": "Product",
            "commitment": "Full-time",
        },
        "hostedUrl": "https://jobs.lever.co/company/abc-123",
        "createdAt": "2025-01-10T10:00:00Z",
    }


@pytest.fixture
def sample_job_with_skills():
    """Sample job description with skills."""
    return """
    We are seeking a Senior Data Engineer to join our team.

    Requirements:
    - 5+ years of experience with Python and SQL
    - Expertise in AWS, Snowflake, and dbt
    - Experience with Airflow and Spark
    - Strong understanding of data modeling and ETL pipelines
    - Bachelor's degree in Computer Science or related field

    Nice to have:
    - Experience with Kubernetes and Docker
    - Knowledge of machine learning and TensorFlow
    """


@pytest.fixture
def us_locations():
    """Valid US location strings."""
    return [
        "San Francisco, CA",
        "New York, NY 10001",
        "Boston, MA",
        "Remote, United States",
        "Austin, TX",
        "Seattle, WA",
        "Chicago, IL",
    ]


@pytest.fixture
def non_us_locations():
    """Non-US location strings."""
    return [
        "London, UK",
        "Toronto, Canada",
        "Berlin, Germany",
        "Sydney, Australia",
        "Remote, Europe",
    ]


@pytest.fixture
def ambiguous_locations():
    """Ambiguous location strings."""
    return [
        "Remote",
        "Multiple Locations",
        "Global",
        "Anywhere",
    ]
