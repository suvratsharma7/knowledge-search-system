"""
BM25 search component for the Knowledge Search system.

Wraps :pypi:`rank_bm25` to provide build / query / persist operations on a
BM25Okapi index, using the project's own tokenizer.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from app.utils.preprocessing import tokenize

# ---------------------------------------------------------------------------
# File name used when persisting the index to disk.
# ---------------------------------------------------------------------------
_INDEX_FILENAME: str = "bm25_index.pkl"


class BM25Index:
    """In-memory BM25 index backed by :class:`rank_bm25.BM25Okapi`."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._doc_ids: list[str] = []
        self._corpus: list[list[str]] = []

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, doc_ids: list[str], texts: list[str]) -> None:
        """Build the BM25 index from parallel lists of *doc_ids* and *texts*.

        Each text is tokenized via :func:`app.utils.preprocessing.tokenize`
        before being fed to ``BM25Okapi``.
        """
        if len(doc_ids) != len(texts):
            raise ValueError(
                f"doc_ids ({len(doc_ids)}) and texts ({len(texts)}) "
                "must have the same length."
            )
        self._doc_ids = list(doc_ids)
        self._corpus = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(self._corpus)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Return the *top_k* most relevant documents for *query_text*.

        Each result is a dict with keys ``doc_id`` and ``score``.
        Returns an empty list when the query is empty or the index has not
        been built.
        """
        if not query_text.strip() or self._bm25 is None:
            return []

        query_tokens: list[str] = tokenize(query_text)
        if not query_tokens:
            return []

        scores: np.ndarray = self._bm25.get_scores(query_tokens)

        # Indices of top-k scores in descending order
        k = min(top_k, len(self._doc_ids))
        top_indices: np.ndarray = np.argsort(scores)[::-1][:k]

        return [
            {"doc_id": self._doc_ids[i], "score": float(scores[i])}
            for i in top_indices
            if scores[i] > 0.0
        ]

    def get_all_scores(self, query_text: str) -> dict[str, float]:
        """Return ``{doc_id: score}`` for **all** documents.

        Useful for hybrid score combining with a vector search component.
        Returns an empty dict on empty query or unbuilt index.
        """
        if not query_text.strip() or self._bm25 is None:
            return {}

        query_tokens: list[str] = tokenize(query_text)
        if not query_tokens:
            return {}

        scores: np.ndarray = self._bm25.get_scores(query_tokens)
        return {
            doc_id: float(score)
            for doc_id, score in zip(self._doc_ids, scores)
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Pickle the index to *path*/*bm25_index.pkl*."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        payload = {
            "bm25": self._bm25,
            "doc_ids": self._doc_ids,
            "corpus": self._corpus,
        }
        with (path / _INDEX_FILENAME).open("wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        """Load a previously saved index from *path*/*bm25_index.pkl*.

        Raises:
            FileNotFoundError: If the pickle file does not exist.
        """
        pkl_path = Path(path) / _INDEX_FILENAME
        if not pkl_path.exists():
            raise FileNotFoundError(f"BM25 index not found at {pkl_path}")

        with pkl_path.open("rb") as f:
            payload: dict[str, Any] = pickle.load(f)  # noqa: S301

        instance = cls()
        instance._bm25 = payload["bm25"]
        instance._doc_ids = payload["doc_ids"]
        instance._corpus = payload.get("corpus", [])
        return instance

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def doc_count(self) -> int:
        """Number of documents in the index."""
        return len(self._doc_ids)

    @property
    def is_built(self) -> bool:
        """Whether :meth:`build` has been called."""
        return self._bm25 is not None

    def __repr__(self) -> str:
        status = "built" if self.is_built else "empty"
        return f"<BM25Index {status}, {self.doc_count} docs>"
