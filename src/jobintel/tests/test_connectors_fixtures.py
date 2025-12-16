"""Tests for connectors using fixtures (no live HTTP)."""

import pytest
from jobintel.connectors.greenhouse import GreenhouseConnector
from jobintel.connectors.lever import LeverConnector


def test_greenhouse_detect_board_token():
    """Test Greenhouse board token detection."""
    urls = [
        ("https://boards.greenhouse.io/openai", "openai"),
        ("https://boards.greenhouse.io/stripe/jobs/12345", "stripe"),
        ("https://careers.greenhouse.io/anthropic", "anthropic"),
    ]

    for url, expected_token in urls:
        token = GreenhouseConnector.detect_board_token(url)
        assert token == expected_token, f"Failed for {url}"


def test_greenhouse_is_greenhouse_url():
    """Test Greenhouse URL detection."""
    assert GreenhouseConnector.is_greenhouse_url("https://boards.greenhouse.io/openai")
    assert GreenhouseConnector.is_greenhouse_url("https://careers.greenhouse.io/stripe")
    assert not GreenhouseConnector.is_greenhouse_url("https://jobs.lever.co/netflix")


def test_greenhouse_get_job_url():
    """Test Greenhouse job URL generation."""
    connector = GreenhouseConnector()
    url = connector.get_job_url("openai", "12345")
    assert url == "https://boards.greenhouse.io/openai/jobs/12345"


def test_lever_detect_company_identifier():
    """Test Lever company identifier detection."""
    urls = [
        ("https://jobs.lever.co/netflix", "netflix"),
        ("https://jobs.lever.co/faire/abc-123", "faire"),
    ]

    for url, expected_id in urls:
        company_id = LeverConnector.detect_company_identifier(url)
        assert company_id == expected_id, f"Failed for {url}"


def test_lever_is_lever_url():
    """Test Lever URL detection."""
    assert LeverConnector.is_lever_url("https://jobs.lever.co/netflix")
    assert LeverConnector.is_lever_url("https://jobs.lever.co/faire")
    assert not LeverConnector.is_lever_url("https://boards.greenhouse.io/openai")


def test_lever_get_job_url():
    """Test Lever job URL generation."""
    connector = LeverConnector()
    url = connector.get_job_url("netflix", "abc-123")
    assert url == "https://jobs.lever.co/netflix/abc-123"


def test_transform_greenhouse_job(sample_greenhouse_job):
    """Test transforming Greenhouse job to canonical schema."""
    from jobintel.pipeline.transform import _transform_greenhouse_job
    from datetime import date

    job = _transform_greenhouse_job(
        sample_greenhouse_job,
        "Test Company",
        date.today(),
        strict_us=True,
    )

    assert job is not None
    assert job.source == "greenhouse"
    assert job.source_job_id == "12345"
    assert job.title == "Senior Data Engineer"
    assert job.state == "CA"
    assert job.city == "San Francisco"


def test_transform_lever_job(sample_lever_job):
    """Test transforming Lever job to canonical schema."""
    from jobintel.pipeline.transform import _transform_lever_job
    from datetime import date

    job = _transform_lever_job(
        sample_lever_job,
        "Test Company",
        date.today(),
        strict_us=True,
    )

    assert job is not None
    assert job.source == "lever"
    assert job.source_job_id == "abc-123"
    assert job.title == "Product Manager"
    assert job.state == "NY"
    assert job.city == "New York"


def test_extract_skills(sample_job_with_skills):
    """Test skills extraction."""
    from jobintel.enrich.skills import extract_skills

    skills = extract_skills(sample_job_with_skills)

    assert "Python" in skills
    assert "SQL" in skills
    assert "AWS" in skills
    assert "Snowflake" in skills
    assert "dbt" in skills
    assert "Airflow" in skills
    assert "Spark" in skills
    assert len(skills) >= 5
