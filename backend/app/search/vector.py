"""
Vector (semantic) search component for the Knowledge Search system.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

# Import the project configuration for validation
from app.config import MODEL_NAME

# ---------------------------------------------------------------------------
# File names used when persisting the index to disk.
# ---------------------------------------------------------------------------
_FAISS_FILENAME: str = "faiss.index"
_META_FILENAME: str = "metadata.json"


class VectorIndex:
    """Dense vector index backed by FAISS ``IndexFlatIP`` and a
    ``SentenceTransformer`` encoder.
    """

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name: str = model_name
        self._model: SentenceTransformer | None = None
        self._dimension: int = 0
        self._index: faiss.IndexFlatIP | None = None
        self._doc_ids: list[str] = []

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()  # type: ignore[assignment]
        return self._model

    def build(self, doc_ids: list[str], texts: list[str]) -> None:
        if len(doc_ids) != len(texts):
            raise ValueError(f"doc_ids ({len(doc_ids)}) and texts ({len(texts)}) must match.")

        model = self._get_model()
        embeddings: NDArray[np.float32] = model.encode(
            texts, show_progress_bar=True, batch_size=32, convert_to_numpy=True,
        )

        faiss.normalize_L2(embeddings)
        self._dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(self._dimension)
        self._index.add(embeddings)
        self._doc_ids = list(doc_ids)

    def query(self, query_text: str, top_k: int = 10) -> list[dict[str, Any]]:
        if not query_text.strip() or self._index is None:
            return []

        model = self._get_model()
        q_vec: NDArray[np.float32] = model.encode([query_text], convert_to_numpy=True)
        faiss.normalize_L2(q_vec)

        k = min(top_k, len(self._doc_ids))
        scores, indices = self._index.search(q_vec, k)

        return [
            {"doc_id": self._doc_ids[int(idx)], "score": float(scores[0][rank])}
            for rank, idx in enumerate(indices[0]) if idx != -1
        ]

    def get_all_scores(self, query_text: str) -> dict[str, float]:
        if not query_text.strip() or self._index is None:
            return {}

        model = self._get_model()
        q_vec: NDArray[np.float32] = model.encode([query_text], convert_to_numpy=True)
        faiss.normalize_L2(q_vec)

        k = len(self._doc_ids)
        scores, indices = self._index.search(q_vec, k)

        return {
            self._doc_ids[int(idx)]: float(scores[0][rank])
            for rank, idx in enumerate(indices[0]) if idx != -1
        }

    @staticmethod
    def _corpus_hash(doc_ids: list[str]) -> str:
        joined = "|".join(sorted(doc_ids))
        return hashlib.sha256(joined.encode()).hexdigest()[:8]

    def save(self, path: Path) -> None:
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
        (path / _META_FILENAME).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "VectorIndex":
        """Load a previously saved index with strict config validation."""
        path = Path(path)
        faiss_path = path / _FAISS_FILENAME
        meta_path = path / _META_FILENAME

        if not faiss_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Index files missing at {path}")

        meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))

        # --- VALIDATION AGAINST APP CONFIG ---
        instance = cls(model_name=MODEL_NAME) # Use the APP config, NOT the metadata
        model = instance._get_model()
        expected_dim = model.get_sentence_embedding_dimension()

        if meta["model_name"] != MODEL_NAME:
            raise ValueError(
                f"Index mismatch: index was built with model={meta['model_name']!r} "
                f"(dim={meta['dimension']}) but config expects model={MODEL_NAME!r} (dim={expected_dim}).\n"
                f"Please rebuild: python -m app.index --input data/processed/docs.jsonl"
            )
            
        if meta["dimension"] != expected_dim:
            raise ValueError(
                f"Dimension mismatch: index has dimension {meta['dimension']} "
                f"but model {MODEL_NAME} produces {expected_dim}. Please rebuild index."
            )

        instance._index = faiss.read_index(str(faiss_path))
        instance._doc_ids = meta["doc_ids"]
        instance._dimension = meta["dimension"]
        return instance

    @property
    def doc_count(self) -> int:
        return len(self._doc_ids)

    @property
    def is_built(self) -> bool:
        return self._index is not None

    @property
    def dimension(self) -> int:
        return self._dimension

    def __repr__(self) -> str:
        status = "built" if self.is_built else "empty"
        return f"<VectorIndex {status}, model={self._model_name!r}, {self.doc_count} docs, dim={self._dimension}>"