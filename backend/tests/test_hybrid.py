"""Tests for backend.app.search.hybrid — HybridSearcher.

Uses mocks to avoid loading real sentence-transformer models.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.search.hybrid import HybridSearcher

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
BM25_SCORES: dict[str, float] = {"doc1": 5.0, "doc2": 1.0, "doc3": 3.0}
VECTOR_SCORES: dict[str, float] = {"doc1": 0.3, "doc2": 0.9, "doc3": 0.6}

DOC_STORE: dict[str, dict[str, str]] = {
    "doc1": {"title": "Doc 1", "text": "some text about foxes"},
    "doc2": {"title": "Doc 2", "text": "machine learning AI"},
    "doc3": {"title": "Doc 3", "text": "fox and dog"},
}

REQUIRED_KEYS: set[str] = {
    "doc_id", "title", "snippet",
    "bm25_score", "bm25_score_normalized",
    "vector_score", "vector_score_normalized",
    "hybrid_score",
}


@pytest.fixture()
def searcher() -> HybridSearcher:
    """HybridSearcher wired to mocked BM25 and Vector indexes."""
    bm25_mock = MagicMock()
    bm25_mock.get_all_scores.return_value = BM25_SCORES
    bm25_mock.doc_count = 3

    vector_mock = MagicMock()
    vector_mock.get_all_scores.return_value = VECTOR_SCORES
    vector_mock.doc_count = 3

    return HybridSearcher(bm25_mock, vector_mock, DOC_STORE)


# ── Alpha extremes ───────────────────────────────────────────────────────────

class TestAlphaExtremes:
    def test_hybrid_alpha_1_is_pure_bm25(self, searcher: HybridSearcher) -> None:
        results = searcher.search("fox", alpha=1.0)
        ids = [r["doc_id"] for r in results]
        # BM25 order: doc1 (5.0) > doc3 (3.0) > doc2 (1.0)
        assert ids == ["doc1", "doc3", "doc2"]

    def test_hybrid_alpha_0_is_pure_vector(self, searcher: HybridSearcher) -> None:
        results = searcher.search("fox", alpha=0.0)
        ids = [r["doc_id"] for r in results]
        # Vector order: doc2 (0.9) > doc3 (0.6) > doc1 (0.3)
        assert ids == ["doc2", "doc3", "doc1"]


# ── Balanced ─────────────────────────────────────────────────────────────────

class TestBalanced:
    def test_hybrid_balanced(self, searcher: HybridSearcher) -> None:
        results = searcher.search("fox", alpha=0.5)
        for r in results:
            # hybrid = 0.5 * norm_bm25 + 0.5 * norm_vector
            expected = (
                0.5 * r["bm25_score_normalized"]
                + 0.5 * r["vector_score_normalized"]
            )
            assert r["hybrid_score"] == pytest.approx(expected, abs=1e-9)


# ── Result shape ─────────────────────────────────────────────────────────────

class TestResultShape:
    def test_hybrid_returns_all_fields(self, searcher: HybridSearcher) -> None:
        results = searcher.search("fox")
        assert len(results) > 0
        for r in results:
            assert REQUIRED_KEYS.issubset(r.keys())

    def test_hybrid_top_k_limits(self, searcher: HybridSearcher) -> None:
        results = searcher.search("fox", top_k=2)
        assert len(results) == 2


# ── Validation ───────────────────────────────────────────────────────────────

class TestValidation:
    def test_hybrid_invalid_alpha_negative(self, searcher: HybridSearcher) -> None:
        with pytest.raises(ValueError, match="alpha"):
            searcher.search("fox", alpha=-0.1)

    def test_hybrid_invalid_alpha_above_one(self, searcher: HybridSearcher) -> None:
        with pytest.raises(ValueError, match="alpha"):
            searcher.search("fox", alpha=1.5)

    def test_empty_query_returns_empty(self, searcher: HybridSearcher) -> None:
        assert searcher.search("") == []
