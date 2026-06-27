"""
services/duplicate_checker.py – Guards against generating duplicate articles.

Checks the database for collisions on:
  1. content_hash – same title + slug + topic fingerprint
  2. slug          – identical URL slug
  3. topic         – exact topic string (case-insensitive)
"""

from __future__ import annotations

from database import ArticleRepository
from logger import get_logger
from utils import compute_hash, make_slug

log = get_logger("duplicate_checker")


class DuplicateChecker:
    """Validates that a prospective article is genuinely new.

    Args:
        repo: The :class:`ArticleRepository` instance to query against.
    """

    def __init__(self, repo: ArticleRepository) -> None:
        self._repo = repo

    def is_duplicate(self, title: str, slug: str, topic: str) -> bool:
        """Return ``True`` if the article should be skipped as a duplicate.

        Performs three independent checks and short-circuits on the first hit.

        Args:
            title: Proposed SEO title.
            slug: URL slug derived from the title.
            topic: The raw topic string from Pinterest.

        Returns:
            ``True`` when a duplicate is detected; ``False`` otherwise.
        """
        content_hash = compute_hash(title, slug, topic)

        if self._repo.exists_by_hash(content_hash):
            log.warning("Duplicate detected via content_hash – skipping. topic=%s", topic)
            return True

        if self._repo.exists_by_slug(slug):
            log.warning("Duplicate detected via slug='%s' – skipping.", slug)
            return True

        if self._repo.exists_by_topic(topic):
            log.warning("Duplicate detected via topic='%s' – skipping.", topic)
            return True

        log.debug("No duplicate found for topic='%s'", topic)
        return False

    def compute_hash(self, title: str, slug: str, topic: str) -> str:
        """Compute and return the content hash for the given fields.

        Args:
            title: Article title.
            slug:  URL slug.
            topic: Source topic.

        Returns:
            Hex SHA-256 string.
        """
        return compute_hash(title, slug, topic)
