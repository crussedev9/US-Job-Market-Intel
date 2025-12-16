"""CLI for US Job Market Intelligence pipeline."""

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
import pandas as pd
import yaml

from . import __version__
from .config import config
from .logging import setup_logging
from .schema.models import CompanySeed, DiscoveredCompany
from .connectors import CompanyDiscovery
from .pipeline import (
    extract_jobs,
    transform_to_canonical,
    deduplicate_jobs,
    save_to_parquet,
    save_to_csv,
    save_rejects,
    build_latest_snapshot,
    generate_metrics,
    load_parquet_dataset,
)
from .enrich import enrich_role_family, enrich_skills, enrich_industry

app = typer.Typer(
    name="jobintel",
    help="US Job Market Intelligence Pipeline - Greenhouse & Lever data aggregation",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"jobintel version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """US Job Market Intelligence Pipeline."""
    pass


@app.command()
def discover(
    seed_file: Path = typer.Option(
        config.seeds_dir / "discovery_seeds.yml",
        "--seed-file",
        "-s",
        help="Path to discovery seeds YAML file",
    ),
    out: Path = typer.Option(
        config.seeds_dir / "discovered_companies.csv",
        "--out",
        "-o",
        help="Output CSV file for discovered companies",
    ),
    verify: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Verify boards by fetching sample jobs",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Discover new Greenhouse/Lever boards from seeds."""
    setup_logging(log_level)

    console.print(f"[bold]Discovering companies from {seed_file}[/bold]")

    # Load seeds
    if not seed_file.exists():
        console.print(f"[red]Seed file not found: {seed_file}[/red]")
        raise typer.Exit(1)

    with open(seed_file, "r", encoding="utf-8") as f:
        seeds = yaml.safe_load(f)

    discovered_companies = []

    # Discover from domains
    domains = seeds.get("domains", [])
    if domains:
        console.print(f"Probing {len(domains)} domains...")
        with CompanyDiscovery() as discovery:
            domain_tuples = [(d["domain"], d["company_name"]) for d in domains]
            results = discovery.discover_batch(domain_tuples)

            for result in results:
                if not verify or discovery.verify_board(result.ats_type, result.company_name):
                    discovered_companies.append(result)

    # Discover from known URLs
    known_urls = seeds.get("known_careers_urls", [])
    if known_urls:
        console.print(f"Analyzing {len(known_urls)} known URLs...")
        with CompanyDiscovery() as discovery:
            for url in known_urls:
                result = discovery.discover_from_url(url)
                if result:
                    discovered_companies.append(result)

    # Save results
    if discovered_companies:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "company_name",
                    "company_domain",
                    "careers_url",
                    "ats_type",
                    "discovery_method",
                    "discovered_at",
                    "confidence",
                ],
            )
            writer.writeheader()
            for company in discovered_companies:
                writer.writerow(company.model_dump())

        console.print(f"[green]Discovered {len(discovered_companies)} companies[/green]")
        console.print(f"[green]Results saved to {out}[/green]")
    else:
        console.print("[yellow]No companies discovered[/yellow]")


