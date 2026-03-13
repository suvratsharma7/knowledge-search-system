"""
Query-log viewing API router.

Prefix: ``/api/logs``
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from app.db.database import get_query_logs

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("/")
async def list_logs(
    limit: int = Query(default=50, ge=1, le=500),
    severity: Optional[str] = Query(default=None, pattern="^(error|info)$"),
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
) -> dict[str, list[dict[str, Any]]]:
    """Return query log entries, optionally filtered."""
    logs = get_query_logs(
        limit=limit,
        severity=severity,
        start_time=start_time,
        end_time=end_time,
    )
    return {"data": logs}
