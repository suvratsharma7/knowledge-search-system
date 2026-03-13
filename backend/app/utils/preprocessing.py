"""
Text preprocessing utilities for the Knowledge Search system.

All functions are pure (no side effects), use only the standard library,
and are fully type-hinted.
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Stop words
# ---------------------------------------------------------------------------
STOP_WORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "it", "this", "that",
})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Clean *text* by removing control characters and collapsing whitespace."""
    cleaned = "".join(
        ch for ch in text
        if ch in ("\n", "\r", "\t")
        or not unicodedata.category(ch).startswith("C")
    )
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def tokenize(text: str) -> list[str]:
    """Tokenize *text* into a list of lower-cased, non-stop-word tokens."""
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return [
        tok for tok in tokens
        if len(tok) >= 2 and tok not in STOP_WORDS
    ]


def truncate_text(text: str, max_chars: int = 50_000) -> str:
    """Return *text* truncated to *max_chars* with a marker."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "[truncated]"


def extract_snippets(
    text: str,
    query_tokens: list[str],
    context_chars: int = 150,
) -> str:
    """
    Return a contextual snippet with ALL query tokens wrapped in **bold** markers.
    """
    if not text:
        return ""

    # 1. Handle No Query Case
    if not query_tokens:
        return text[:200] + "..." if len(text) > 200 else text

    # 2. Find the first occurrence to center the snippet
    text_lower = text.lower()
    first_idx = -1
    matched_token = ""
    
    for token in query_tokens:
        found_idx = text_lower.find(token.lower())
        if found_idx != -1 and (first_idx == -1 or found_idx < first_idx):
            first_idx = found_idx
            matched_token = token

    # If no match at all (e.g. vector only match), return start of text
    if first_idx == -1:
        return text[:200] + "..."

    # 3. Determine window boundaries around the first match
    start = max(0, first_idx - context_chars)
    end = min(len(text), first_idx + len(matched_token) + context_chars)
    
    raw_snippet = text[start:end]
    
    # 4. Apply Bolding to ALL query tokens within the window
    # Sort tokens by length descending to prevent partial matching bugs
    sorted_tokens = sorted(query_tokens, key=len, reverse=True)
    pattern = re.compile(f"({'|'.join(re.escape(t) for t in sorted_tokens)})", re.IGNORECASE)
    
    highlighted = pattern.sub(r"**\1**", raw_snippet)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{highlighted}{suffix}"