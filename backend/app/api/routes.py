from typing import Literal
from fastapi import APIRouter, HTTPException, Request, Response
import time
from pydantic import BaseModel, Field
from app.db.database import log_query, log_feedback, get_kpi_data
from app.config import APP_VERSION, get_git_commit_hash

router = APIRouter()

# --- 1. Pydantic Models ---

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=100)
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    # This Literal is what forces the 422 error
    normalization: Literal["minmax", "rank", "none"] = "minmax"

class FeedbackRequest(BaseModel):
    query: str
    doc_id: str
    relevance: int  # e.g., 1 for relevant, 0 for not relevant

# --- 2. Endpoints ---

@router.get("/health")
async def health():
    """Liveness probe for monitoring systems."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "commit": get_git_commit_hash()
    }

@router.post("/search")
async def search(body: SearchRequest, request: Request):
    """
    Performs a hybrid search using BM25 and Vector indices.
    Results are fused and logged to the telemetry database.
    """
    searcher = getattr(request.app.state, "searcher", None)
    if not searcher:
        raise HTTPException(
            status_code=503, 
            detail="Search engine not initialized. Check server logs for startup errors."
        )

    # request_id is injected by our RequestLoggingMiddleware
    request_id = getattr(request.state, "request_id", "unknown")
    t0 = time.perf_counter()
    
    try:
        # Execute the search logic from the HybridSearcher class
        results = searcher.search(
            query=body.query, 
            top_k=body.top_k, 
            alpha=body.alpha,
            normalization=body.normalization
        )
        
        latency_ms = (time.perf_counter() - t0) * 1000
        
        # Log this query event to our SQLite telemetry table
        log_query(
            request_id=request_id,
            query=body.query,
            latency_ms=latency_ms,
            top_k=body.top_k,
            alpha=body.alpha,
            result_count=len(results)
        )
        
        return {
            "request_id": request_id,
            "results": results, 
            "latency_ms": round(latency_ms, 2),
            "query": body.query,
            "alpha": body.alpha
        }
        
    except Exception as e:
        # Log error to console and return a 500
        print(f"ERROR during search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failure: {str(e)}")

@router.post("/feedback")
async def feedback(body: FeedbackRequest):
    """
    Stores user relevance feedback for a specific document.
    Useful for future evaluation and fine-tuning.
    """
    try:
        log_feedback(query=body.query, doc_id=body.doc_id, relevance=body.relevance)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback log failed: {str(e)}")

@router.get("/metrics")
async def metrics():
    """
    Returns Prometheus-style text metrics for observability.
    """
    try:
        kpi = get_kpi_data()
        lines = [
            f"search_requests_total {kpi['total_queries']}",
            f"search_latency_p50 {kpi['p50_latency']:.2f}",
            f"search_latency_p95 {kpi['p95_latency']:.2f}",
        ]
        return Response(content="\n".join(lines) + "\n", media_type="text/plain")
    except Exception as e:
        return Response(content=f"# Error fetching metrics: {e}", media_type="text/plain", status_code=500)