#!/usr/bin/env python3
"""
Data ingestion CLI for the Knowledge Search system.

Scans a directory of .txt / .md files, cleans and normalises each document,
and writes a consolidated JSONL file (one JSON object per line).

Usage (from project root):
    python -m backend.app.ingest --input data/raw --out data/processed

Usage (from backend/ directory):
    python -m app.ingest --input ../data/raw --out ../data/processed
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so both invocation styles work.
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent            # backend/app/
_BACKEND_DIR = _THIS_DIR.parent                        # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                    # project root

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import DATA_PROCESSED, DATA_RAW       # noqa: E402
from app.utils.preprocessing import clean_text, truncate_text  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_CHARS: int = 50          # skip files with < 50 chars after cleaning
EXTENSIONS: set[str] = {".txt", ".md"}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _extract_title(first_line: str, fallback: str) -> str:
    """Return the title from a ``Title: …`` line, or *fallback*."""
    stripped = first_line.strip()
    if stripped.lower().startswith("title:"):
        return stripped[len("title:"):].strip()
    return fallback


def _iso_mtime(path: Path) -> str:
    """Return the file's modification time as an ISO-8601 string (UTC)."""
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def ingest_directory(
    input_dir: Path,
    output_dir: Path,
) -> tuple[int, int, int]:
    """Ingest all .txt/.md files from *input_dir* into *output_dir*/docs.jsonl.

    Returns:
        (ingested_count, total_chars, skipped_count)
    """
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS
    )

    if not files:
        print(f"⚠ No .txt or .md files found in {input_dir}")
        return 0, 0, 0

    out_path: Path = output_dir / "docs.jsonl"
    ingested: int = 0
    skipped: int = 0
    total_chars: int = 0

    with out_path.open("w", encoding="utf-8") as fout:
        for filepath in files:
            raw = filepath.read_text(encoding="utf-8", errors="replace")
            lines = raw.split("\n", maxsplit=1)

            first_line = lines[0] if lines else ""
            body = lines[1] if len(lines) > 1 else ""

            # Derive title
            fallback_title = filepath.stem.replace("_", " ").title()
            title = _extract_title(first_line, fallback_title)

            # If first line wasn't a title header, include it in the body
            if not first_line.strip().lower().startswith("title:"):
                body = raw

            # Clean and truncate
            text = truncate_text(clean_text(body))

            if len(text) < MIN_CHARS:
                skipped += 1
                continue

            doc = {
                "doc_id": filepath.stem,
                "title": title,
                "text": text,
                "source": filepath.name,
                "created_at": _iso_mtime(filepath),
            }
            fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
            ingested += 1
            total_chars += len(text)

    return ingested, total_chars, skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest raw documents into a JSONL file for the Knowledge Search system.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_RAW,
        help=f"Input directory with .txt/.md files (default: {DATA_RAW})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DATA_PROCESSED,
        help=f"Output directory for docs.jsonl (default: {DATA_PROCESSED})",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    input_dir: Path = args.input
    output_dir: Path = args.out

    print(f"Input directory : {input_dir.resolve()}")
    print(f"Output directory: {output_dir.resolve()}")
    print()

    ingested, total_chars, skipped = ingest_directory(input_dir, output_dir)

    print()
    print("═" * 50)
    print(f"Documents ingested : {ingested}")
    print(f"Total characters   : {total_chars:,}")
    print(f"Skipped (too short): {skipped}")
    print(f"Output file        : {(output_dir / 'docs.jsonl').resolve()}")


if __name__ == "__main__":
    main()
