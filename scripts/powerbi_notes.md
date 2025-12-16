# Power BI Integration Notes

## Data Sources

### Primary Source: Latest Snapshot

**Recommended for most dashboards**

- **File**: `data/staged/latest/jobs_latest.parquet`
- **Format**: Parquet (best performance) or CSV (`data/exports/jobs_latest.csv`)
- **Update Frequency**: After each pipeline run
- **Content**: Most recent occurrence of each unique job

#### Loading in Power BI

1. **Get Data** → **Parquet** → Navigate to `data/staged/latest/jobs_latest.parquet`
2. OR **Get Data** → **Text/CSV** → Navigate to `data/exports/jobs_latest.csv`

### Historical Data: Partitioned Dataset

**For time-series analysis**

- **Path**: `data/staged/jobs/`
- **Format**: Partitioned Parquet (by `run_date` and `source`)
- **Use Case**: Trend analysis, historical comparisons

#### Loading in Power BI

1. **Get Data** → **Folder** → Navigate to `data/staged/jobs/`
2. Combine files across partitions
3. Use `run_date` column for time-based filtering

### Pre-built Metrics

**For quick dashboard creation**

Located in `data/exports/`:

- `summary_stats_{run_date}.csv` - Run-level statistics
- `top_skills_overall_{run_date}.csv` - Most in-demand skills
- `skills_by_role_family_{run_date}.csv` - Skills demand by role family
- `skills_by_state_{run_date}.csv` - Regional skill demand
- `role_mix_by_industry_{run_date}.csv` - Role distribution by industry

Load these as separate tables and relate via `run_date`.

## Data Model

### Recommended Table Structure

```
┌──────────────┐
│  dim_date    │  (Create in Power BI)
│  - run_date  │
└──────┬───────┘
       │
       │ 1:N
       │
┌──────▼───────┐
│   jobs       │  (jobs_latest.parquet)
│  - job_key   │
│  - run_date  │
│  - company_id│
│  - state     │
│  - ...       │
└──────┬───────┘
       │
       │ N:1
       │
┌──────▼───────┐
│ dim_company  │  (Create from jobs)
│ - company_id │
│ - company_   │
│    name      │
└──────────────┘
```

### Key Columns for Analysis

#### Dimensions

- `company_name` - Company grouping
- `state` - Geographic analysis (US states)
- `city` - City-level analysis
- `role_family` - Role category
- `industry_tag` - Industry classification
- `source` - ATS type (greenhouse/lever)
- `is_remote` - Remote vs onsite
- `employment_type` - Full-time, contract, etc.
- `seniority` - Entry, mid, senior, etc.

#### Measures (to create)

```DAX
Total Jobs = COUNT(jobs[job_key])
Remote % = DIVIDE(COUNTROWS(FILTER(jobs, jobs[is_remote] = TRUE)), COUNTROWS(jobs))
Avg Jobs per Company = DIVIDE([Total Jobs], DISTINCTCOUNT(jobs[company_id]))
```

#### Skills (List Column)

The `skills` column is a JSON array. To analyze:

**Option 1: Power Query Expansion**

```M
= Table.ExpandListColumn(jobs, "skills")
```

Creates one row per skill (unpivot).

**Option 2: Text Analysis**

Use DAX to count skill occurrences:

```DAX
Python Jobs = COUNTROWS(FILTER(jobs, CONTAINSSTRING(jobs[skills], "Python")))
```

## Dashboard Ideas

### 1. Hiring Velocity Dashboard

**Metrics:**

- Total jobs by `run_date` (line chart)
- New jobs vs existing jobs (delta from previous run)
- Jobs by company (bar chart)
- Top hiring companies (table)

**Filters:**

- `run_date` slider
- `role_family` slicer
- `is_remote` toggle

### 2. Geographic Demand Dashboard

**Visualizations:**

- Jobs by state (map or bar chart)
- Top cities (table)
- Remote vs onsite by state (stacked bar)

**Metrics:**

- Jobs per 1M population (if you add census data)
- State concentration index

### 3. Skills Demand Dashboard

**Use Pre-built CSV:**

Load `top_skills_overall_{run_date}.csv` and `skills_by_role_family_{run_date}.csv`

**Visualizations:**

- Top 20 skills (bar chart)
- Skills by role family (matrix)
- Skill growth over time (requires historical data)

**Filters:**

- `role_family`
- `industry_tag`

### 4. Role Mix Analysis

**Use Pre-built CSV:**

Load `role_mix_by_industry_{run_date}.csv`

**Visualizations:**

