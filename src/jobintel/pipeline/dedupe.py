"""Deduplication stage: remove duplicate job records."""

from typing import Any
from loguru import logger
import pandas as pd

from ..schema.models import JobRecord


def deduplicate_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    """Deduplicate job records based on job_key.

    Keeps the first occurrence of each job_key.

    Args:
        jobs: List of JobRecord objects

    Returns:
        Deduplicated list of JobRecord objects
    """
    if not jobs:
        return []

    logger.info(f"Deduplicating {len(jobs)} jobs")

    # Convert to DataFrame for easier deduplication
    df = pd.DataFrame([job.model_dump() for job in jobs])

    # Deduplicate by job_key (keep first)
    initial_count = len(df)
    df_deduped = df.drop_duplicates(subset=["job_key"], keep="first")
    duplicates_removed = initial_count - len(df_deduped)

    logger.info(f"Removed {duplicates_removed} duplicates, {len(df_deduped)} unique jobs remaining")

    # Convert back to JobRecord objects
    deduped_jobs = [JobRecord(**row) for row in df_deduped.to_dict("records")]

    return deduped_jobs


def deduplicate_across_runs(
    current_jobs: list[JobRecord],
    historical_df: pd.DataFrame,
) -> tuple[list[JobRecord], list[JobRecord]]:
    """Deduplicate current jobs against historical data.

    Args:
        current_jobs: Current run's jobs
        historical_df: Historical jobs DataFrame with 'job_key' column

    Returns:
        Tuple of (new_jobs, existing_jobs)
    """
    if not current_jobs:
        return [], []

    if historical_df.empty:
        logger.info("No historical data, all jobs are new")
        return current_jobs, []

    # Get historical job keys
    historical_keys = set(historical_df["job_key"].unique())

    # Split into new and existing
    new_jobs = []
    existing_jobs = []

    for job in current_jobs:
        if job.job_key in historical_keys:
            existing_jobs.append(job)
        else:
            new_jobs.append(job)

    logger.info(
        f"Dedupe vs history: {len(new_jobs)} new, {len(existing_jobs)} existing"
    )

    return new_jobs, existing_jobs
