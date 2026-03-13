"""
SQLite database management for the Knowledge Search system.

Provides table creation, query/feedback logging, and KPI analytics.
No external dependencies — stdlib only.
"""

from __future__ import annotations

import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import DB_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_db_path() -> Path:
    """Return the configured database file path."""
    return DB_PATH


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a :class:`sqlite3.Connection` with ``Row`` factory and WAL mode.

    Ensures the parent directory exists before opening the database.
    """
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

_SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS query_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id   TEXT    NOT NULL,
    query        TEXT    NOT NULL,
    latency_ms   REAL    NOT NULL,
    top_k        INTEGER NOT NULL,
    alpha        REAL    NOT NULL,
    result_count INTEGER NOT NULL,
    error        TEXT,
    user_agent   TEXT    DEFAULT 'unknown',
    timestamp    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT    NOT NULL,
    doc_id     TEXT    NOT NULL,
    relevance  INTEGER NOT NULL,
    timestamp  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    """Create the SQLite database and all tables if they don't exist."""
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA_SQL)
        row = conn.execute("SELECT COUNT(*) AS cnt FROM schema_version").fetchone()
        if row["cnt"] == 0:
            conn.execute("INSERT INTO schema_version (version) VALUES (1)")
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log_query(
    request_id: str,
    query: str,
    latency_ms: float,
    top_k: int,
    alpha: float,
    result_count: int,
    error: Optional[str] = None,
    user_agent: str = "unknown",
) -> None:
    """Insert a row into ``query_logs``.
    
    Catches OperationalErrors to prevent API crashes if schema migrations
    or database locks are in progress.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO query_logs
                (request_id, query, latency_ms, top_k, alpha, result_count, error, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (request_id, query, latency_ms, top_k, alpha, result_count, error, user_agent),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        # Scenario B: Log warning instead of crashing the API response
        logger.warning(f"Database logging failed (OperationalError): {e}. Search result still returned to user.")
    except Exception as e:
        logger.error(f"Unexpected database error during log_query: {e}")
    finally:
        conn.close()


def log_feedback(query: str, doc_id: str, relevance: int) -> None:
    """Insert a row into ``feedback``."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO feedback (query, doc_id, relevance) VALUES (?, ?, ?)",
            (query, doc_id, relevance),
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to log feedback: {e}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_query_logs(
    limit: int = 100,
    offset: int = 0,
    severity: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if severity == "error":
        clauses.append("error IS NOT NULL")
    elif severity == "info":
        clauses.append("error IS NULL")

    if start_time is not None:
        clauses.append("timestamp >= ?")
        params.append(start_time)
    if end_time is not None:
        clauses.append("timestamp <= ?")
        params.append(end_time)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT * FROM query_logs
        {where}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# KPI analytics
# ---------------------------------------------------------------------------

def get_kpi_data() -> dict[str, Any]:
    conn = get_connection()
    try:
        total: int = conn.execute("SELECT COUNT(*) AS cnt FROM query_logs").fetchone()["cnt"]

        latency_rows = conn.execute("SELECT latency_ms FROM query_logs ORDER BY latency_ms").fetchall()
        latencies: list[float] = [r["latency_ms"] for r in latency_rows]

        p50 = _percentile(latencies, 50.0)
        p95 = _percentile(latencies, 95.0)

        top_q_rows = conn.execute(
            "SELECT query, COUNT(*) AS cnt FROM query_logs GROUP BY query ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        top_queries = [(r["query"], r["cnt"]) for r in top_q_rows]

        zero_rows = conn.execute(
            "SELECT query, COUNT(*) AS cnt FROM query_logs WHERE result_count = 0 GROUP BY query ORDER BY cnt DESC"
        ).fetchall()
        zero_result_queries = [(r["query"], r["cnt"]) for r in zero_rows]

        vol_rows = conn.execute(
            """
            SELECT strftime('%Y-%m-%d %H:00', timestamp) AS date_hour, COUNT(*) AS cnt
            FROM query_logs
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY date_hour ORDER BY date_hour
            """
        ).fetchall()
        volume_over_time = [(r["date_hour"], r["cnt"]) for r in vol_rows]

        return {
            "total_queries": total,
            "p50_latency": p50,
            "p95_latency": p95,
            "top_queries": top_queries,
            "zero_result_queries": zero_result_queries,
            "volume_over_time": volume_over_time,
        }
    finally:
        conn.close()


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    idx = (pct / 100.0) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])
