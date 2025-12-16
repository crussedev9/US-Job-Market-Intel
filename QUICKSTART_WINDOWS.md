# Quick Start Guide for Windows

## ✅ Installation Complete!

Your US Job Market Intel pipeline is installed and ready to use.

## Running Commands

### Option 1: Activate Virtual Environment (Recommended)

```powershell
# Activate the virtual environment
.\venv\Scripts\activate

# Now you can use jobintel directly
jobintel --version
jobintel --help
```

### Option 2: Direct Execution

```powershell
# Call jobintel.exe directly
.\venv\Scripts\jobintel.exe --version
.\venv\Scripts\jobintel.exe --help
```

## Try It Out!

### 1. Test with 2 Companies

```powershell
# Activate virtual environment first
.\venv\Scripts\activate

# Ingest data from 2 companies
jobintel ingest --max-companies 2

# Build the dataset
jobintel build

# Generate metrics
jobintel metrics

# Create latest snapshot
jobintel latest
```

### 2. Full Pipeline Run

```powershell
# Run entire pipeline (all 7 companies)
jobintel full-run
```

### 3. Discovery (Optional)

```powershell
# Discover new job boards
jobintel discover
```

## Check Your Data

After running the pipeline, check these directories:

```
data/
├── raw/               # Raw JSON from each company
├── staged/
│   ├── jobs/          # Partitioned parquet dataset
│   └── latest/        # Current snapshot (Power BI)
└── exports/
    ├── jobs_latest.csv
    ├── summary_stats_YYYY-MM-DD.csv
    ├── top_skills_overall_YYYY-MM-DD.csv
    └── ...
```

## PowerShell Tips

### Activation Script Error?

If you see "execution of scripts is disabled", run this **once** as Administrator:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:

```powershell
.\venv\Scripts\activate
```

### Daily Automation

Use the included PowerShell script:

```powershell
.\scripts\run_daily_example.ps1
```

Or set up Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Start a program
   - Program: `C:\Python314\python.exe`
   - Arguments: `-m jobintel full-run`
   - Start in: `C:\Users\ckrus\US-Job-Market-Intel`

## Next Steps

1. **Customize Company List**: Edit `data/seeds/companies.csv`
2. **Power BI**: Connect to `data/staged/latest/jobs_latest.parquet`
3. **Read Full Docs**: See [README.md](README.md) for complete documentation

## Common Commands

```powershell
# Show all commands
jobintel --help

# Run with specific date
jobintel full-run --run-date 2025-01-20

# Export to CSV
jobintel export --format csv

# Run tests (requires dev dependencies)
pip install -e ".[dev]"
pytest
```

## Need Help?

- Full documentation: [README.md](README.md)
- Power BI guide: [scripts/powerbi_notes.md](scripts/powerbi_notes.md)
- GitHub issues: https://github.com/crussedev9/US-Job-Market-Intel/issues

Enjoy your job market intelligence pipeline! 🚀
