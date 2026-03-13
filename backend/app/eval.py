#!/usr/bin/env python3
"""
Evaluation harness for the Knowledge Search system.
Performs quantitative assessment of search quality using IR metrics.
"""

import argparse
import csv
import json
import math
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Path setup for imports
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import (
    BM25_INDEX_DIR,
    METRICS_DIR,
    PROJECT_ROOT,
    VECTOR_INDEX_DIR,
    EMBEDDING_MODEL,
    get_git_commit_hash,
)
from app.search.bm25 import BM25Index
from app.search.hybrid import HybridSearcher
from app.search.vector import VectorIndex

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_dcg(relevances: list[int]) -> float:
    """Compute Discounted Cumulative Gain (standard formula)."""
    dcg = 0.0
    for i, rel in enumerate(relevances):
        # Using the formula suggested by user: rel_i / log2(i+1)
        # Assuming rank i starts at 1, so log2(i+1) where i is 1-based.
        # Rank k = i + 1
        rank = i + 1
        dcg += rel / math.log2(rank + 1)
    return dcg

def compute_ndcg(results: list[str], qrels: dict[str, int], k: int = 10) -> float:
    """Compute Normalized Discounted Cumulative Gain at k."""
    # Actual DCG
    relevances = [qrels.get(doc_id, 0) for doc_id in results[:k]]
    actual_dcg = compute_dcg(relevances)
    
    # Ideal DCG (sort all known relevant qrels descending)
    ideal_relevances = sorted(qrels.values(), reverse=True)[:k]
    ideal_dcg = compute_dcg(ideal_relevances)
    
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg

def compute_recall(results: list[str], qrels: dict[str, int], k: int = 10) -> float:
    """Compute Recall at k (fraction of all relevant docs found in top k)."""
    relevant_in_qrels = [doc_id for doc_id, rel in qrels.items() if rel > 0]
    if not relevant_in_qrels:
        return 0.0
    
    retrieved_at_k = set(results[:k])
    found = sum(1 for doc_id in relevant_in_qrels if doc_id in retrieved_at_k)
    return found / len(relevant_in_qrels)

def compute_mrr(results: list[str], qrels: dict[str, int], k: int = 10) -> float:
    """Compute Mean Reciprocal Rank at k."""
    for i, doc_id in enumerate(results[:k]):
        if qrels.get(doc_id, 0) > 0:
            return 1.0 / (i + 1)
    return 0.0

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_evaluation(
    queries: list[dict[str, Any]],
    qrels: dict[str, dict[str, int]],
    searcher: HybridSearcher,
    alpha: float = 0.5,
    normalization: str = "minmax",
) -> dict[str, float]:
    """Execute evaluation across all queries and return average metrics."""
    total_ndcg = 0.0
    total_recall = 0.0
    total_mrr = 0.0
    count = 0

    print(f"{'Query ID':<10} | {'nDCG@10':<8} | {'Recall@10':<9} | {'MRR@10':<7}")
    print("-" * 45)

    for q_entry in queries:
        query_id = q_entry["query_id"]
        query_text = q_entry["query"]
        target_qrels = qrels.get(query_id, {})
        
        # Run search
        results = searcher.search(
            query=query_text,
            top_k=10,
            alpha=alpha,
            normalization=normalization,
        )
        ranked_doc_ids = [r["doc_id"] for r in results]
        
        # Compute metrics
        ndcg = compute_ndcg(ranked_doc_ids, target_qrels, k=10)
        recall = compute_recall(ranked_doc_ids, target_qrels, k=10)
        mrr = compute_mrr(ranked_doc_ids, target_qrels, k=10)
        
        total_ndcg += ndcg
        total_recall += recall
        total_mrr += mrr
        count += 1
        
        print(f"{query_id:<10} | {ndcg:<8.4f} | {recall:<9.4f} | {mrr:<7.4f}")

    if count == 0:
        return {"ndcg_10": 0.0, "recall_10": 0.0, "mrr_10": 0.0, "count": 0}

    return {
        "ndcg_10": total_ndcg / count,
        "recall_10": total_recall / count,
        "mrr_10": total_mrr / count,
        "count": count,
    }

def log_experiment(
    metrics: dict[str, float],
    alpha: float,
    normalization: str,
) -> None:
    """Append evaluation results to experiments.csv."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = METRICS_DIR / "experiments.csv"
    
    file_exists = csv_path.exists()
    
    headers = [
        "timestamp", "alpha", "normalization", "embedding_model",
        "ndcg_10", "recall_10", "mrr_10", "num_queries", "commit_hash"
    ]
    
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "alpha": alpha,
            "normalization": normalization,
            "embedding_model": EMBEDDING_MODEL,
            "ndcg_10": round(metrics["ndcg_10"], 4),
            "recall_10": round(metrics["recall_10"], 4),
            "mrr_10": round(metrics["mrr_10"], 4),
            "num_queries": int(metrics["count"]),
            "commit_hash": get_git_commit_hash(),
        })
    print(f"\n✔ Results logged to {csv_path}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge Search Evaluation Harness")
    parser.add_argument("--queries", type=Path, default=PROJECT_ROOT / "data" / "eval" / "queries.jsonl")
    parser.add_argument("--qrels", type=Path, default=PROJECT_ROOT / "data" / "eval" / "qrels.json")
    parser.add_argument("--alpha", type=float, default=0.5, help="Weight for BM25 (default 0.5)")
    parser.add_argument("--normalization", type=str, default="minmax", choices=["minmax", "zscore"])
    
    args = parser.parse_args()
    
    # 1. Load Evaluation Data
    if not args.queries.exists():
        print(f"✘ Queries file not found: {args.queries}")
        sys.exit(1)
    if not args.qrels.exists():
        print(f"✘ Qrels file not found: {args.qrels}")
        sys.exit(1)
        
    queries = []
    with open(args.queries, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
                
    with open(args.qrels, "r", encoding="utf-8") as f:
        qrels = json.load(f)
        
    print(f"Loaded {len(queries)} queries and {len(qrels)} qrels entries.")

    # 2. Load Searcher
    print("Loading search indexes...")
    try:
        bm25 = BM25Index.load(BM25_INDEX_DIR)
        vector = VectorIndex.load(VECTOR_INDEX_DIR)
        
        doc_store_path = PROJECT_ROOT / "data" / "index" / "doc_store.json"
        doc_store = {}
        if doc_store_path.exists():
            doc_store = json.loads(doc_store_path.read_text(encoding="utf-8"))
            
        searcher = HybridSearcher(bm25, vector, doc_store)
        print("✔ HybridSearcher ready.\n")
    except Exception as e:
        print(f"✘ Failed to load indexes: {e}")
        sys.exit(1)

    # 3. Run evaluation
    metrics = run_evaluation(
        queries=queries,
        qrels=qrels,
        searcher=searcher,
        alpha=args.alpha,
        normalization=args.normalization
    )

    # 4. Final results summary
    print("-" * 45)
    print(f"{'AVERAGES':<10} | {metrics['ndcg_10']:<8.4f} | {metrics['recall_10']:<9.4f} | {metrics['mrr_10']:<7.4f}")
    print("-" * 45)

    # 5. Log
    log_experiment(metrics, args.alpha, args.normalization)

if __name__ == "__main__":
    main()
