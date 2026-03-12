"""
Vector (semantic) search component for the Knowledge Search system.

Wraps `sentence-transformers <https://sbert.net>`_ and
`FAISS <https://github.com/facebookresearch/faiss>`_ to provide build /
query / persist operations on a dense vector index (cosine similarity via
inner product on L2-normalised vectors).

Designed for **CPU-only** environments (``faiss-cpu``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# File names used when persisting the index to disk.
# ---------------------------------------------------------------------------
_FAISS_FILENAME: str = "faiss.index"
_META_FILENAME: str = "metadata.json"


class VectorIndex:
    """Dense vector index backed by FAISS ``IndexFlatIP`` and a
    ``SentenceTransformer`` encoder.
    """

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name: str = model_name
        self._model: SentenceTransformer | None = None
        self._dimension: int = 0
        self._index: faiss.IndexFlatIP | None = None
        self._doc_ids: list[str] = []

    # Lazy-load the encoder on first use.
    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()  # type: ignore[assignment]
        return self._model

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, doc_ids: list[str], texts: list[str]) -> None:
        """Encode *texts*, L2-normalise, and build a FAISS inner-product index.

        Args:
            doc_ids: Unique identifier for each document.
            texts:   Plain-text content for each document (parallel to *doc_ids*).
        """
        if len(doc_ids) != len(texts):
            raise ValueError(
                f"doc_ids ({len(doc_ids)}) and texts ({len(texts)}) "
                "must have the same length."
            )

        model = self._get_model()
        embeddings: NDArray[np.float32] = model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True,
        )

        # L2-normalise so inner product == cosine similarity.
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        self._dimension = dim
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        self._doc_ids = list(doc_ids)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Return the *top_k* most similar documents to *query_text*.

        Each result is a dict with keys ``doc_id`` and ``score``.
        Returns an empty list when the query is empty or the index has not
        been built.
        """
        if not query_text.strip() or self._index is None:
            return []

        model = self._get_model()
        q_vec: NDArray[np.float32] = model.encode(
            [query_text], convert_to_numpy=True,
        )
        faiss.normalize_L2(q_vec)

        k = min(top_k, len(self._doc_ids))
        scores, indices = self._index.search(q_vec, k)

        return [
            {"doc_id": self._doc_ids[int(idx)], "score": float(scores[0][rank])}
            for rank, idx in enumerate(indices[0])
            if idx != -1
        ]

    def get_all_scores(self, query_text: str) -> dict[str, float]:
        """Return ``{doc_id: score}`` for **all** documents.

        Useful for hybrid score combining with the BM25 component.
        Returns an empty dict on empty query or unbuilt index.
        """
        if not query_text.strip() or self._index is None:
            return {}

        model = self._get_model()
        q_vec: NDArray[np.float32] = model.encode(
            [query_text], convert_to_numpy=True,
        )
        faiss.normalize_L2(q_vec)

        k = len(self._doc_ids)
        scores, indices = self._index.search(q_vec, k)

        return {
            self._doc_ids[int(idx)]: float(scores[0][rank])
            for rank, idx in enumerate(indices[0])
            if idx != -1
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _corpus_hash(doc_ids: list[str]) -> str:
        """First 8 hex chars of SHA-256 of sorted doc_ids joined by ``|``."""
        joined = "|".join(sorted(doc_ids))
        return hashlib.sha256(joined.encode()).hexdigest()[:8]

    def save(self, path: Path) -> None:
        """Save the FAISS index and metadata to *path*.

        Creates *path* (and parents) if it does not already exist.
        """
        if self._index is None:
            raise RuntimeError("Cannot save — index has not been built yet.")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(path / _FAISS_FILENAME))

        meta: dict[str, Any] = {
            "model_name": self._model_name,
            "dimension": self._dimension,
            "num_docs": len(self._doc_ids),
            "doc_ids": self._doc_ids,
            "build_timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "corpus_hash": self._corpus_hash(self._doc_ids),
        }
        (path / _META_FILENAME).write_text(
            json.dumps(meta, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "VectorIndex":
        """Load a previously saved index from *path*.

        Raises:
            FileNotFoundError: If the index files do not exist.
            ValueError:        If model name or dimension diverge from the
                               loaded metadata (index must be rebuilt).
        """
        path = Path(path)
        faiss_path = path / _FAISS_FILENAME
        meta_path = path / _META_FILENAME

        if not faiss_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {faiss_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata not found at {meta_path}")

        meta: dict[str, Any] = json.loads(
            meta_path.read_text(encoding="utf-8")
        )

        instance = cls(model_name=meta["model_name"])

        # Eagerly load the model so we can validate the dimension.
        model = instance._get_model()
        actual_dim: int = model.get_sentence_embedding_dimension()  # type: ignore[assignment]

        if meta["model_name"] != instance._model_name:
            raise ValueError(
                f"Model mismatch: index was built with {meta['model_name']!r} "
                f"but current model is {instance._model_name!r}. "
                "Please rebuild the index."
            )
        if meta["dimension"] != actual_dim:
            raise ValueError(
                f"Dimension mismatch: index has dimension {meta['dimension']} "
                f"but model produces {actual_dim}. Please rebuild the index."
            )

        instance._index = faiss.read_index(str(faiss_path))
        instance._doc_ids = meta["doc_ids"]
        instance._dimension = meta["dimension"]
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
        return self._index is not None

    @property
    def dimension(self) -> int:
        """Embedding dimension of the loaded / built index."""
        return self._dimension

    def __repr__(self) -> str:
        status = "built" if self.is_built else "empty"
        return (
            f"<VectorIndex {status}, model={self._model_name!r}, "
            f"{self.doc_count} docs, dim={self._dimension}>"
        )
