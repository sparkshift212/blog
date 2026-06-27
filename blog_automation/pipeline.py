"""
pipeline.py – Orchestrates the full end-to-end article generation pipeline.

Execution order:
  1. PinterestService  → scrape latest pin
  2. DuplicateChecker  → skip if already published
  3. AIWriter          → generate blog article (markdown + SEO)
  4. BasePublisher     → publish to configured backend
  5. SitemapService    → update sitemap.xml
  6. ArticleRepository → record in database

Each step is logged and any failure is caught, recorded, and re-raised so
the caller (CLI or scheduler) decides how to handle it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from database import ArticleRepository, article_repo
from logger import get_logger
from models import ArticleRecord, BlogArticle, PublishStatus
from services.ai_writer import AIWriter
from services.duplicate_checker import DuplicateChecker
from services.pinterest import PinterestService
from services.publisher import BasePublisher, get_publisher
from services.sitemap import SitemapService
from settings import settings
from utils import now_utc

log = get_logger("pipeline")


class Pipeline:
    """Full automation pipeline for generating and publishing blog posts.

    Args:
        publish: When ``False`` the publisher step is skipped (generate-only mode).
        publisher: Override the default publisher (useful for testing).
        repo: Override the default repository (useful for testing).
    """

    def __init__(
        self,
        publish: bool = True,
        publisher: Optional[BasePublisher] = None,
        repo: Optional[ArticleRepository] = None,
    ) -> None:
        self._publish = publish
        self._pinterest = PinterestService(settings.pinterest_profile_url)
        self._writer = AIWriter()
        self._checker = DuplicateChecker(repo or article_repo)
        self._publisher = publisher or (get_publisher() if publish else None)
        self._sitemap = SitemapService()
        self._repo = repo or article_repo

    def execute(self) -> Optional[BlogArticle]:
        """Run the complete pipeline and return the generated article.

        Returns:
            The :class:`BlogArticle` on success, or ``None`` if skipped
            (e.g. duplicate detected).

        Raises:
            Exception: Any unrecoverable error encountered during the run.
        """
        log.info("═══ Pipeline starting ═══")

        # ── Step 1: Pinterest ─────────────────────────────────────────────────
        log.info("[1/5] Fetching latest Pinterest pin…")
        try:
            pin = self._pinterest.get_latest_pin()
        except Exception as exc:
            log.error("Pinterest fetch failed: %s", exc, exc_info=True)
            raise

        log.info("     Pin topic: %s", pin.topic)

        # ── Step 2: Duplicate check (pre-generation) ──────────────────────────
        log.info("[2/5] Checking for duplicates…")
        from utils import make_slug
        tentative_slug = make_slug(pin.topic)
        if self._checker.is_duplicate(title=pin.title, slug=tentative_slug, topic=pin.topic):
            log.info("     Skipped – duplicate detected.")
            return None

        # ── Step 3: AI generation ─────────────────────────────────────────────
        log.info("[3/5] Generating article with AI…")
        try:
            article = self._writer.generate(pin)
        except Exception as exc:
            log.error("AI generation failed: %s", exc, exc_info=True)
            raise

        # Post-generation duplicate check (now we have the actual slug + hash)
        if self._checker.is_duplicate(
            title=article.seo.seo_title,
            slug=article.seo.slug,
            topic=pin.topic,
        ):
            log.info("     Skipped – post-generation duplicate detected.")
            return None

        log.info("     Generated: '%s' (%d chars)", article.seo.seo_title, len(article.markdown_content))

        # ── Step 4: Publish ───────────────────────────────────────────────────
        published_url = ""
        if self._publish and self._publisher:
            log.info("[4/5] Publishing article…")
            try:
                published_url = self._publisher.publish(article)
                article.published_url = published_url
                article.status = PublishStatus.PUBLISHED
                log.info("     Published → %s", published_url)
            except Exception as exc:
                log.error("Publishing failed: %s", exc, exc_info=True)
                article.status = PublishStatus.FAILED
                # Fall through to still log the attempt
        else:
            log.info("[4/5] Skipping publish (generate-only mode).")

        # ── Step 5: Sitemap ───────────────────────────────────────────────────
        if article.status == PublishStatus.PUBLISHED:
            log.info("[5/5] Updating sitemap…")
            try:
                self._sitemap.add_url(article.seo.slug)
            except Exception as exc:
                log.warning("Sitemap update failed (non-fatal): %s", exc)

        # ── Step 6: Database ──────────────────────────────────────────────────
        log.info("[6/6] Saving record to database…")
        record = ArticleRecord(
            title=article.seo.seo_title,
            slug=article.seo.slug,
            topic=pin.topic,
            focus_keyword=article.seo.focus_keyword,
            category=article.seo.category,
            pinterest_url=pin.pin_url,
            content_hash=article.content_hash,
            status=article.status,
            published_url=published_url,
            published_at=now_utc() if article.status == PublishStatus.PUBLISHED else None,
        )
        try:
            self._repo.insert(record)
            log.info("     Record saved. status=%s", record.status.value)
        except Exception as exc:
            log.error("Database insert failed: %s", exc, exc_info=True)
            # Non-fatal – article may already be published

        log.info("═══ Pipeline complete ═══")
        return article
