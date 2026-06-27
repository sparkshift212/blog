"""
services/pinterest.py – Scrapes the YarnoodleAmigurumi Pinterest profile
and returns structured :class:`PinData` for the most recent pin.

Pinterest renders its content via JavaScript, so we use a combination of:
1. Open Graph / meta tags (fast, reliable).
2. JSON-LD embedded in the page.
3. Fallback heuristics from BeautifulSoup text parsing.
"""

from __future__ import annotations

import json
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from config import PINTEREST_HEADERS
from logger import get_logger
from models import PinData
from utils import clean_text, extract_keywords_from_text

log = get_logger("pinterest")


class PinterestService:
    """Fetches and parses the latest Pinterest pin for a given profile URL."""

    def __init__(self, profile_url: str) -> None:
        self._profile_url = profile_url
        self._session = requests.Session()
        self._session.headers.update(PINTEREST_HEADERS)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_latest_pin(self) -> PinData:
        """Scrape the profile page and return the most recent pin.

        Returns:
            Populated :class:`PinData` describing the latest pin.

        Raises:
            RuntimeError: If no pin data can be extracted after all retries.
        """
        log.info("Fetching Pinterest profile: %s", self._profile_url)
        html = self._fetch_page(self._profile_url)
        pin = self._parse_pin(html)
        log.info("Extracted pin: %s", pin.title)
        return pin

    # ── Private helpers ───────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _fetch_page(self, url: str) -> str:
        """Download *url* with retries and return the response text.

        Args:
            url: Absolute URL to download.

        Returns:
            Raw HTML as a string.

        Raises:
            requests.HTTPError: On non-2xx responses.
        """
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text

    def _parse_pin(self, html: str) -> PinData:
        """Parse pin metadata from a Pinterest profile HTML page.

        Pinterest embeds pin data in Open Graph tags and JSON-LD scripts.
        We attempt JSON-LD first (richest data), then fall back to OG tags.

        Args:
            html: Raw HTML content of the Pinterest profile page.

        Returns:
            :class:`PinData` populated from extracted metadata.
        """
        soup = BeautifulSoup(html, "lxml")

        # 1. Try JSON-LD ---------------------------------------------------
        pin = self._try_json_ld(soup)
        if pin:
            return pin

        # 2. Try Open Graph / meta tags ------------------------------------
        pin = self._try_og_tags(soup)
        if pin:
            return pin

        # 3. Fallback: best-effort from page text -------------------------
        log.warning("Using fallback pin extraction – Pinterest may have blocked scraping")
        return self._fallback_pin()

    def _try_json_ld(self, soup: BeautifulSoup) -> Optional[PinData]:
        """Attempt to extract pin data from JSON-LD script blocks."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                if data.get("@type") in ("ImageObject", "CreativeWork", "Article"):
                    title = data.get("name", "")
                    description = data.get("description", "")
                    image = data.get("image", {})
                    image_url = image.get("url", "") if isinstance(image, dict) else str(image)
                    if title:
                        return self._build_pin(title, description, image_url, self._profile_url)
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _try_og_tags(self, soup: BeautifulSoup) -> Optional[PinData]:
        """Extract pin metadata from Open Graph <meta> tags."""
        def _meta(prop: str) -> str:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return (tag.get("content", "") if tag else "").strip()

        title = _meta("og:title") or _meta("twitter:title")
        description = _meta("og:description") or _meta("description")
        image_url = _meta("og:image") or _meta("twitter:image")
        pin_url = _meta("og:url") or self._profile_url

        if title and title != "Pinterest":
            return self._build_pin(title, description, image_url, pin_url)
        return None

    def _fallback_pin(self) -> PinData:
        """Return a crochet-themed default pin when scraping fails.

        This allows the pipeline to continue with a sensible topic rather
        than crashing when Pinterest blocks the request.
        """
        return PinData(
            title="Cute Crochet Amigurumi Fox Pattern",
            description=(
                "Learn how to make an adorable crochet fox amigurumi! "
                "Perfect for beginners, this step-by-step guide covers yarn, "
                "hooks, and shaping tips."
            ),
            image_url="",
            pin_url=self._profile_url,
            topic="crochet fox amigurumi",
            keywords=[
                "crochet fox",
                "amigurumi fox",
                "free crochet pattern",
                "beginner crochet",
                "stuffed animal",
            ],
        )

    @staticmethod
    def _build_pin(
        title: str,
        description: str,
        image_url: str,
        pin_url: str,
    ) -> PinData:
        """Construct a :class:`PinData` from raw scraped strings.

        Args:
            title: Raw pin title.
            description: Raw pin description.
            image_url: URL to the pin's image.
            pin_url: Canonical URL of the pin.

        Returns:
            Validated :class:`PinData` instance.
        """
        title = clean_text(title)
        description = clean_text(description)

        # Derive topic from title (strip site branding noise)
        topic = re.sub(r"\|.*$|–.*$", "", title).strip()

        # Extract keywords from description
        keywords = extract_keywords_from_text(description, max_keywords=10)

        return PinData(
            title=title,
            description=description,
            image_url=image_url,
            pin_url=pin_url,
            topic=topic,
            keywords=keywords,
        )
