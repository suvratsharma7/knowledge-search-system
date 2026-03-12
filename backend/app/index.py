#!/usr/bin/env python3
"""
Indexing CLI for the Knowledge Search system.

Reads a JSONL document file, builds BM25 and FAISS vector indexes, and
persists everything to disk alongside a ``doc_store.json`` used by
:class:`HybridSearcher` for snippet generation.

Usage (from project root):
    python -m backend.app.index --input data/processed/docs.jsonl

Usage (from backend/ directory):
    python -m app.index --input ../data/processed/docs.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure imports work from both project root and backend/ directory.
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import (                               # noqa: E402
    BM25_INDEX_DIR,
    DATA_PROCESSED,
    VECTOR_INDEX_DIR,
)
from app.search.bm25 import BM25Index                  # noqa: E402
from app.search.vector import VectorIndex               # noqa: E402

# Optional: tqdm for progress bar
try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Index output directory  (parent of bm25 / vector dirs)
# ---------------------------------------------------------------------------
INDEX_DIR: Path = BM25_INDEX_DIR.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_docs(jsonl_path: Path) -> list[dict[str, Any]]:
    """Load every JSON object from *jsonl_path* (one per line)."""
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    iterator = tqdm(lines, desc="Loading documents", unit="doc") if tqdm else lines
    docs: list[dict[str, Any]] = []
    for line in iterator:
        line = line.strip()
        if line:
            docs.append(json.loads(line))
    return docs


def _build_content(doc: dict[str, Any]) -> str:
    """Concatenate title and text for indexing."""
    return f"{doc.get('title', '')} {doc.get('text', '')}".strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build BM25 and FAISS vector indexes from a docs.jsonl file.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_PROCESSED / "docs.jsonl",
        help="Path to the docs.jsonl file (default: data/processed/docs.jsonl)",
    )
    args = parser.parse_args()
    jsonl_path: Path = args.input.resolve() if args.input.is_absolute() else (Path.cwd() / args.input).resolve()

    if not jsonl_path.exists():
        print(f"✘ Input file not found: {jsonl_path}")
        sys.exit(1)

    print(f"Input file: {jsonl_path}")
    print()

    overall_start = time.perf_counter()

    # ── 1. Load documents ────────────────────────────────────────────
    docs = _load_docs(jsonl_path)
    doc_ids: list[str] = [d["doc_id"] for d in docs]
    contents: list[str] = [_build_content(d) for d in docs]
    print(f"Loaded {len(docs):,} documents.\n")

    # ── 2. Build BM25 index ──────────────────────────────────────────
    print("Building BM25 index…")
    t0 = time.perf_counter()
    bm25 = BM25Index()
    bm25.build(doc_ids, contents)
    bm25.save(BM25_INDEX_DIR)
    bm25_time = time.perf_counter() - t0
    print(f"  ✔ BM25 index built and saved ({bm25.doc_count:,} docs, {bm25_time:.2f}s)")
    print(f"    → {BM25_INDEX_DIR}\n")

    # ── 3. Build Vector index ────────────────────────────────────────
    print("Building Vector index…")
    t0 = time.perf_counter()
    vector = VectorIndex()
    vector.build(doc_ids, contents)
    vector.save(VECTOR_INDEX_DIR)
    vector_time = time.perf_counter() - t0
    print(f"  ✔ Vector index built and saved ({vector.doc_count:,} docs, {vector_time:.2f}s)")
    print(f"    → {VECTOR_INDEX_DIR}\n")

    # ── 4. Save doc_store.json ───────────────────────────────────────
    doc_store: dict[str, dict[str, str]] = {
        d["doc_id"]: {"title": d.get("title", ""), "text": d.get("text", "")}
        for d in docs
    }
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    doc_store_path = INDEX_DIR / "doc_store.json"
    doc_store_path.write_text(
        json.dumps(doc_store, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  ✔ doc_store.json saved ({len(doc_store):,} entries)")
    print(f"    → {doc_store_path}\n")

    # ── Summary ──────────────────────────────────────────────────────
    total_time = time.perf_counter() - overall_start
    print("═" * 50)
    print(f"Total indexing time: {total_time:.2f}s")
    print(f"  BM25  : {bm25_time:.2f}s")
    print(f"  Vector: {vector_time:.2f}s")
    print(f"  Docs  : {len(docs):,}")


if __name__ == "__main__":
    main()
