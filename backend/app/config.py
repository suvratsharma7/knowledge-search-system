"""
Application configuration for the Knowledge Search system.

All paths are defined relative to the auto-detected PROJECT_ROOT.
"""

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root: two levels up from this file  (backend/app/config.py → root)
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Data directories
# ---------------------------------------------------------------------------
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"

# Index directories
BM25_INDEX_DIR: Path = PROJECT_ROOT / "data" / "index" / "bm25"
VECTOR_INDEX_DIR: Path = PROJECT_ROOT / "data" / "index" / "vector"

# Evaluation & metrics
EVAL_DIR: Path = PROJECT_ROOT / "data" / "eval"
METRICS_DIR: Path = PROJECT_ROOT / "data" / "metrics"

# Database
DB_PATH: Path = PROJECT_ROOT / "data" / "db" / "app.db"

# ---------------------------------------------------------------------------
# Model / search defaults
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384
DEFAULT_TOP_K: int = 10
DEFAULT_ALPHA: float = 0.5

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_VERSION: str = "0.1.0"


def get_git_commit_hash() -> str:
    """Return the short git commit hash, or ``'unknown'`` on failure."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(PROJECT_ROOT),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"
