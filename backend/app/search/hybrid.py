"""
Hybrid search component for the Knowledge Search system.
"""

from __future__ import annotations
from typing import Any

from app.search.bm25 import BM25Index
from app.search.vector import VectorIndex
from app.utils.preprocessing import extract_snippets, tokenize

class HybridSearcher:
    def __init__(
        self,
        bm25_index: BM25Index,
        vector_index: VectorIndex,
        doc_store: dict[str, dict[str, str]],
    ) -> None:
        self._bm25 = bm25_index
        self._vector = vector_index
        self._doc_store = doc_store

    def _normalize_dict(self, d: dict[str, float]) -> dict[str, float]:
        """Internal helper to force scores into a 0.0 - 1.0 range."""
        if not d: return {}
        min_val = min(d.values())
        max_val = max(d.values())
        if max_val == min_val:
            return {k: 1.0 for k in d.keys()}
        return {k: (v - min_val) / (max_val - min_val) for k, v in d.items()}

    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        normalization: str = "minmax",
    ) -> list[dict[str, Any]]:
        if not query.strip(): return []

        # 1. Get RAW scores
        bm25_raw = self._bm25.get_all_scores(query)
        vector_raw = self._vector.get_all_scores(query)

        # 2. THE GIBBERISH GUARD (Strict 0.35)
        # We only consider semantic hits that are actually meaningful.
        valid_vector = {k: v for k, v in vector_raw.items() if v >= 0.35}

        if not bm25_raw and not valid_vector:
            return []

        # 3. INTERNAL MIN-MAX NORMALIZATION (The Fix)
        # We squash BM25 (0-20) and Vector (0-1) into a shared 0-1 scale.
        def normalize(scores):
            if not scores: return {}
            low, high = min(scores.values()), max(scores.values())
            if high == low: return {k: 1.0 for k in scores}
            return {k: (v - low) / (high - low) for k, v in scores.items()}

        b_norm = normalize(bm25_raw)
        v_norm = normalize(valid_vector)

        # 4. COMBINE (The Fair Handshake)
        all_ids = set(b_norm) | set(v_norm)
        combined = []
        for doc_id in all_ids:
            # Now Alpha 0.1 actually means 90% Vector power
            h_score = (alpha * b_norm.get(doc_id, 0)) + ((1 - alpha) * v_norm.get(doc_id, 0))
            if h_score > 0:
                combined.append((doc_id, h_score))

        combined.sort(key=lambda x: x[1], reverse=True)
        
        # 5. Build Result List
        results = []
        q_tokens = tokenize(query)
        for doc_id, final_score in combined[:top_k]:
            doc = self._doc_store.get(doc_id, {})
            results.append({
                "doc_id": doc_id,
                "title": doc.get("title", doc_id),
                "snippet": extract_snippets(doc.get("text", ""), q_tokens),
                "bm25_score": bm25_raw.get(doc_id, 0),
                "vector_score": vector_raw.get(doc_id, 0),
                "hybrid_score": final_score,
            })
        return results
    
    