"""Tests for deduplication logic."""

import pytest
from datetime import date, datetime
from jobintel.schema.models import JobRecord
from jobintel.pipeline.dedupe import deduplicate_jobs
from jobintel.utils.hashing import generate_job_key, generate_company_id


def test_generate_job_key_stable():
    """Test that job keys are stable."""
    key1 = generate_job_key("greenhouse", "Acme Corp", "12345", "Data Engineer")
    key2 = generate_job_key("greenhouse", "Acme Corp", "12345", "Data Engineer")
    assert key1 == key2


def test_generate_job_key_unique():
    """Test that different jobs get different keys."""
    key1 = generate_job_key("greenhouse", "Acme Corp", "12345", "Data Engineer")
    key2 = generate_job_key("greenhouse", "Acme Corp", "67890", "Data Engineer")
    key3 = generate_job_key("lever", "Acme Corp", "12345", "Data Engineer")

    assert key1 != key2
    assert key1 != key3


def test_generate_company_id_stable():
    """Test that company IDs are stable."""
    id1 = generate_company_id("Acme Corp", "acme.com")
    id2 = generate_company_id("Acme Corp", "acme.com")
    assert id1 == id2


def test_deduplicate_jobs():
    """Test job deduplication."""
    # Create duplicate jobs
    job1 = JobRecord(
        source="greenhouse",
        source_job_id="12345",
        job_url="https://example.com/1",
        company_name="Acme",
        company_id="abc123",
        title="Engineer",
        description="Job desc",
        location_raw="SF, CA",
        city="San Francisco",
        state="CA",
        country="US",
        is_remote=False,
        date_scraped=datetime.now(),
        run_date=date.today(),
        job_key="test_key_1",
    )

    job2 = JobRecord(
        source="greenhouse",
        source_job_id="12345",
        job_url="https://example.com/1",
        company_name="Acme",
        company_id="abc123",
        title="Engineer",
        description="Job desc",
        location_raw="SF, CA",
        city="San Francisco",
        state="CA",
        country="US",
        is_remote=False,
        date_scraped=datetime.now(),
        run_date=date.today(),
        job_key="test_key_1",  # Same key as job1
    )

    job3 = JobRecord(
        source="greenhouse",
        source_job_id="67890",
        job_url="https://example.com/2",
        company_name="Acme",
        company_id="abc123",
        title="Manager",
        description="Job desc 2",
        location_raw="NY, NY",
        city="New York",
        state="NY",
        country="US",
        is_remote=False,
        date_scraped=datetime.now(),
        run_date=date.today(),
        job_key="test_key_2",  # Different key
    )

    jobs = [job1, job2, job3]
    deduped = deduplicate_jobs(jobs)

    assert len(deduped) == 2  # Should remove one duplicate
    assert job1.job_key in [j.job_key for j in deduped]
    assert job3.job_key in [j.job_key for j in deduped]