@app.command()
def ingest(
    companies_file: Path = typer.Option(
        config.seeds_dir / "companies.csv",
        "--companies",
        "-c",
        help="Path to companies CSV file",
    ),
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date (YYYY-MM-DD), defaults to today",
    ),
    max_companies: Optional[int] = typer.Option(
        None,
        "--max-companies",
        "-n",
        help="Maximum number of companies to process",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Ingest raw job data from companies."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Ingesting jobs for {run_date_obj}[/bold]")

    # Load companies
    if not companies_file.exists():
        console.print(f"[red]Companies file not found: {companies_file}[/red]")
        raise typer.Exit(1)

    companies = []
    with open(companies_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(
                CompanySeed(
                    company_name=row["company_name"],
                    careers_url=row.get("careers_url"),
                    ats_type=row.get("ats_type"),
                    is_portfolio=row.get("is_portfolio", "false").lower() == "true",
                    notes=row.get("notes"),
                )
            )

    console.print(f"Loaded {len(companies)} companies")

    # Extract
    stats = extract_jobs(companies, run_date_obj, max_companies=max_companies)

    # Display stats
    table = Table(title="Extraction Stats")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


@app.command()
def build(
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date (YYYY-MM-DD), defaults to today",
    ),
    strict_us: bool = typer.Option(
        True,
        "--strict-us/--no-strict-us",
        help="Strict US location filtering",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Build canonical dataset from raw data."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Building dataset for {run_date_obj}[/bold]")

    # Load raw data
    raw_dir = config.raw_dir / run_date_obj.isoformat()
    if not raw_dir.exists():
        console.print(f"[red]No raw data found for {run_date_obj}[/red]")
        raise typer.Exit(1)

    all_jobs = []
    all_rejects = []

    # Process each source directory
    for source_dir in raw_dir.iterdir():
        if not source_dir.is_dir():
            continue

        source = source_dir.name

        for company_dir in source_dir.iterdir():
            if not company_dir.is_dir():
                continue

            jobs_file = company_dir / "jobs.json"
            if not jobs_file.exists():
                continue

            # Load raw jobs
            import json

            with open(jobs_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            company_name = data["company_name"]
            raw_jobs = data["jobs"]

            # Transform
            jobs, rejects = transform_to_canonical(
                raw_jobs, company_name, source, run_date_obj, strict_us=strict_us
            )

            all_jobs.extend(jobs)
            all_rejects.extend(rejects)

    console.print(f"Transformed {len(all_jobs)} valid jobs, {len(all_rejects)} rejected")

    # Enrich
    console.print("Enriching with role families, skills, and industries...")
    all_jobs = enrich_role_family(all_jobs)
    all_jobs = enrich_skills(all_jobs)
    all_jobs = enrich_industry(all_jobs)

    # Deduplicate
    all_jobs = deduplicate_jobs(all_jobs)

    # Save
    if all_jobs:
        save_to_parquet(all_jobs, run_date_obj)
        console.print(f"[green]Saved {len(all_jobs)} jobs to parquet[/green]")

    if all_rejects:
        save_rejects(all_rejects, run_date_obj)
        console.print(f"[yellow]Saved {len(all_rejects)} rejects[/yellow]")


@app.command()
def full_run(
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date (YYYY-MM-DD), defaults to today",
    ),
    discover_first: bool = typer.Option(
        False,
        "--discover-first",
        help="Run discovery before ingestion",
    ),
    max_companies: Optional[int] = typer.Option(
        None,
        "--max-companies",
        "-n",
        help="Maximum number of companies to process",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Run full pipeline: discover, ingest, build, metrics, latest."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Running full pipeline for {run_date_obj}[/bold]")

    # 1. Discovery (optional)
    if discover_first:
        console.print("\n[bold cyan]Step 1: Discovery[/bold cyan]")
        # Note: This would require implementing a proper merge mechanism
        console.print("[yellow]Discovery step skipped (merge logic not implemented)[/yellow]")

    # 2. Ingestion
    console.print("\n[bold cyan]Step 2: Ingestion[/bold cyan]")
    from typer.testing import CliRunner

    runner = CliRunner()
    runner.invoke(
        ingest,
        [
            "--run-date",
            run_date_obj.isoformat(),
            "--max-companies",
            str(max_companies) if max_companies else "999",
            "--log-level",
            log_level,
        ],
    )

    # 3. Build
    console.print("\n[bold cyan]Step 3: Build[/bold cyan]")
    runner.invoke(
        build,
        ["--run-date", run_date_obj.isoformat(), "--log-level", log_level],
    )

    # 4. Metrics
    console.print("\n[bold cyan]Step 4: Metrics[/bold cyan]")
    runner.invoke(
        metrics,
        ["--run-date", run_date_obj.isoformat(), "--log-level", log_level],
    )

    # 5. Latest
    console.print("\n[bold cyan]Step 5: Latest Snapshot[/bold cyan]")
    runner.invoke(
        latest,
        ["--run-date", run_date_obj.isoformat(), "--log-level", log_level],
    )

    console.print("\n[bold green]Full pipeline complete![/bold green]")


@app.command()
def export(
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date (YYYY-MM-DD), defaults to today",
    ),
    format: str = typer.Option(
        "csv",
        "--format",
        "-f",
        help="Export format (csv or parquet)",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Export dataset to CSV or Parquet."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Exporting data for {run_date_obj}[/bold]")

    # Load data
    df = load_parquet_dataset(run_date=run_date_obj)

    if df.empty:
        console.print(f"[red]No data found for {run_date_obj}[/red]")
        raise typer.Exit(1)

    # Export
    if format == "csv":
        output_file = config.exports_dir / f"jobs_{run_date_obj.isoformat()}.csv"
        save_to_csv(df, output_file)
        console.print(f"[green]Exported {len(df)} jobs to {output_file}[/green]")
    else:
        console.print(f"[yellow]Format {format} not yet implemented[/yellow]")


@app.command()
def metrics(
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date (YYYY-MM-DD), defaults to today",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Generate metrics and insights."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Generating metrics for {run_date_obj}[/bold]")

    # Generate metrics
    outputs = generate_metrics(run_date_obj)

    if outputs:
        table = Table(title="Generated Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("File", style="green")

        for name, path in outputs.items():
            table.add_row(name.replace("_", " ").title(), str(path.name))

        console.print(table)
        console.print(f"[green]Generated {len(outputs)} metric files[/green]")
    else:
        console.print("[yellow]No metrics generated[/yellow]")


@app.command()
def latest(
    run_date: str = typer.Option(
        None,
        "--run-date",
        "-d",
        help="Run date to include (YYYY-MM-DD), defaults to today",
    ),
    log_level: str = typer.Option("INFO", "--log-level", "-l", help="Logging level"),
):
    """Build/refresh latest snapshot for Power BI."""
    setup_logging(log_level)

    # Parse run_date
    if run_date:
        run_date_obj = date.fromisoformat(run_date)
    else:
        run_date_obj = date.today()

    console.print(f"[bold]Building latest snapshot (up to {run_date_obj})[/bold]")

    # Build snapshot
    output_dir = build_latest_snapshot(run_date_obj)

    console.print(f"[green]Latest snapshot saved to {output_dir}[/green]")


if __name__ == "__main__":
    app()
