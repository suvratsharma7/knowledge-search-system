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
async def experiments() -> list[dict[str, Any]]:
    # 1. Print the absolute path to your terminal to verify it
    print(f"DEBUG: Looking for CSV at: {_EXPERIMENTS_FILE.absolute()}")
    
    if not _EXPERIMENTS_FILE.exists():
        print("DEBUG: File NOT found!")
        return []

    rows = []
    with _EXPERIMENTS_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {}
            for key, value in row.items():
                try:
                    cleaned[key] = float(value)
                except (ValueError, TypeError):
                    cleaned[key] = value
            rows.append(cleaned)
    
    print(f"DEBUG: Found {len(rows)} experiments.")
    return rows

    return rows

