"""
Score normalization strategies for the Knowledge Search system.

All functions are pure, use only the standard library, and are fully
type-hinted.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable


# ---------------------------------------------------------------------------
# Normalizers
# ---------------------------------------------------------------------------

def minmax_normalize(scores: dict[str, float]) -> dict[str, float]:
    """Scale every value in *scores* to the ``[0, 1]`` range.

    ``norm = (score - min) / (max - min + 1e-10)``

    * If all scores are identical → all values become ``0.0``.
    * Empty dict → empty dict.
    """
    if not scores:
        return {}

    vals = list(scores.values())
    lo = min(vals)
    hi = max(vals)
    span = hi - lo

    # All identical → return 0.0 for every key.
    if span == 0.0:
        return {k: 0.0 for k in scores}

    denom = span + 1e-10
    return {k: (v - lo) / denom for k, v in scores.items()}


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
