"""Tests for backend.app.search.vector — VectorIndex.

All tests are marked ``@pytest.mark.slow`` because they load a real
sentence-transformer model.  Skip in CI with:  ``pytest -m 'not slow'``
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.search.vector import VectorIndex

# ---------------------------------------------------------------------------
# Toy corpus (same as BM25 tests)
# ---------------------------------------------------------------------------
DOC_IDS: list[str] = ["doc1", "doc2", "doc3", "doc4", "doc5"]
TEXTS: list[str] = [
    "the quick brown fox jumps over the lazy dog",
    "machine learning and artificial intelligence",
    "the fox is quick and brown",
    "deep learning neural networks for AI",
    "lazy dog sleeping in the sun",
]

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def built_index() -> VectorIndex:
    """Module-scoped fixture — builds the index once for all tests."""
    idx = VectorIndex()
    idx.build(DOC_IDS, TEXTS)
    return idx


# ── Build ────────────────────────────────────────────────────────────────────

class TestBuild:
    def test_build_creates_index(self, built_index: VectorIndex) -> None:
        assert built_index.is_built
        assert built_index.doc_count == 5
        assert built_index.dimension > 0


# ── Query ────────────────────────────────────────────────────────────────────

class TestQuery:
    def test_query_returns_results(self, built_index: VectorIndex) -> None:
        results = built_index.query("artificial intelligence")
        assert len(results) > 0
        # doc2 or doc4 should be ranked highest (both are AI-related)
        top_id = results[0]["doc_id"]
        assert top_id in ("doc2", "doc4")

    def test_result_has_required_keys(self, built_index: VectorIndex) -> None:
        results = built_index.query("artificial intelligence")
        for r in results:
            assert "doc_id" in r
            assert "score" in r
            assert isinstance(r["score"], float)

    def test_query_top_k(self, built_index: VectorIndex) -> None:
        results = built_index.query("fox", top_k=2)
        assert len(results) == 2


# ── get_all_scores ───────────────────────────────────────────────────────────

class TestGetAllScores:
    def test_get_all_scores(self, built_index: VectorIndex) -> None:
        scores = built_index.get_all_scores("fox")
        assert set(scores.keys()) == set(DOC_IDS)
        for v in scores.values():
            assert isinstance(v, float)


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_query(self, built_index: VectorIndex) -> None:
        assert built_index.query("") == []
        assert built_index.get_all_scores("") == {}

    def test_unbuilt_index(self) -> None:
        idx = VectorIndex()
        assert idx.query("fox") == []


# ── Save / Load ──────────────────────────────────────────────────────────────

class TestSaveLoad:
    def test_save_and_load(
        self, built_index: VectorIndex, tmp_path: Path
    ) -> None:
        built_index.save(tmp_path)
        loaded = VectorIndex.load(tmp_path)

        assert loaded.is_built
        assert loaded.doc_count == built_index.doc_count

        # Same query should return the same top result.
        original = built_index.query("artificial intelligence", top_k=3)
        restored = loaded.query("artificial intelligence", top_k=3)
        assert (
            [r["doc_id"] for r in original]
            == [r["doc_id"] for r in restored]
        )

    def test_load_dimension_validation(
        self, built_index: VectorIndex, tmp_path: Path
    ) -> None:
        built_index.save(tmp_path)

        # Tamper with metadata to simulate a dimension mismatch.
        meta_path = tmp_path / "metadata.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["dimension"] = 999
        meta_path.write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        with pytest.raises(ValueError, match="[Dd]imension"):
            VectorIndex.load(tmp_path)

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            VectorIndex.load(tmp_path / "nonexistent")
