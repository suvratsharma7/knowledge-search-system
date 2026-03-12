"""
Hybrid search component for the Knowledge Search system.

Combines BM25 (lexical) and dense-vector (semantic) scores into a single
ranked result list using configurable weighting and normalization.
"""

from __future__ import annotations

from typing import Any

from app.search.bm25 import BM25Index
from app.search.normalizers import get_normalizer
from app.search.vector import VectorIndex
from app.utils.preprocessing import extract_snippets, tokenize


class HybridSearcher:
    """Merges :class:`BM25Index` and :class:`VectorIndex` results.

    Args:
        bm25_index:   A built BM25 index.
        vector_index: A built FAISS vector index.
        doc_store:    Mapping of ``doc_id`` → ``{"title": str, "text": str}``.
    """

    def __init__(
        self,
        bm25_index: BM25Index,
        vector_index: VectorIndex,
        doc_store: dict[str, dict[str, str]],
    ) -> None:
        self._bm25 = bm25_index
        self._vector = vector_index
        self._doc_store = doc_store

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        normalization: str = "minmax",
    ) -> list[dict[str, Any]]:
        """Run a hybrid search and return the top-*top_k* results.

        Args:
            query:         Free-text search query.
            top_k:         Number of results to return.
            alpha:         Weight for BM25 score (``1 - alpha`` for vector).
                           Must be in ``[0, 1]``.
            normalization: Normalization strategy (``"minmax"`` or ``"zscore"``).

        Returns:
            A list of result dicts, each containing ``doc_id``, ``title``,
            ``snippet``, raw and normalised scores, and the final
            ``hybrid_score``.

        Raises:
            ValueError: If *alpha* is outside ``[0, 1]``.
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(
                f"alpha must be in [0, 1], got {alpha}"
            )

        if not query.strip():
            return []

        # 1. Raw scores from both indexes.
        bm25_raw: dict[str, float] = self._bm25.get_all_scores(query)
        vector_raw: dict[str, float] = self._vector.get_all_scores(query)

        # 2. Normalise.
        normalize = get_normalizer(normalization)
        bm25_norm: dict[str, float] = normalize(bm25_raw)
        vector_norm: dict[str, float] = normalize(vector_raw)

        # 3. Combine — union of doc_ids from both indexes.
        all_doc_ids: set[str] = set(bm25_norm) | set(vector_norm)
        combined: list[tuple[str, float]] = []
        for doc_id in all_doc_ids:
            b = bm25_norm.get(doc_id, 0.0)
            v = vector_norm.get(doc_id, 0.0)
            hybrid = alpha * b + (1.0 - alpha) * v
            combined.append((doc_id, hybrid))

        # 4. Sort descending by hybrid score and take top-k.
        combined.sort(key=lambda x: x[1], reverse=True)
        top_results = combined[:top_k]

        # 5. Build rich result dicts.
        query_tokens: list[str] = tokenize(query)
        results: list[dict[str, Any]] = []
        for doc_id, hybrid_score in top_results:
            doc = self._doc_store.get(doc_id, {})
            title = doc.get("title", doc_id)
            text = doc.get("text", "")
            snippet = extract_snippets(text, query_tokens) if text else ""

            results.append({
                "doc_id": doc_id,
                "title": title,
                "snippet": snippet,
                "bm25_score": bm25_raw.get(doc_id, 0.0),
                "bm25_score_normalized": bm25_norm.get(doc_id, 0.0),
                "vector_score": vector_raw.get(doc_id, 0.0),
                "vector_score_normalized": vector_norm.get(doc_id, 0.0),
                "hybrid_score": hybrid_score,
            })

        return results

    def __repr__(self) -> str:
        return (
            f"<HybridSearcher bm25={self._bm25.doc_count} docs, "
            f"vector={self._vector.doc_count} docs, "
            f"store={len(self._doc_store)} docs>"
        )
