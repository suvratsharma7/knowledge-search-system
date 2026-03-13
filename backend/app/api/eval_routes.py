"""
Evaluation experiments API router.

Prefix: ``/api/eval``
"""

from __future__ import annotations

import csv
from typing import Any

from fastapi import APIRouter

from app.config import METRICS_DIR

router = APIRouter(prefix="/api/eval", tags=["Evaluation"])

_EXPERIMENTS_FILE = METRICS_DIR / "experiments.csv"


@router.get("/experiments")
async def experiments() -> dict[str, list[dict[str, Any]]]:
    """Return evaluation experiments from ``experiments.csv`` as JSON.

    Returns ``{"data": []}`` if the file does not exist.
    """
    if not _EXPERIMENTS_FILE.exists():
        return {"data": []}

    rows: list[dict[str, Any]] = []
    with _EXPERIMENTS_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Coerce numeric fields where possible
            cleaned: dict[str, Any] = {}
            for key, value in row.items():
                try:
                    cleaned[key] = float(value)
                except (ValueError, TypeError):
                    cleaned[key] = value
            rows.append(cleaned)

    return {"data": rows}
