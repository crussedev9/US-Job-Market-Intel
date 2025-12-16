"""Load stage: save processed data to storage."""

from datetime import date
from pathlib import Path
from typing import Any
from loguru import logger
import pandas as pd

from ..config import config
from ..schema.models import JobRecord


def save_to_parquet(
    jobs: list[JobRecord],
    run_date: date,
    partition_by: list[str] | None = None,
) -> Path:
    """Save jobs to Parquet format.

    Args:
        jobs: List of JobRecord objects
        run_date: Run date
        partition_by: Optional partition columns (default: ["run_date", "source"])

    Returns:
        Path to saved parquet file/directory
    """
    if not jobs:
        logger.warning("No jobs to save")
        return config.staged_dir

    # Convert to DataFrame
    df = pd.DataFrame([job.model_dump() for job in jobs])

    # Set partitioning
    if partition_by is None:
        partition_by = ["run_date", "source"]

    # Output directory
    output_dir = config.staged_dir / "jobs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save partitioned parquet
    logger.info(f"Saving {len(df)} jobs to {output_dir} (partitioned by {partition_by})")

    # Use pyarrow engine for better performance
    df.to_parquet(
        output_dir,
        engine="pyarrow",
        partition_cols=partition_by,
        index=False,
        compression="snappy",
    )

    logger.info(f"Saved {len(df)} jobs to {output_dir}")
    return output_dir


def save_to_csv(
    jobs: list[JobRecord] | pd.DataFrame,
    output_file: Path,
) -> None:
    """Save jobs to CSV format.

    Args:
        jobs: List of JobRecord objects or DataFrame
        output_file: Output CSV file path
    """
    if isinstance(jobs, list):
        if not jobs:
            logger.warning("No jobs to save")
            return
        df = pd.DataFrame([job.model_dump() for job in jobs])
    else:
        df = jobs

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save CSV
    logger.info(f"Saving {len(df)} jobs to {output_file}")
    df.to_csv(output_file, index=False, encoding="utf-8")


def save_rejects(
    rejects: list[dict[str, Any]],
    run_date: date,
) -> None:
    """Save rejected jobs to CSV.

    Args:
        rejects: List of reject records
        run_date: Run date
    """
    if not rejects:
        logger.info("No rejects to save")
        return

    df = pd.DataFrame(rejects)
    output_file = config.exports_dir / f"rejects_{run_date.isoformat()}.csv"

    logger.info(f"Saving {len(df)} rejects to {output_file}")
    df.to_csv(output_file, index=False, encoding="utf-8")


def load_parquet_dataset(
    run_date: date | None = None,
    source: str | None = None,
) -> pd.DataFrame:
    """Load parquet dataset with optional filtering.

    Args:
        run_date: Optional run date filter
        source: Optional source filter

    Returns:
        DataFrame with loaded data
    """
    dataset_dir = config.staged_dir / "jobs"

    if not dataset_dir.exists():
        logger.warning(f"Dataset directory not found: {dataset_dir}")
        return pd.DataFrame()

    # Load entire dataset
    try:
        df = pd.read_parquet(dataset_dir, engine="pyarrow")

        # Apply filters
        if run_date:
            df = df[df["run_date"] == run_date.isoformat()]
        if source:
            df = df[df["source"] == source]

        logger.info(f"Loaded {len(df)} jobs from {dataset_dir}")
        return df

    except Exception as e:
        logger.error(f"Failed to load parquet dataset: {e}")
        return pd.DataFrame()
