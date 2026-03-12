"""
Simple schema migration system for the Knowledge Search database.

Migrations are defined as a dict mapping version numbers to SQL statements.
Version 1 is the initial schema created by :func:`database.init_db`.
"""

from __future__ import annotations

import sqlite3
from typing import Any


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
    """Return the highest version in ``schema_version``, or ``0`` if the
    table does not exist yet (very first run).
    """
    try:
        row = conn.execute(
            "SELECT MAX(version) AS v FROM schema_version"
        ).fetchone()
        version: Any = row["v"] if row else None
        return int(version) if version is not None else 0
    except sqlite3.OperationalError:
        # Table doesn't exist yet — treat as version 0.
        return 0


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations whose version exceeds the current one.

    After each migration, a new row is inserted into ``schema_version``
    and a message is printed to stdout.
    """
    current = get_current_version(conn)

    pending = sorted(v for v in MIGRATIONS if v > current)
    if not pending:
        return

    for version in pending:
        sql = MIGRATIONS[version]
        print(f"  Applying migration v{version}: {sql[:60]}…")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (version,),
        )
        conn.commit()
        print(f"  ✔ Migration v{version} applied.")
