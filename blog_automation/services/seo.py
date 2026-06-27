"""
services/seo.py – SEO utility helpers (slug normalisation, meta validation).
Heavy lifting is done by the AI; this module post-processes and validates output.
"""

from __future__ import annotations

from logger import get_logger
from utils import make_slug, truncate

log = get_logger("seo")


class SEOService:
    """Validates and normalises SEO metadata produced by the AI writer."""

    MAX_META_TITLE = 60
    MAX_META_DESC = 160

    def normalise_meta_title(self, title: str) -> str:
        """Ensure meta title fits within 60 characters.

        Args:
            title: Raw AI-generated meta title.

        Returns:
            Title truncated to ``MAX_META_TITLE`` characters if needed.
        """
        result = truncate(title, self.MAX_META_TITLE)
        if result != title:
            log.debug("Meta title truncated from %d to %d chars", len(title), len(result))
        return result

    def normalise_meta_description(self, desc: str) -> str:
        """Ensure meta description fits within 160 characters.

        Args:
            desc: Raw AI-generated meta description.

        Returns:
            Description truncated to ``MAX_META_DESC`` characters if needed.
        """
        result = truncate(desc, self.MAX_META_DESC)
        if result != desc:
            log.debug("Meta description truncated from %d to %d chars", len(desc), len(result))
        return result

    def clean_slug(self, raw_slug: str) -> str:
        """Re-generate a clean URL slug from raw AI output.

        The AI sometimes returns slugs with uppercase letters, spaces, or
        underscores. This method guarantees a properly formatted slug.

        Args:
            raw_slug: Slug string as returned by the AI.

        Returns:
            Clean, URL-safe slug.
        """
        return make_slug(raw_slug)

    def validate_tags(self, tags: list[str], limit: int = 15) -> list[str]:
        """Deduplicate and enforce the maximum tag count.

        Args:
            tags: Raw tag list from AI output.
            limit: Maximum allowed tags.

        Returns:
            Cleaned, deduplicated tag list capped at *limit*.
        """
        seen: set[str] = set()
        result: list[str] = []
        for tag in tags:
            normalised = tag.strip().lower()
            if normalised and normalised not in seen:
                seen.add(normalised)
                result.append(tag.strip())
            if len(result) >= limit:
                break
        return result
