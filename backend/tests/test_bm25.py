"""Tests for backend.app.search.bm25 — BM25Index."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.search.bm25 import BM25Index

# ---------------------------------------------------------------------------
# Toy corpus
# ---------------------------------------------------------------------------
DOC_IDS: list[str] = ["doc1", "doc2", "doc3", "doc4", "doc5"]
TEXTS: list[str] = [
    "the quick brown fox jumps over the lazy dog",
    "machine learning and artificial intelligence",
    "the fox is quick and brown",
    "deep learning neural networks for AI",
    "lazy dog sleeping in the sun",
]


@pytest.fixture()
def built_index() -> BM25Index:
    """Return a BM25Index already built on the toy corpus."""
    idx = BM25Index()
    idx.build(DOC_IDS, TEXTS)
    return idx


# ── Build ────────────────────────────────────────────────────────────────────

class TestBuild:
    def test_build_creates_index(self, built_index: BM25Index) -> None:
        assert built_index.is_built
        assert built_index.doc_count == 5

    def test_build_does_not_raise(self) -> None:
        idx = BM25Index()
        idx.build(DOC_IDS, TEXTS)  # should complete without error


# ── Query ────────────────────────────────────────────────────────────────────

class TestQuery:
    def test_query_returns_ranked_results(self, built_index: BM25Index) -> None:
        results = built_index.query("quick fox")
        assert len(results) > 0
        # Top result should be doc1 or doc3 (both mention quick + fox)
        top_id = results[0]["doc_id"]
        assert top_id in ("doc1", "doc3")

    def test_result_has_required_keys(self, built_index: BM25Index) -> None:
        results = built_index.query("quick fox")
        for r in results:
            assert "doc_id" in r
            assert "score" in r
            assert isinstance(r["score"], float)

    def test_query_top_k_limits(self, built_index: BM25Index) -> None:
        results = built_index.query("quick fox", top_k=2)
        assert len(results) <= 2

    def test_scores_are_descending(self, built_index: BM25Index) -> None:
        results = built_index.query("learning", top_k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)


# ── get_all_scores ───────────────────────────────────────────────────────────

class TestGetAllScores:
    def test_get_all_scores_returns_all(self, built_index: BM25Index) -> None:
        scores = built_index.get_all_scores("fox")
        assert set(scores.keys()) == set(DOC_IDS)

    def test_all_scores_are_floats(self, built_index: BM25Index) -> None:
        scores = built_index.get_all_scores("fox")
        for v in scores.values():
            assert isinstance(v, float)


# ── Empty / edge-case queries ────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_query_returns_empty_list(self, built_index: BM25Index) -> None:
        assert built_index.query("") == []

    def test_whitespace_query_returns_empty_list(self, built_index: BM25Index) -> None:
        assert built_index.query("   ") == []

    def test_unbuilt_index_returns_empty(self) -> None:
        idx = BM25Index()
        assert idx.query("fox") == []
        assert idx.get_all_scores("fox") == {}


# ── Save / Load ──────────────────────────────────────────────────────────────

class TestSaveLoad:
    def test_save_and_load(
        self, built_index: BM25Index, tmp_path: Path
    ) -> None:
        built_index.save(tmp_path)
        loaded = BM25Index.load(tmp_path)

        assert loaded.is_built
        assert loaded.doc_count == built_index.doc_count

        # Same query should give identical results
        original = built_index.query("quick fox", top_k=3)
        restored = loaded.query("quick fox", top_k=3)
        assert [r["doc_id"] for r in original] == [r["doc_id"] for r in restored]

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            BM25Index.load(tmp_path / "nonexistent")
