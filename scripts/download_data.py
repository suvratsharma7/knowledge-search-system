#!/usr/bin/env python3
"""
Download a sample corpus from Project Gutenberg and split each book into
~500-word chunks saved as individual .txt files in data/raw/.

Usage:
    python scripts/download_data.py

No external dependencies — stdlib only.
"""

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Project root (this file lives at <root>/scripts/download_data.py)
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"

MIN_FILES: int = 300          # skip download when this many files exist
WORDS_PER_CHUNK: int = 500    # target words per chunk
MAX_RETRIES: int = 3          # per-book download retries


# ---------------------------------------------------------------------------
# Book catalogue
# ---------------------------------------------------------------------------
class Book(NamedTuple):
    title: str
    slug: str
    url: str


BOOKS: list[Book] = [
    Book("Pride and Prejudice",   "pride_and_prejudice",
         "https://www.gutenberg.org/cache/epub/1342/pg1342.txt"),
    Book("Alice in Wonderland",   "alice_in_wonderland",
         "https://www.gutenberg.org/cache/epub/11/pg11.txt"),
    Book("Frankenstein",          "frankenstein",
         "https://www.gutenberg.org/cache/epub/84/pg84.txt"),
    Book("Sherlock Holmes",       "sherlock_holmes",
         "https://www.gutenberg.org/cache/epub/1661/pg1661.txt"),
    Book("A Tale of Two Cities",  "a_tale_of_two_cities",
         "https://www.gutenberg.org/cache/epub/98/pg98.txt"),
    Book("Moby Dick",            "moby_dick",
         "https://www.gutenberg.org/cache/epub/2701/pg2701.txt"),
    Book("The Yellow Wallpaper",  "the_yellow_wallpaper",
         "https://www.gutenberg.org/cache/epub/1952/pg1952.txt"),
    Book("Dorian Gray",          "dorian_gray",
         "https://www.gutenberg.org/cache/epub/174/pg174.txt"),
    Book("Huckleberry Finn",     "huckleberry_finn",
         "https://www.gutenberg.org/cache/epub/76/pg76.txt"),
    Book("A Christmas Carol",    "a_christmas_carol",
         "https://www.gutenberg.org/cache/epub/46/pg46.txt"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_text(url: str, retries: int = MAX_RETRIES) -> str:
    """Download *url* and return its text content, retrying on failure."""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "KerneySearchBot/0.1 (educational)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8-sig", errors="replace")
        except (urllib.error.URLError, OSError) as exc:
            print(f"  ⚠ Attempt {attempt}/{retries} failed: {exc}")
            if attempt < retries:
                time.sleep(2 * attempt)          # simple backoff
    raise RuntimeError(f"Failed to download {url} after {retries} attempts")


def strip_gutenberg_header_footer(text: str) -> str:
    """Remove the Project Gutenberg boilerplate header and footer."""
    # Header ends after a line like "*** START OF THE PROJECT GUTENBERG …"
    start_markers = ["*** START OF THE PROJECT GUTENBERG", "*** START OF THIS PROJECT GUTENBERG"]
    end_markers = ["*** END OF THE PROJECT GUTENBERG", "*** END OF THIS PROJECT GUTENBERG"]

    lines = text.splitlines(keepends=True)
    start_idx = 0
    end_idx = len(lines)

    for i, line in enumerate(lines):
        upper = line.upper()
        if any(m.upper() in upper for m in start_markers):
            start_idx = i + 1
            break

    for i in range(len(lines) - 1, -1, -1):
        upper = lines[i].upper()
        if any(m.upper() in upper for m in end_markers):
            end_idx = i
            break

    body = "".join(lines[start_idx:end_idx]).strip()
    # Normalise Windows-style line endings so paragraph splitting works.
    body = body.replace("\r\n", "\n")
    return body


def chunk_text(text: str, words_per_chunk: int = WORDS_PER_CHUNK) -> list[str]:
    """Split *text* into chunks of roughly *words_per_chunk* words.

    Splits on paragraph boundaries (double newlines) first, then groups
    paragraphs until the word target is reached.
    """
    paragraphs: list[str] = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_paragraphs: list[str] = []
    current_word_count: int = 0

    for para in paragraphs:
        para_words = len(para.split())
        current_paragraphs.append(para)
        current_word_count += para_words

        if current_word_count >= words_per_chunk:
            chunks.append("\n\n".join(current_paragraphs))
            current_paragraphs = []
            current_word_count = 0

    # Flush remaining paragraphs
    if current_paragraphs:
        # If the leftover is very short, merge with the last chunk
        if chunks and current_word_count < words_per_chunk // 4:
            chunks[-1] += "\n\n" + "\n\n".join(current_paragraphs)
        else:
            chunks.append("\n\n".join(current_paragraphs))

    return chunks


def save_chunks(
    book: Book,
    chunks: list[str],
    out_dir: Path,
) -> int:
    """Save each chunk as a numbered .txt file. Return number saved."""
    for idx, chunk_text_content in enumerate(chunks, start=1):
        title_line = f"Title: {book.title} — Part {idx}"
        filename = f"{book.slug}_{idx:03d}.txt"
        filepath = out_dir / filename
        filepath.write_text(f"{title_line}\n\n{chunk_text_content}", encoding="utf-8")
    return len(chunks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Early exit if we already have enough files
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    existing = list(DATA_RAW.glob("*.txt"))
    if len(existing) >= MIN_FILES:
        print(
            f"✔ data/raw/ already contains {len(existing)} files "
            f"(>= {MIN_FILES}). Skipping download."
        )
        return

    total_chunks = 0

    for i, book in enumerate(BOOKS, start=1):
        print(f"\n[{i}/{len(BOOKS)}] Downloading: {book.title}")
        print(f"    URL: {book.url}")

        try:
            raw = download_text(book.url)
        except RuntimeError as exc:
            print(f"  ✘ {exc} — skipping this book.")
            continue

        body = strip_gutenberg_header_footer(raw)
        chunks = chunk_text(body)
        saved = save_chunks(book, chunks, DATA_RAW)
        total_chunks += saved
        print(f"  ✔ {saved} chunks saved  (running total: {total_chunks})")

    print(f"\n{'═' * 50}")
    print(f"Done. {total_chunks} chunk files saved to {DATA_RAW.relative_to(PROJECT_ROOT)}/")
    if total_chunks < MIN_FILES:
        print(
            f"⚠ Only {total_chunks} chunks created (target was {MIN_FILES}+). "
            "Consider adding more books or lowering WORDS_PER_CHUNK."
        )


if __name__ == "__main__":
    main()
