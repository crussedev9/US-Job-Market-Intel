"""Metrics and insights generation."""

from datetime import date
from pathlib import Path
from loguru import logger
import pandas as pd

from ..config import config
from .load import load_parquet_dataset


def generate_metrics(run_date: date) -> dict[str, Path]:
    """Generate metrics and insights for a run.

    Creates:
    - skills_by_role_family_{run_date}.csv
    - skills_by_state_{run_date}.csv
    - top_skills_overall_{run_date}.csv
    - role_mix_by_industry_{run_date}.csv
    - summary_stats_{run_date}.csv

    Args:
        run_date: Run date to generate metrics for

    Returns:
        Dict mapping metric name to output file path
    """
    logger.info(f"Generating metrics for {run_date}")

    # Load data for this run
    df = load_parquet_dataset(run_date=run_date)

    if df.empty:
        logger.warning(f"No data found for {run_date}")
        return {}

    outputs = {}

    # 1. Skills by role family
    outputs["skills_by_role_family"] = _skills_by_role_family(df, run_date)

    # 2. Skills by state
    outputs["skills_by_state"] = _skills_by_state(df, run_date)

    # 3. Top skills overall
    outputs["top_skills_overall"] = _top_skills_overall(df, run_date)

    # 4. Role mix by industry
    outputs["role_mix_by_industry"] = _role_mix_by_industry(df, run_date)

    # 5. Summary stats
    outputs["summary_stats"] = _summary_stats(df, run_date)

    logger.info(f"Generated {len(outputs)} metric files")
    return outputs


def _skills_by_role_family(df: pd.DataFrame, run_date: date) -> Path:
    """Generate skills by role family metrics.

    Args:
        df: Jobs DataFrame
        run_date: Run date

    Returns:
        Path to output CSV
    """
    # Explode skills list
    df_skills = df[df["skills"].notna() & (df["skills"].str.len() > 0)].copy()
    df_skills["skill"] = df_skills["skills"].apply(lambda x: x if isinstance(x, list) else [])
    df_exploded = df_skills.explode("skill")

    if df_exploded.empty:
        logger.warning("No skills data for role_family aggregation")
        return config.exports_dir / f"skills_by_role_family_{run_date.isoformat()}.csv"

    # Group and count
    result = (
        df_exploded[df_exploded["role_family"].notna()]
        .groupby(["role_family", "skill"])
        .size()
        .reset_index(name="job_count")
        .sort_values(["role_family", "job_count"], ascending=[True, False])
    )

    # Save
    output_file = config.exports_dir / f"skills_by_role_family_{run_date.isoformat()}.csv"
    result.to_csv(output_file, index=False)
    logger.info(f"Saved skills_by_role_family to {output_file}")

    return output_file


def _skills_by_state(df: pd.DataFrame, run_date: date) -> Path:
    """Generate skills by state metrics.

    Args:
        df: Jobs DataFrame
        run_date: Run date

    Returns:
        Path to output CSV
    """
    df_skills = df[df["skills"].notna() & (df["skills"].str.len() > 0)].copy()
    df_skills["skill"] = df_skills["skills"].apply(lambda x: x if isinstance(x, list) else [])
    df_exploded = df_skills.explode("skill")

    if df_exploded.empty:
        logger.warning("No skills data for state aggregation")
        return config.exports_dir / f"skills_by_state_{run_date.isoformat()}.csv"

    result = (
        df_exploded[df_exploded["state"].notna()]
        .groupby(["state", "skill"])
        .size()
        .reset_index(name="job_count")
        .sort_values(["state", "job_count"], ascending=[True, False])
    )

    output_file = config.exports_dir / f"skills_by_state_{run_date.isoformat()}.csv"
    result.to_csv(output_file, index=False)
    logger.info(f"Saved skills_by_state to {output_file}")

    return output_file


def _top_skills_overall(df: pd.DataFrame, run_date: date) -> Path:
    """Generate top skills overall.

    Args:
        df: Jobs DataFrame
        run_date: Run date

    Returns:
        Path to output CSV
    """
    df_skills = df[df["skills"].notna() & (df["skills"].str.len() > 0)].copy()
    df_skills["skill"] = df_skills["skills"].apply(lambda x: x if isinstance(x, list) else [])
    df_exploded = df_skills.explode("skill")

    if df_exploded.empty:
        logger.warning("No skills data for overall aggregation")
        return config.exports_dir / f"top_skills_overall_{run_date.isoformat()}.csv"

    result = (
        df_exploded.groupby("skill")
        .size()
        .reset_index(name="job_count")
        .sort_values("job_count", ascending=False)
        .head(100)  # Top 100
    )

    output_file = config.exports_dir / f"top_skills_overall_{run_date.isoformat()}.csv"
    result.to_csv(output_file, index=False)
    logger.info(f"Saved top_skills_overall to {output_file}")

    return output_file


def _role_mix_by_industry(df: pd.DataFrame, run_date: date) -> Path:
    """Generate role mix by industry.

    Args:
        df: Jobs DataFrame
        run_date: Run date

    Returns:
        Path to output CSV
    """
    result = (
        df[df["industry_tag"].notna() & df["role_family"].notna()]
        .groupby(["industry_tag", "role_family"])
        .size()
        .reset_index(name="job_count")
        .sort_values(["industry_tag", "job_count"], ascending=[True, False])
    )

    output_file = config.exports_dir / f"role_mix_by_industry_{run_date.isoformat()}.csv"
    result.to_csv(output_file, index=False)
    logger.info(f"Saved role_mix_by_industry to {output_file}")

    return output_file


def _summary_stats(df: pd.DataFrame, run_date: date) -> Path:
    """Generate summary statistics.

    Args:
        df: Jobs DataFrame
        run_date: Run date

    Returns:
        Path to output CSV
    """
    stats = {
        "run_date": [run_date.isoformat()],
        "total_jobs": [len(df)],
        "greenhouse_jobs": [len(df[df["source"] == "greenhouse"])],
        "lever_jobs": [len(df[df["source"] == "lever"])],
        "unique_companies": [df["company_id"].nunique()],
        "remote_jobs": [len(df[df["is_remote"]])],
        "states_covered": [df["state"].nunique()],
        "jobs_with_skills": [len(df[df["skills"].str.len() > 0])],
        "jobs_with_industry": [len(df[df["industry_tag"].notna()])],
    }

    result = pd.DataFrame(stats)

    output_file = config.exports_dir / f"summary_stats_{run_date.isoformat()}.csv"
    result.to_csv(output_file, index=False)
    logger.info(f"Saved summary_stats to {output_file}")

    return output_file
