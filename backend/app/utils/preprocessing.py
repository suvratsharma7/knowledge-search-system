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
    """Clean *text* by removing control characters and collapsing whitespace.

    Steps:
    1. Remove null bytes and control characters (except newlines, which are
       kept temporarily so callers can split on them before this step).
    2. Collapse runs of whitespace / newlines into a single space.
    3. Strip leading and trailing whitespace.
    """
    # Remove null bytes and control chars (keep \n, \r, \t for now)
    cleaned = "".join(
        ch for ch in text
        if ch in ("\n", "\r", "\t")
        or not unicodedata.category(ch).startswith("C")
    )
    # Collapse all whitespace (including newlines) into a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def tokenize(text: str) -> list[str]:
    """Tokenize *text* into a list of lower-cased, non-stop-word tokens.

    Steps:
    1. Lower-case the text.
    2. Split on non-alphanumeric characters.
    3. Discard tokens shorter than 2 characters.
    4. Discard tokens present in :data:`STOP_WORDS`.
    """
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return [
        tok for tok in tokens
        if len(tok) >= 2 and tok not in STOP_WORDS
    ]


def truncate_text(text: str, max_chars: int = 50_000) -> str:
    """Return *text* truncated to *max_chars* with a ``[truncated]`` marker.

    If the text is already within the limit it is returned unchanged.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "[truncated]"


def extract_snippets(
    text: str,
    query_tokens: list[str],
    context_chars: int = 100,
) -> str:
    """Return a contextual snippet around the first matching query token.

    * The match is case-insensitive.
    * The matched token is wrapped in ``**bold**`` markers.
    * If no token is found, the first 200 characters of *text* are returned.
    """
    text_lower = text.lower()

    for token in query_tokens:
        idx = text_lower.find(token.lower())
        if idx == -1:
            continue

        # Determine snippet boundaries
        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(token) + context_chars)

        before = text[start:idx]
        matched = text[idx : idx + len(token)]
        after = text[idx + len(token) : end]

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""

        return f"{prefix}{before}**{matched}**{after}{suffix}"

    # No match — return the first 200 characters
    return text[:200]
