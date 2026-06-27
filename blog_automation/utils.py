"""
utils.py – Shared helper functions used across all services.
"""

from __future__ import annotations

import hashlib
import re
import textwrap
from datetime import datetime
from typing import Any

from slugify import slugify as _slugify


# ── Hashing ────────────────────────────────────────────────────────────────────

def compute_hash(*parts: str) -> str:
    """Compute a SHA-256 hash from one or more strings.

    The hash is used for duplicate detection. Any combination of title/slug/topic
    can be fed in to produce a stable fingerprint.

    Args:
        *parts: Strings to concatenate and hash.

    Returns:
        Hex-encoded 64-character SHA-256 digest.
    """
    combined = "|".join(p.strip().lower() for p in parts)
    return hashlib.sha256(combined.encode()).hexdigest()


# ── Slug helpers ───────────────────────────────────────────────────────────────

def make_slug(text: str) -> str:
    """Generate a URL-safe slug from any text.

    Args:
        text: Raw title or phrase.

    Returns:
        Lowercase, hyphenated slug (e.g. ``"crochet-fox-amigurumi"``).
    """
    return _slugify(text, max_length=80, word_boundary=True)


# ── Text helpers ───────────────────────────────────────────────────────────────

def word_count(text: str) -> int:
    """Count the words in a markdown or plain-text string."""
    return len(text.split())


def truncate(text: str, max_chars: int, suffix: str = "…") -> str:
    """Truncate *text* to at most *max_chars* characters.

    Args:
        text: Input string.
        max_chars: Maximum allowed length including suffix.
        suffix: Appended when truncation occurs.

    Returns:
        Original string or truncated version with suffix.
    """
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)].rstrip() + suffix


def clean_text(text: str) -> str:
    """Remove excess whitespace and non-printable characters from *text*."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    return text.strip()


# ── Keyword helpers ────────────────────────────────────────────────────────────

def extract_keywords_from_text(text: str, max_keywords: int = 10) -> list[str]:
    """Naive keyword extraction: splits on commas/newlines and deduplicates.

    Designed to be applied to the raw AI output before Pydantic validation.

    Args:
        text: Raw comma- or newline-separated keyword string.
        max_keywords: Upper limit on returned keywords.

    Returns:
        Deduplicated list of stripped keyword strings.
    """
    parts = re.split(r"[,\n]+", text)
    seen: set[str] = set()
    keywords: list[str] = []
    for part in parts:
        kw = part.strip().strip("#").strip()
        if kw and kw not in seen:
            seen.add(kw)
            keywords.append(kw)
        if len(keywords) >= max_keywords:
            break
    return keywords


# ── Date helpers ───────────────────────────────────────────────────────────────

def now_utc() -> datetime:
    """Return the current UTC datetime (timezone-naive for SQLite compat.)."""
    return datetime.utcnow()


def format_date(dt: datetime) -> str:
    """Format a datetime as ``YYYY-MM-DD`` for display."""
    return dt.strftime("%Y-%m-%d")


# ── JSON-safe coercion ─────────────────────────────────────────────────────────

def to_str_list(value: Any) -> list[str]:
    """Coerce *value* to a list of strings.

    Handles str, list, and None gracefully so AI output inconsistencies
    don't crash Pydantic parsing.

    Args:
        value: Raw value from AI JSON response.

    Returns:
        List of non-empty strings.
    """
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    if isinstance(value, str):
        return extract_keywords_from_text(value)
    return []
