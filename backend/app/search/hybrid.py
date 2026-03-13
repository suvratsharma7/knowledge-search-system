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
    """Merges :class:`BM25Index` and :class:`VectorIndex` results."""

    def __init__(
        self,
        bm25_index: BM25Index,
        vector_index: VectorIndex,
        doc_store: dict[str, dict[str, str]],
    ) -> None:
        self._bm25 = bm25_index
        self._vector = vector_index
        self._doc_store = doc_store

    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        normalization: str = "minmax",
    ) -> list[dict[str, Any]]:
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be in [0, 1], got {alpha}")

        if not query.strip():
            return []

        # 1. Get RAW scores
        bm25_raw: dict[str, float] = self._bm25.get_all_scores(query)
        vector_raw: dict[str, float] = self._vector.get_all_scores(query)

        # --- THE FIX: COSINE SIMILARITY THRESHOLDING ---
        # Your debug output showed distances around 0.21. 
        # In Cosine Similarity, we want values GREATER than a threshold.
        # Anything below 0.45 is usually semantically unrelated noise.
        valid_vector_raw = {
            doc_id: sim for doc_id, sim in vector_raw.items() if sim > 0.45
        }

        # If BM25 found nothing AND Vector similarity is too low, return empty.
        if not bm25_raw and not valid_vector_raw:
            return []
        # ----------------------------------------------

        # 2. Normalise only the valid data
        normalize = get_normalizer(normalization)
        bm25_norm: dict[str, float] = normalize(bm25_raw)
        vector_norm: dict[str, float] = normalize(valid_vector_raw)

        # 3. Combine scores
        all_doc_ids: set[str] = set(bm25_norm) | set(vector_norm)
        combined: list[tuple[str, float]] = []
        for doc_id in all_doc_ids:
            b = bm25_norm.get(doc_id, 0.0)
            v = vector_norm.get(doc_id, 0.0)
            hybrid = alpha * b + (1.0 - alpha) * v
            
            # Baseline hybrid check to ensure quality
            if hybrid >= 0.05:
                combined.append((doc_id, hybrid))

        # 4. Sort and slice
        combined.sort(key=lambda x: x[1], reverse=True)
        top_results = combined[:top_k]

        # 5. Build rich results
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
                "vector_score": vector_raw.get(doc_id, 0.0),
                "hybrid_score": hybrid_score,
            })

        # --- DEBUG OUTPUT ---
        print(f"--- DEBUG SEARCH ---")
        print(f"Query: {query}")
        print(f"Raw Vector Distances (Top 3): {list(vector_raw.values())[:3]}")
        print(f"Results after threshold: {len(results)}")

        return results

    def __repr__(self) -> str:
        return (
            f"<HybridSearcher bm25={self._bm25.doc_count} docs, "
            f"vector={self._vector.doc_count} docs, "
            f"store={len(self._doc_store)} docs>"
        )
