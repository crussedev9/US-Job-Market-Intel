# US Job Market Intel

> **US-only job listings intelligence pipeline**
> Aggregates data from Greenhouse & Lever job boards (Workday excluded by design)

[![Python Tests](https://github.com/crussedev9/US-Job-Market-Intel/actions/workflows/python-tests.yml/badge.svg)](https://github.com/crussedev9/US-Job-Market-Intel/actions/workflows/python-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

US Job Market Intel is a CLI-first data pipeline that collects, normalizes, and enriches job posting data from public Greenhouse and Lever job boards. It's designed for:

- **VC Firms**: Track hiring velocity, role-mix shifts, portfolio company benchmarking
- **Economic Research**: Regional demand analysis, remote work trends, industry signals
- **HR Analytics**: Skills demand tracking, role taxonomy, labor market insights

### Key Features

- ✅ **Automatic Discovery**: Find new Greenhouse/Lever boards programmatically
- ✅ **Historical Partitions**: Track changes over time with run_date partitioning
- ✅ **Latest Snapshot**: Power BI-ready "current state" dataset
- ✅ **US-Only Filtering**: Strict location validation with state-level parsing
- ✅ **Enrichment Pipeline**: Role family classification, skills extraction, industry tagging
- ✅ **Metrics & Insights**: Pre-built aggregations for skills, roles, and industries
- ❌ **Workday Excluded**: By design (no login bypass or scraping)

## Architecture

```
┌─────────────┐
│   Sources   │  Greenhouse API, Lever API
└──────┬──────┘
       │
       v
┌─────────────┐
│  Discovery  │  Automatic board detection
└──────┬──────┘
       │
       v
┌─────────────┐
│   Extract   │  Raw JSON → data/raw/{run_date}/{source}/
└──────┬──────┘
       │
       v
┌─────────────┐
│ Transform + │  Canonical schema + US filtering
│  Enrich     │  Role families, skills, industry tags
└──────┬──────┘
       │
       v
┌─────────────┐
│   Dedupe    │  Stable job_key hashing
└──────┬──────┘
       │
       v
┌─────────────┐
│    Load     │  Parquet (partitioned) + CSV exports
└──────┬──────┘
       │
       v
┌─────────────┐
│   Latest    │  Current snapshot for Power BI
│  Snapshot   │
└─────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/crussedev9/US-Job-Market-Intel.git
cd US-Job-Market-Intel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure Companies

Edit `data/seeds/companies.csv`:

```csv
company_name,careers_url,ats_type,is_portfolio,notes
OpenAI,https://boards.greenhouse.io/openai,greenhouse,false,AI research
Stripe,https://boards.greenhouse.io/stripe,greenhouse,false,Payments
Netflix,https://jobs.lever.co/netflix,lever,false,Streaming
```

### 2. Run Pipeline

```bash
# Full pipeline for today
jobintel full-run

# Or run stages individually
jobintel ingest --run-date 2025-01-20
jobintel build --run-date 2025-01-20
jobintel metrics --run-date 2025-01-20
jobintel latest --run-date 2025-01-20
```

### 3. Access Data

Output files:

```
data/
├── staged/
│   ├── jobs/                        # Partitioned parquet dataset
│   │   ├── run_date=2025-01-20/
│   │   │   ├── source=greenhouse/
│   │   │   └── source=lever/
│   └── latest/
│       └── jobs_latest.parquet      # Power BI snapshot
├── exports/
│   ├── jobs_latest.csv
│   ├── summary_stats_2025-01-20.csv
│   ├── top_skills_overall_2025-01-20.csv
│   ├── skills_by_role_family_2025-01-20.csv
│   ├── skills_by_state_2025-01-20.csv
│   └── role_mix_by_industry_2025-01-20.csv
└── raw/
    └── 2025-01-20/                  # Raw JSON by company
```

## CLI Commands

### Discovery

Automatically find new Greenhouse/Lever boards:

```bash
# Discover from seeds
jobintel discover --seed-file data/seeds/discovery_seeds.yml \
                  --out data/seeds/discovered_companies.csv

# Edit discovery_seeds.yml to add company domains
```

### Ingestion

Pull raw job data:

```bash
# Ingest from all companies
jobintel ingest --companies data/seeds/companies.csv

# Limit to 10 companies for testing
jobintel ingest --max-companies 10

# Specify run date
jobintel ingest --run-date 2025-01-15
```

### Build

Transform raw data to canonical schema:

```bash
# Build dataset (includes enrichment)
jobintel build --run-date 2025-01-20

# Disable strict US filtering (not recommended)
jobintel build --no-strict-us
```

### Metrics

Generate insights and aggregations:

```bash
# Generate all metrics
jobintel metrics --run-date 2025-01-20
```

### Latest Snapshot

Refresh current state dataset:

```bash
# Update latest snapshot
jobintel latest --run-date 2025-01-20
```

### Export

Export to CSV:

```bash
# Export run to CSV
jobintel export --run-date 2025-01-20 --format csv
```

### Full Run

Execute entire pipeline:

```bash
# Full pipeline with discovery
jobintel full-run --discover-first --run-date 2025-01-20

# Full pipeline (skip discovery)
jobintel full-run
```

## How Discovery Works

Discovery finds new Greenhouse/Lever boards **without** login bypass or scraping:

### Method 1: URL Pattern Detection

Given a careers URL, detect ATS type:

```python
# Greenhouse: boards.greenhouse.io/{token}
# Lever: jobs.lever.co/{company}
```

### Method 2: Domain Probing

For a company domain, try common patterns:

```python
https://boards.greenhouse.io/{clean_domain}
https://jobs.lever.co/{company_name_slug}
```

### Limitations

- **Public boards only**: No authentication bypass
- **No heavy crawling**: Respects ToS and robots.txt
- **Best effort**: Some boards may be missed if not following standard patterns

### Expanding Seeds

Edit `data/seeds/discovery_seeds.yml`:

```yaml
domains:
  - domain: "example.com"
    company_name: "Example Inc"

known_careers_urls:
  - "https://boards.greenhouse.io/newcompany"
```

Then run:

```bash
jobintel discover
```

Merge discovered companies into `companies.csv` manually.

## US-Only Filtering

### Strict Mode (Default)

Jobs are **excluded** unless they clearly map to US:

1. ✅ State code present: "San Francisco, CA"
2. ✅ State name present: "Boston, Massachusetts"
3. ✅ Explicit "United States" keyword
4. ❌ Ambiguous: "Remote", "Multiple Locations"
5. ❌ Non-US: "London, UK", "Toronto, Canada"

### Rejected Jobs

Non-US jobs are logged to:

```
data/exports/rejects_{run_date}.csv
```

Review this file to verify filtering accuracy.

## Canonical Schema

Each job record includes:

| Field | Type | Description |
|-------|------|-------------|
| `source` | str | greenhouse \| lever |
| `source_job_id` | str | Original job ID |
| `job_url` | str | Public posting URL |
| `company_name` | str | Company name |
| `company_id` | str | Stable hash |
| `title` | str | Job title |
| `description` | str | Full description |
| `department` | str? | Department/team |
| `employment_type` | str? | Full-time, Contract, etc. |
| `seniority` | str? | Entry, Mid, Senior, etc. |
| `location_raw` | str | Original location string |
| `city` | str? | Parsed city |
| `state` | str? | US state code (2-letter) |
| `postal_code` | str? | ZIP code |
| `msa` | str? | Metropolitan area |
| `is_remote` | bool | Remote flag |
| `country` | str | "US" (enforced) |
| `date_posted` | date? | Original post date |
| `date_scraped` | datetime | Scrape timestamp |
| `role_family` | str? | Normalized role category |
| `skills` | list[str] | Extracted skills |
| `industry_tag` | str? | Industry classification |
| `run_date` | date | Pipeline run date |
| `job_key` | str | Deduplication hash |

## Enrichment

### Role Family Classification

Maps jobs to 10+ role families:

- Tech/Engineering
- Data/AI
- Product/Design
- Sales
- Marketing
- Customer Success
- Finance
- HR/Talent
- Operations/Strategy
- Legal/Compliance

Configured in `data/seeds/role_taxonomy.yml`.

### Skills Extraction

Extracts skills from title + description:

- Programming languages (Python, Java, Go, etc.)
- Cloud platforms (AWS, Azure, GCP)
- Data tools (Snowflake, dbt, Airflow)
- ML/AI (TensorFlow, PyTorch, LLM)
- BI tools (Tableau, Power BI)
- Sales tools (Salesforce, HubSpot)

Configured in `data/seeds/skills.yml`.

### Industry Tagging

Rule-based industry classification:

- Technology
- Financial Services
- Healthcare
- E-commerce/Retail
- Media/Entertainment
- Education
- Real Estate
- Transportation/Logistics
- Energy
- Professional Services

Configured in `data/seeds/industry_mapping.yml`.

## Power BI Integration

### Latest Snapshot

Power BI should connect to:

```
data/staged/latest/jobs_latest.parquet
```

Or CSV alternative:

```
data/exports/jobs_latest.csv
```

### What is "Latest"?

The latest snapshot contains the most recent occurrence of each unique job (by `job_key`) across all historical runs.

**Strategy**: For each `job_key`, keep only the record from the most recent `run_date`.

### Historical Analysis

For time-series analysis, connect to partitioned dataset:

```
data/staged/jobs/
```

Filter by `run_date` in Power BI.

### Pre-built Metrics

Load these CSVs for quick dashboards:

- `summary_stats_{run_date}.csv` - Run-level stats
- `top_skills_overall_{run_date}.csv` - Most demanded skills
- `skills_by_role_family_{run_date}.csv` - Skills by role
- `skills_by_state_{run_date}.csv` - Regional skill demand
- `role_mix_by_industry_{run_date}.csv` - Role distribution by industry

## Testing

Run tests:

```bash
# All tests
pytest

# With coverage
pytest --cov=jobintel --cov-report=html

# Specific test file
pytest src/jobintel/tests/test_us_filter.py -v
```

Tests cover:

- ✅ US location parsing
- ✅ Deduplication stability
- ✅ Role family classification
- ✅ Industry tagging
- ✅ Connector URL parsing

## Development

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/jobintel
```

### Adding New Connectors

To add a new ATS (e.g., Ashby, BambooHR):

1. Create `src/jobintel/connectors/{ats_name}.py`
2. Inherit from `BaseConnector`
3. Implement `fetch_jobs()` and `get_job_url()`
4. Add transformer in `pipeline/transform.py`
5. Update discovery logic

## Limitations & Non-Goals

### What This Project Does NOT Do

- ❌ **No Workday**: Workday jobs are excluded by design
- ❌ **No Login Bypass**: Only public, unauthenticated endpoints
- ❌ **No CAPTCHA Solving**: Respects anti-bot measures
- ❌ **No UI**: CLI-only (Power BI is the UI)
- ❌ **No Real-time**: Batch processing only
- ❌ **No Global Data**: US-only (by strict filtering)

### Known Limitations

- **Discovery Coverage**: Not all Greenhouse/Lever boards are findable programmatically
- **Location Parsing**: Some edge cases may be misclassified
- **Skills Extraction**: Keyword-based (not NLP/LLM)
- **Industry Tagging**: Rule-based (not ML)

## Scheduling

### Daily Runs

Use cron (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/US-Job-Market-Intel && /path/to/venv/bin/jobintel full-run
```

Use Task Scheduler (Windows):

```powershell
# See scripts/run_daily_example.ps1
```

### GitHub Actions (Optional)

You can schedule runs in GitHub Actions:

```yaml
# .github/workflows/daily-run.yml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure CI passes
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- **Issues**: https://github.com/crussedev9/US-Job-Market-Intel/issues
- **Discussions**: https://github.com/crussedev9/US-Job-Market-Intel/discussions

## Acknowledgments

- Greenhouse & Lever for providing public APIs
- Built with: Python, pandas, pyarrow, pydantic, typer, httpx, loguru, rich

---

**Disclaimer**: This tool is for research and analytics purposes. Always respect job board terms of service and rate limits. Do not use for spam, unsolicited outreach, or other unethical purposes.
