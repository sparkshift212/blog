"""
services/sitemap.py – Appends newly published article URLs to sitemap.xml.

Creates sitemap.xml if it doesn't exist yet, then upserts the new URL entry.
Generates a standard XML sitemap compatible with Google Search Console.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from config import GENERATED_DIR, SITE_URL
from logger import get_logger

log = get_logger("sitemap")

SITEMAP_PATH = Path(GENERATED_DIR) / "sitemap.xml"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class SitemapService:
    """Maintains a dynamic sitemap.xml for generated blog posts."""

    def add_url(self, slug: str, last_modified: datetime | None = None) -> None:
        """Add or update *slug* in the sitemap.

        Args:
            slug: URL slug of the published article.
            last_modified: Publication timestamp (defaults to now).
        """
        url = f"{SITE_URL}/{slug}.html"
        lastmod = (last_modified or datetime.now(tz=timezone.utc)).strftime("%Y-%m-%d")

        tree, root = self._load_or_create()

        # Check if URL already exists → update lastmod
        for url_el in root.findall(f"{{{SITEMAP_NS}}}url"):
            loc = url_el.find(f"{{{SITEMAP_NS}}}loc")
            if loc is not None and loc.text == url:
                lm = url_el.find(f"{{{SITEMAP_NS}}}lastmod")
                if lm is not None:
                    lm.text = lastmod
                log.debug("Updated sitemap entry: %s", url)
                self._save(tree)
                return

        # Create new entry
        url_el = ET.SubElement(root, "url")
        ET.SubElement(url_el, "loc").text = url
        ET.SubElement(url_el, "lastmod").text = lastmod
        ET.SubElement(url_el, "changefreq").text = "monthly"
        ET.SubElement(url_el, "priority").text = "0.8"

        self._save(tree)
        log.info("Added to sitemap: %s", url)

    # ── Private ───────────────────────────────────────────────────────────────

    def _load_or_create(self) -> tuple[ET.ElementTree, ET.Element]:
        """Load existing sitemap.xml or create a new one."""
        Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)

        if SITEMAP_PATH.exists():
            ET.register_namespace("", SITEMAP_NS)
            tree = ET.parse(str(SITEMAP_PATH))
            root = tree.getroot()
        else:
            ET.register_namespace("", SITEMAP_NS)
            root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
            tree = ET.ElementTree(root)

        return tree, root

    def _save(self, tree: ET.ElementTree) -> None:
        """Write the sitemap tree to disk with proper XML declaration."""
        tree.write(
            str(SITEMAP_PATH),
            xml_declaration=True,
            encoding="utf-8",
            default_namespace=SITEMAP_NS,
        )
