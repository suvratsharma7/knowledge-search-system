"""
Score normalization strategies for the Knowledge Search system.

All functions are pure, use only the standard library, and are fully
type-hinted.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable
from typing import Dict

# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------

def minmax_normalize(scores: Dict[str, float]) -> Dict[str, float]:
    """
    Normalizes scores to [0, 1] range. 
    
    Includes safeguards:
    1. Returns zeros if all scores are identical (prevents div by zero).
    2. Uses an epsilon (1e-10) in the denominator for numerical stability.
    3. Handles empty input gracefully.
    """
    if not scores:
        return {}

    vals = list(scores.values())
    min_score = min(vals)
    max_score = max(vals)
    
    # Safeguard 1: All scores are identical
    if max_score == min_score:
        return {doc_id: 0.0 for doc_id in scores.keys()}

    # Safeguard 2: Use epsilon to prevent floating-point division errors
    epsilon = 1e-10
    denominator = max_score - min_score + epsilon
    
    return {
        doc_id: (score - min_score) / denominator 
        for doc_id, score in scores.items()
    }


def zscore_normalize(scores: dict[str, float]) -> dict[str, float]:
    """Z-score normalise, then shift to ``[0, 1]`` via min-max.

    ``z = (score - mean) / (std + 1e-10)``

    * If all scores identical → all ``0.0``.
    * Empty dict → empty dict.
    """
    if not scores:
        return {}

    vals = list(scores.values())
    mean = statistics.mean(vals)
    std = statistics.pstdev(vals)      # population std (no Bessel correction)

    # All identical → std == 0 → return zeros directly.
    if std == 0.0:
        return {k: 0.0 for k in scores}

    denom = std + 1e-10
    z_scores: dict[str, float] = {k: (v - mean) / denom for k, v in scores.items()}

    # Shift z-scores to [0, 1] via min-max.
    return minmax_normalize(z_scores)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_NORMALIZERS: dict[str, Callable[[dict[str, float]], dict[str, float]]] = {
    "minmax": minmax_normalize,
    "zscore": zscore_normalize,
}


def get_normalizer(
    name: str,
) -> Callable[[dict[str, float]], dict[str, float]]:
    """Return the normalizer function registered under *name*.

    Raises:
        ValueError: If *name* is not ``"minmax"`` or ``"zscore"``.
    """
    try:
        return _NORMALIZERS[name]
    except KeyError:
        valid = ", ".join(sorted(_NORMALIZERS))
        raise ValueError(
            f"Unknown normalizer {name!r}. Choose from: {valid}"
        ) from None
    