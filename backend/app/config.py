import subprocess
from pathlib import Path

# Project root: two levels up from this file (backend/app/config.py → root)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

MODEL_NAME = "all-MiniLM-L6-v2"

# --- Data & Index Directories ---
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW: Path = DATA_DIR / "raw"
DATA_PROCESSED: Path = DATA_DIR / "processed"

# Consolidated Index Paths
DATA_INDEX: Path = DATA_DIR / "index" # Base index path
BM25_INDEX_DIR: Path = DATA_INDEX / "bm25"
VECTOR_INDEX_DIR: Path = DATA_INDEX / "vector"

# Evaluation, Metrics & DB
EVAL_DIR: Path = DATA_DIR / "eval"
METRICS_DIR: Path = DATA_DIR / "metrics"
DB_PATH: Path = DATA_DIR / "db" / "app.db"

# --- Model / search defaults ---
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2" # [cite: 386, 454]
EMBEDDING_DIM: int = 384                 # [cite: 386, 455]
DEFAULT_TOP_K: int = 10                  # [cite: 456]
DEFAULT_ALPHA: float = 0.5               # [cite: 457]
APP_VERSION: str = "0.1.0"               # [cite: 458]

def get_git_commit_hash() -> str:
    """Return the short git commit hash, or 'unknown' on failure."""
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
        return "unknown" # [cite: 460]