- Role distribution by industry (stacked bar)
- Industry breakdown (pie chart)
- Engineering vs non-engineering ratio

### 5. Portfolio Company Tracker

**For VC Use Case**

**Filter:**

- `is_portfolio = true` (if you tagged companies in `companies.csv`)

**Metrics:**

- Hiring velocity by portfolio company
- Role mix shifts over time
- Benchmark vs market (compare portfolio avg to overall avg)

## Data Refresh Strategy

### Manual Refresh

1. Run pipeline: `jobintel full-run`
2. In Power BI Desktop: **Home** → **Refresh**

### Scheduled Refresh (Power BI Service)

**Requirements:**

- Power BI Pro or Premium
- Gateway for file-based sources (if not in cloud)

**Setup:**

1. Publish report to Power BI Service
2. Configure data source credentials
3. Set refresh schedule (e.g., daily at 6 AM)

**Note**: Parquet sources may require **On-premises Data Gateway**.

### Alternative: Azure Blob Storage

For cloud-based refreshes:

1. Upload `jobs_latest.parquet` to Azure Blob Storage after each run
2. Connect Power BI to Blob Storage
3. Enable automatic refresh (no gateway needed)

## Performance Tips

### Use Parquet over CSV

- **Faster**: Parquet is columnar and compressed
- **Smaller**: 5-10x smaller than CSV
- **Native Support**: Power BI reads Parquet directly

### Filter Early in Power Query

In Power Query, filter data before loading:

```M
= Table.SelectRows(Source, each [run_date] >= #date(2025, 1, 1))
```

### Aggregate Metrics in Pipeline

Instead of aggregating in Power BI DAX, use pre-built CSVs:

- Load `skills_by_role_family_{run_date}.csv` instead of expanding skills in Power BI
- Reduces data model size and improves performance

### Use Import Mode

For datasets <1GB, use **Import** mode instead of **DirectQuery**.

### Optimize Data Types

In Power Query:

- `job_key`, `company_id` → Text (not whole number)
- `run_date`, `date_posted` → Date
- `is_remote` → True/False
- `skills` → Text (JSON) or expand to list

## Common Issues

### Issue: Skills Column is Text

**Symptom**: Can't analyze skills as list

**Solution**: Expand in Power Query:

```M
= Json.Document([skills])
= Table.ExpandListColumn(jobs, "skills")
```

### Issue: Parquet File Not Found

**Symptom**: "File not found" error

**Solution**:

- Ensure pipeline ran: `jobintel latest`
- Check path: `data/staged/latest/jobs_latest.parquet`
- Use absolute path in Power BI

### Issue: Refresh Fails on Schedule

**Symptom**: Scheduled refresh fails

**Solution**:

- Install On-premises Data Gateway
- OR move data to cloud storage (Azure Blob, OneDrive)

### Issue: Too Many Rows

**Symptom**: Performance degradation

**Solution**:

- Filter to recent `run_date` only (e.g., last 90 days)
- Use aggregated metrics CSVs
- Enable incremental refresh (Power BI Premium)

## Example DAX Measures

### Total Jobs

```DAX
Total Jobs = COUNTROWS(jobs)
```

### Remote Percentage

```DAX
Remote % =
DIVIDE(
    CALCULATE(COUNTROWS(jobs), jobs[is_remote] = TRUE),
    COUNTROWS(jobs),
    0
)
```

### Top Skill Count

```DAX
Python Count =
CALCULATE(
    COUNTROWS(jobs),
    CONTAINSSTRING(jobs[skills], "Python")
)
```

### Jobs Growth (vs Previous Run)

```DAX
Jobs Growth =
VAR CurrentJobs = [Total Jobs]
VAR PreviousDate =
    CALCULATE(
        MAX(jobs[run_date]),
        FILTER(ALL(jobs), jobs[run_date] < MAX(jobs[run_date]))
    )
VAR PreviousJobs =
    CALCULATE([Total Jobs], jobs[run_date] = PreviousDate)
RETURN
    CurrentJobs - PreviousJobs
```

### Average Jobs per Company

```DAX
Avg Jobs per Company =
DIVIDE(
    [Total Jobs],
    DISTINCTCOUNT(jobs[company_id])
)
```

## Sample Power BI Template (PBIX)

A starter template is planned for future release. It will include:

- Pre-configured data model
- Sample dashboards
- DAX measures
- Formatting and themes

Stay tuned!

## Questions?

For Power BI-specific questions:

- Open an issue: https://github.com/crussedev9/US-Job-Market-Intel/issues
- Tag with `power-bi` label
