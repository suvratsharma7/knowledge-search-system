"""
KPI (Key Performance Indicators) API router.

Prefix: ``/api/kpi``
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.db.database import get_kpi_data

router = APIRouter(prefix="/api/kpi", tags=["KPI"])


@router.get("/latency")
async def latency() -> dict[str, float]:
    """Return p50 and p95 search latency."""
    kpi = get_kpi_data()
    return {"p50": kpi["p50_latency"], "p95": kpi["p95_latency"]}


@router.get("/volume")
async def volume() -> dict[str, list[dict[str, Any]]]:
    """Return hourly query volume for the last 24 h."""
    kpi = get_kpi_data()
    data = [{"hour": h, "count": c} for h, c in kpi["volume_over_time"]]
    return {"data": data}


@router.get("/top-queries")
async def top_queries() -> dict[str, list[dict[str, Any]]]:
    """Return the 10 most frequent queries."""
    kpi = get_kpi_data()
    data = [{"query": q, "count": c} for q, c in kpi["top_queries"]]
    return {"data": data}


@router.get("/zero-results")
async def zero_results() -> dict[str, list[dict[str, Any]]]:
    """Return queries that produced zero results."""
    kpi = get_kpi_data()
    data = [{"query": q, "count": c} for q, c in kpi["zero_result_queries"]]
    return {"data": data}
