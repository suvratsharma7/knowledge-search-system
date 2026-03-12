"""Tests for backend.app.search.normalizers."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.search.normalizers import (
    get_normalizer,
    minmax_normalize,
    zscore_normalize,
)


# ── minmax_normalize ─────────────────────────────────────────────────────────

class TestMinmaxNormalize:
    def test_minmax_basic(self) -> None:
        result = minmax_normalize({"a": 1.0, "b": 5.0, "c": 3.0})
        assert result["a"] == pytest.approx(0.0, abs=1e-6)
        assert result["c"] == pytest.approx(0.5, abs=1e-3)
        assert result["b"] == pytest.approx(1.0, abs=1e-3)

    def test_minmax_all_same(self) -> None:
        result = minmax_normalize({"a": 3.0, "b": 3.0})
        assert result == {"a": 0.0, "b": 0.0}
        # Importantly — no NaN!
        for v in result.values():
            assert not math.isnan(v)

    def test_minmax_empty(self) -> None:
        assert minmax_normalize({}) == {}

    def test_minmax_single_value(self) -> None:
        result = minmax_normalize({"a": 5.0})
        assert result == {"a": 0.0}
        assert not math.isnan(result["a"])


# ── zscore_normalize ─────────────────────────────────────────────────────────

class TestZscoreNormalize:
    def test_zscore_basic(self) -> None:
        result = zscore_normalize({"a": 1.0, "b": 5.0, "c": 3.0})
        for v in result.values():
            assert 0.0 <= v <= 1.0, f"value {v} outside [0, 1]"

    def test_zscore_all_same(self) -> None:
        result = zscore_normalize({"a": 3.0, "b": 3.0})
        assert result == {"a": 0.0, "b": 0.0}
        for v in result.values():
            assert not math.isnan(v)

    def test_zscore_empty(self) -> None:
        assert zscore_normalize({}) == {}

    def test_zscore_preserves_order(self) -> None:
        result = zscore_normalize({"x": 10.0, "y": 20.0, "z": 30.0})
        assert result["x"] < result["y"] < result["z"]


# ── get_normalizer ───────────────────────────────────────────────────────────

class TestGetNormalizer:
    def test_get_normalizer_valid(self) -> None:
        mm = get_normalizer("minmax")
        zs = get_normalizer("zscore")
        assert callable(mm)
        assert callable(zs)
        assert mm is minmax_normalize
        assert zs is zscore_normalize

    def test_get_normalizer_invalid(self) -> None:
        with pytest.raises(ValueError, match="unknown"):
            get_normalizer("unknown")
