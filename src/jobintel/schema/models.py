"""Canonical schema models for job data."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class JobRecord(BaseModel):
    """Canonical analytics-ready job record.

    This is the normalized schema that all sources are transformed into.
    Designed for Power BI consumption and economic analysis.
    """

    # Source metadata
    source: str = Field(..., description="Data source: greenhouse|lever")
    source_job_id: str = Field(..., description="Original job ID from source")
    job_url: str = Field(..., description="Public URL to job posting")

    # Company information
    company_name: str = Field(..., description="Company name")
    company_domain: Optional[str] = Field(None, description="Company domain/website")
    company_id: str = Field(..., description="Stable hash of company identifier")

    # Job details
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description text")
    department: Optional[str] = Field(None, description="Department/team")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, etc.")
    seniority: Optional[str] = Field(None, description="Entry, Mid, Senior, Lead, Executive")

    # Location (US-only enforced)
    location_raw: str = Field(..., description="Original location string from source")
    city: Optional[str] = Field(None, description="Parsed city name")
    state: Optional[str] = Field(None, description="US state code (2-letter)")
    postal_code: Optional[str] = Field(None, description="ZIP/postal code")
    msa: Optional[str] = Field(None, description="Metropolitan Statistical Area")
    is_remote: bool = Field(False, description="Remote work flag")
    country: str = Field("US", description="Must be US for this dataset")

    # Dates
    date_posted: Optional[date] = Field(None, description="Original posting date from source")
    date_scraped: datetime = Field(..., description="Timestamp when scraped")

    # Enrichment fields
    role_family: Optional[str] = Field(None, description="Normalized role family from taxonomy")
    skills: list[str] = Field(default_factory=list, description="Extracted skills")
    industry_tag: Optional[str] = Field(None, description="Industry classification")

    # Pipeline metadata
    run_date: date = Field(..., description="Pipeline run date (partition key)")
    job_key: str = Field(..., description="Deterministic hash for deduplication")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "greenhouse",
                "source_job_id": "12345",
                "job_url": "https://boards.greenhouse.io/company/jobs/12345",
                "company_name": "Acme Corp",
                "company_domain": "acme.com",
                "company_id": "abc123def456",
                "title": "Senior Data Engineer",
                "description": "We are looking for...",
                "department": "Engineering",
                "employment_type": "Full-time",
                "seniority": "Senior",
                "location_raw": "San Francisco, CA",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": None,
                "msa": "San Francisco-Oakland-Hayward, CA",
                "is_remote": False,
                "country": "US",
                "date_posted": "2025-01-15",
                "date_scraped": "2025-01-20T10:30:00",
                "role_family": "Tech/Engineering",
                "skills": ["Python", "SQL", "Airflow", "dbt"],
                "industry_tag": "Technology",
                "run_date": "2025-01-20",
                "job_key": "gh_acme_12345_xyz",
            }
        }


class CompanySeed(BaseModel):
    """Company seed for targeted ingestion."""

    company_name: str = Field(..., description="Company name")
    careers_url: Optional[str] = Field(None, description="Careers page URL")
    ats_type: Optional[str] = Field(None, description="ATS type: greenhouse|lever|unknown")
    is_portfolio: bool = Field(False, description="Portfolio company flag")
    notes: Optional[str] = Field(None, description="Optional notes")


class DiscoveredCompany(BaseModel):
    """Company discovered through automated discovery."""

    company_name: str = Field(..., description="Discovered company name")
    company_domain: Optional[str] = Field(None, description="Company domain")
    careers_url: str = Field(..., description="Detected careers URL")
    ats_type: str = Field(..., description="Detected ATS type: greenhouse|lever")
    discovery_method: str = Field(..., description="How it was discovered")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
    confidence: float = Field(..., description="Confidence score 0-1")

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Example Inc",
                "company_domain": "example.com",
                "careers_url": "https://boards.greenhouse.io/exampleinc",
                "ats_type": "greenhouse",
                "discovery_method": "url_pattern",
                "discovered_at": "2025-01-20T10:30:00",
                "confidence": 0.95,
            }
        }
