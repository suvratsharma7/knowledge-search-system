"""Tests for backend.app.db.database — SQLite database management.

Each test uses a temporary database via ``tmp_path`` so tests are fully
isolated from the real application database.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import backend.app.db.database as db_mod


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path: Path) -> None:
    """Patch DB_PATH to point to a temporary file before every test."""
    tmp_db = tmp_path / "test.db"
    with patch.object(db_mod, "DB_PATH", tmp_db):
        yield


# ── init_db ──────────────────────────────────────────────────────────────────

class TestInitDb:
    def test_init_db_creates_tables(self) -> None:
        db_mod.init_db()
        conn = db_mod.get_connection()
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "query_logs" in tables
        assert "feedback" in tables
        assert "schema_version" in tables

    def test_init_db_sets_schema_version(self) -> None:
        db_mod.init_db()
        conn = db_mod.get_connection()
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        conn.close()
        assert row["version"] == 1

    def test_init_db_idempotent(self) -> None:
        db_mod.init_db()
        db_mod.init_db()  # should not raise or duplicate version
        conn = db_mod.get_connection()
        count = conn.execute("SELECT COUNT(*) AS cnt FROM schema_version").fetchone()["cnt"]
        conn.close()
        assert count == 1


# ── log_query ────────────────────────────────────────────────────────────────

class TestLogQuery:
    def test_log_query(self) -> None:
        db_mod.init_db()
        db_mod.log_query(
            request_id="req-1",
            query="test query",
            latency_ms=12.5,
            top_k=10,
            alpha=0.5,
            result_count=3,
        )
        logs = db_mod.get_query_logs(limit=1)
        assert len(logs) == 1
        log = logs[0]
        assert log["request_id"] == "req-1"
        assert log["query"] == "test query"
        assert log["latency_ms"] == pytest.approx(12.5)
        assert log["top_k"] == 10
        assert log["alpha"] == pytest.approx(0.5)
        assert log["result_count"] == 3
        assert log["error"] is None
        assert log["timestamp"]  # non-empty


# ── log_feedback ─────────────────────────────────────────────────────────────

class TestLogFeedback:
    def test_log_feedback(self) -> None:
        db_mod.init_db()
        db_mod.log_feedback(query="fox", doc_id="d1", relevance=1)
        conn = db_mod.get_connection()
        row = conn.execute("SELECT * FROM feedback").fetchone()
        conn.close()
        assert row["query"] == "fox"
        assert row["doc_id"] == "d1"
        assert row["relevance"] == 1


# ── get_kpi_data ─────────────────────────────────────────────────────────────

class TestGetKpiData:
    def test_get_kpi_data(self) -> None:
        db_mod.init_db()
        # Insert 5 queries: 2 with zero results
        for i in range(1, 6):
            db_mod.log_query(
                request_id=f"r{i}",
                query="fox" if i <= 3 else "empty",
                latency_ms=float(i * 10),
                top_k=10,
                alpha=0.5,
                result_count=5 if i <= 3 else 0,
            )

        kpi = db_mod.get_kpi_data()
        assert kpi["total_queries"] == 5
        assert kpi["p50_latency"] > 0
        assert kpi["p95_latency"] >= kpi["p50_latency"]

        # top_queries should list "fox" with count 3
        top_q = dict(kpi["top_queries"])
        assert top_q["fox"] == 3

        # zero_result_queries should list "empty" with count 2
        zero_q = dict(kpi["zero_result_queries"])
        assert zero_q["empty"] == 2


# ── get_query_logs severity filter ───────────────────────────────────────────

class TestQueryLogsSeverity:
    def test_get_query_logs_severity_filter(self) -> None:
        db_mod.init_db()
        db_mod.log_query("r1", "ok query", 5.0, 10, 0.5, 3, error=None)
        db_mod.log_query("r2", "bad query", 8.0, 10, 0.5, 0, error="timeout")

        errors = db_mod.get_query_logs(severity="error")
        assert len(errors) == 1
        assert errors[0]["query"] == "bad query"
        assert errors[0]["error"] == "timeout"

        infos = db_mod.get_query_logs(severity="info")
        assert len(infos) == 1
        assert infos[0]["query"] == "ok query"
        assert infos[0]["error"] is None
