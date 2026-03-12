"""Tests for backend.app.utils.preprocessing module."""

import sys
from pathlib import Path

import pytest

# Ensure the backend package is importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.utils.preprocessing import (
    STOP_WORDS,
    clean_text,
    extract_snippets,
    tokenize,
    truncate_text,
)


# ── clean_text ───────────────────────────────────────────────────────────────

class TestCleanText:
    """Tests for clean_text()."""

    def test_collapses_multiple_spaces(self) -> None:
        assert clean_text("hello    world") == "hello world"

    def test_collapses_multiple_newlines_and_tabs(self) -> None:
        assert clean_text("line1\n\n\nline2\t\tline3") == "line1 line2 line3"

    def test_removes_null_bytes(self) -> None:
        assert clean_text("hello\x00world") == "helloworld"

    def test_removes_control_characters(self) -> None:
        # \x07 = BEL, \x0b = vertical tab — both are control chars and removed
        assert clean_text("abc\x07def\x0bghi") == "abcdefghi"

    def test_strips_leading_and_trailing_whitespace(self) -> None:
        assert clean_text("   spaced   ") == "spaced"

    def test_empty_string(self) -> None:
        assert clean_text("") == ""

    def test_already_clean_text(self) -> None:
        assert clean_text("perfectly fine text") == "perfectly fine text"


# ── tokenize ─────────────────────────────────────────────────────────────────

class TestTokenize:
    """Tests for tokenize()."""

    def test_lowercases_tokens(self) -> None:
        tokens = tokenize("Hello World Python")
        assert all(tok == tok.lower() for tok in tokens)

    def test_removes_stop_words(self) -> None:
        tokens = tokenize("the cat is on the mat")
        for sw in ("the", "is", "on"):
            assert sw not in tokens

    def test_removes_short_tokens(self) -> None:
        tokens = tokenize("I am a great developer")
        # "I", "a" are single-char → removed; "am" is a 2-char non-stop word
        assert "i" not in tokens
        assert "a" not in tokens
        assert "am" in tokens

    def test_splits_on_non_alphanumeric(self) -> None:
        tokens = tokenize("fast-food, mega_bytes! hello.world")
        assert "fast" in tokens
        assert "food" in tokens
        assert "mega" in tokens
        assert "bytes" in tokens
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_string_returns_empty_list(self) -> None:
        assert tokenize("") == []

    def test_only_stop_words_returns_empty(self) -> None:
        assert tokenize("the a an is are was") == []


# ── truncate_text ────────────────────────────────────────────────────────────

class TestTruncateText:
    """Tests for truncate_text()."""

    def test_under_limit_returns_unchanged(self) -> None:
        text = "short text"
        assert truncate_text(text, max_chars=100) == text

    def test_exact_limit_returns_unchanged(self) -> None:
        text = "x" * 50
        assert truncate_text(text, max_chars=50) == text

    def test_over_limit_truncates_with_marker(self) -> None:
        text = "a" * 200
        result = truncate_text(text, max_chars=100)
        assert result.endswith("[truncated]")
        assert len(result) == 100 + len("[truncated]")

    def test_default_limit_is_50000(self) -> None:
        text = "b" * 50_000
        assert truncate_text(text) == text  # exactly at limit
        assert truncate_text(text + "extra").endswith("[truncated]")


# ── extract_snippets ─────────────────────────────────────────────────────────

class TestExtractSnippets:
    """Tests for extract_snippets()."""

    def test_token_found_is_bolded(self) -> None:
        text = "The quick brown fox jumps over the lazy dog"
        result = extract_snippets(text, ["fox"])
        assert "**fox**" in result

    def test_case_insensitive_match(self) -> None:
        text = "Python is a great language"
        result = extract_snippets(text, ["PYTHON"])
        assert "**Python**" in result  # original casing preserved, bolded

    def test_no_match_returns_first_200_chars(self) -> None:
        text = "a" * 300
        result = extract_snippets(text, ["zzz"])
        assert result == "a" * 200

    def test_ellipsis_when_context_trimmed(self) -> None:
        prefix = "x" * 200
        suffix = "y" * 200
        text = f"{prefix}KEYWORD{suffix}"
        result = extract_snippets(text, ["keyword"], context_chars=50)
        assert result.startswith("...")
        assert result.endswith("...")

    def test_no_leading_ellipsis_at_start_of_text(self) -> None:
        text = "hello world rest of the text goes here"
        result = extract_snippets(text, ["hello"], context_chars=100)
        assert not result.startswith("...")

    def test_short_text_no_match_returns_full_text(self) -> None:
        text = "tiny"
        result = extract_snippets(text, ["missing"])
        assert result == "tiny"
