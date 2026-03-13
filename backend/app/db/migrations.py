"""
Simple schema migration system for the Knowledge Search database.

Migrations are defined as a dict mapping version numbers to SQL statements.
Version 1 is the initial schema created by :func:`database.init_db`.
"""

from __future__ import annotations

import sqlite3
import logging
# Add Row for dictionary-style access
from sqlite3 import Row
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Migration registry — version → SQL
# ---------------------------------------------------------------------------
MIGRATIONS: dict[int, str] = {
    2: "ALTER TABLE query_logs ADD COLUMN normalization TEXT DEFAULT 'minmax';",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_current_version(conn: sqlite3.Connection) -> int:
    """Return the highest version in ``schema_version``, or ``0``."""
    try:
        row = conn.execute(
            "SELECT MAX(version) AS v FROM schema_version"
        ).fetchone()
        version: Any = row["v"] if row else None
        return int(version) if version is not None else 0
    except sqlite3.OperationalError:
        return 0


def run_migrations(db_path_or_conn: str | sqlite3.Connection) -> None:
    """Apply pending migrations and perform self-healing for schema drift.
    
    Now accepts either a string path or a connection object to be flexible.
    """
    if isinstance(db_path_or_conn, str):
        conn = sqlite3.connect(db_path_or_conn)
    else:
        conn = db_path_or_conn

    # CRITICAL FIX: Set row_factory so get_current_version can use row["v"]
    conn.row_factory = Row

    try:
        # 1. Handle Standard Registry Migrations
        current = get_current_version(conn)
        pending = sorted(v for v in MIGRATIONS if v > current)
        
        for version in pending:
            sql = MIGRATIONS[version]
            print(f"  Applying migration v{version}: {sql[:60]}…")
            conn.executescript(sql)
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
            print(f"  ✔ Migration v{version} applied.")

        # 2. Break-Fix B: Self-Healing for 'user_agent' column
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(query_logs)")
        columns = [column[1] for column in cursor.fetchall()]

        if columns and "user_agent" not in columns:
            print("🛠️  Self-Healing: Repairing query_logs schema (adding user_agent)...")
            conn.executescript("""
                BEGIN TRANSACTION;
                CREATE TABLE query_logs_new (
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
                
                INSERT INTO query_logs_new (id, request_id, query, latency_ms, top_k, alpha, result_count, error)
                SELECT id, request_id, query, latency_ms, top_k, alpha, result_count, error FROM query_logs;
                
                DROP TABLE query_logs;
                ALTER TABLE query_logs_new RENAME TO query_logs;
                COMMIT;
            """)
            print("✅  Schema repaired successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌  Migration/Self-healing failed: {e}")
        raise e
    finally:
        if isinstance(db_path_or_conn, str):
            conn.close()

