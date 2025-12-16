"""Configuration management for jobintel."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Global configuration for jobintel pipeline."""

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")

    # Data subdirectories
    seeds_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "seeds")
    raw_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "raw")
    staged_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "staged")
    exports_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "exports")

    # HTTP settings
    http_timeout: int = 30
    http_max_retries: int = 3
    http_backoff_factor: float = 2.0
    rate_limit_delay: float = 1.0

    # Pipeline settings
    batch_size: int = 100
    max_workers: int = 4

    # US-only filtering
    strict_us_only: bool = True
    exclude_ambiguous: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.seeds_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.staged_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
