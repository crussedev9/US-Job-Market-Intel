"""Latest snapshot builder: maintain current state for Power BI."""

from datetime import date
from pathlib import Path
from loguru import logger
import pandas as pd

from ..config import config
from .load import load_parquet_dataset, save_to_csv


def build_latest_snapshot(run_date: date) -> Path:
    """Build/refresh latest snapshot dataset.

    Strategy: Keep the most recent occurrence of each job_key across all run_dates.

    Args:
        run_date: Run date to include in snapshot

    Returns:
        Path to latest snapshot parquet
    """
    logger.info(f"Building latest snapshot including run_date={run_date}")

    # Load all historical data
    df_all = load_parquet_dataset()

    if df_all.empty:
        logger.warning("No data found for snapshot")
        return config.staged_dir / "latest"

    # Convert run_date to datetime for sorting
    df_all["run_date_dt"] = pd.to_datetime(df_all["run_date"])

    # Sort by run_date descending
    df_all = df_all.sort_values("run_date_dt", ascending=False)

    # Keep first (most recent) occurrence of each job_key
    df_latest = df_all.drop_duplicates(subset=["job_key"], keep="first")

    # Drop temp column
    df_latest = df_latest.drop(columns=["run_date_dt"])

    logger.info(f"Latest snapshot: {len(df_latest)} unique jobs")

    # Save to staged_latest/
    output_dir = config.staged_dir / "latest"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as single parquet (no partitioning for latest)
    output_file = output_dir / "jobs_latest.parquet"
    df_latest.to_parquet(
        output_file,
        engine="pyarrow",
        index=False,
        compression="snappy",
    )

    logger.info(f"Saved latest snapshot to {output_file}")

    # Also save CSV for convenience
    csv_file = config.exports_dir / "jobs_latest.csv"
    save_to_csv(df_latest, csv_file)

    return output_dir


def get_latest_snapshot() -> pd.DataFrame:
    """Load the latest snapshot.

    Returns:
        DataFrame with latest jobs
    """
    snapshot_file = config.staged_dir / "latest" / "jobs_latest.parquet"

    if not snapshot_file.exists():
        logger.warning(f"Latest snapshot not found: {snapshot_file}")
        return pd.DataFrame()

    df = pd.read_parquet(snapshot_file, engine="pyarrow")
    logger.info(f"Loaded {len(df)} jobs from latest snapshot")

    return df
