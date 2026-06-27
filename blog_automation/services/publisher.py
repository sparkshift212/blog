"""
services/publisher.py – Publisher abstraction layer.

Provides a base :class:`BasePublisher` protocol and three concrete backends:
  1. :class:`StaticHTMLPublisher`   – saves an HTML file to disk.
  2. :class:`WordPressPublisher`    – posts via the WordPress REST API.
  3. :class:`APIPublisher`          – posts to a custom REST endpoint.

The active publisher is selected via the ``PUBLISHER_MODE`` env var and
instantiated by the :func:`get_publisher` factory function.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import GENERATED_DIR, SITE_NAME, SITE_URL
from logger import get_logger
from models import BlogArticle, PublishStatus
from settings import settings

log = get_logger("publisher")


# ── Base interface ─────────────────────────────────────────────────────────────

class BasePublisher(ABC):
    """Abstract base class all publishers must implement."""

    @abstractmethod
    def publish(self, article: BlogArticle) -> str:
        """Publish *article* and return the live URL.

        Args:
            article: The fully generated :class:`BlogArticle`.

        Returns:
            Absolute URL of the published article (empty string on failure).
        """


# ── Static HTML publisher ─────────────────────────────────────────────────────

class StaticHTMLPublisher(BasePublisher):
    """Writes the article as a standalone HTML file to the output directory.

    Wraps the converted HTML in a full Yarnoodle-styled page template so
    the file opens correctly in a browser.

    Args:
        output_dir: Directory where HTML files are saved.
    """

    def __init__(self, output_dir: str = GENERATED_DIR) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, article: BlogArticle) -> str:
        slug = article.seo.slug
        filename = self._output_dir / f"{slug}.html"
        page_html = self._build_page(article)

        filename.write_text(page_html, encoding="utf-8")
        log.info("Static HTML saved → %s", filename)

        # Also save a JSON metadata sidecar
        meta_file = self._output_dir / f"{slug}.meta.json"
        meta_file.write_text(
            json.dumps(article.seo.model_dump(), indent=2, default=str),
            encoding="utf-8",
        )

        return f"file://{filename.resolve()}"

    def _build_page(self, article: BlogArticle) -> str:
        """Render a full standalone HTML page for *article*."""
        seo = article.seo
        p = article.pinterest
        tags_str = ", ".join(seo.tags)
        schema_keywords = json.dumps(seo.secondary_keywords)
        published_iso = datetime.utcnow().isoformat() + "Z"

        hashtags_html = "".join(
            f'<a href="https://www.pinterest.com/search/pins/?q={h.lstrip("#")}" '
            f'class="hashtag" target="_blank" rel="noopener">{h}</a> '
            for h in p.hashtags[:10]
        )

        return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{seo.meta_title} | {SITE_NAME}</title>
  <meta name="description" content="{seo.meta_description}">
  <meta name="keywords" content="{tags_str}">
  <meta property="og:title" content="{seo.meta_title}">
  <meta property="og:description" content="{seo.meta_description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE_URL}/{seo.slug}.html">
  <meta property="article:tag" content="{seo.focus_keyword}">
  <link rel="canonical" href="{SITE_URL}/{seo.slug}.html">
  <link rel="stylesheet" href="css/styles.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;600;700&family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "{seo.seo_title}",
    "description": "{seo.meta_description}",
    "keywords": {schema_keywords},
    "datePublished": "{published_iso}",
    "author": {{"@type": "Person", "name": "Sarah Weaver"}},
    "publisher": {{"@type": "Organization", "name": "{SITE_NAME}", "url": "{SITE_URL}"}}
  }}
  </script>
</head>
<body>
  <header class="site-header" role="banner">
    <div class="container">
      <a href="{SITE_URL}/index.html" class="site-logo">
        <i class="fas fa-star" style="color:#C17B5C;margin-right:8px;"></i> Yarnoodle
      </a>
      <nav class="main-nav">
        <ul class="nav-list">
          <li><a href="{SITE_URL}/index.html" class="nav-link">Home</a></li>
          <li><a href="{SITE_URL}/blog.html" class="nav-link">Blog</a></li>
          <li><a href="{SITE_URL}/patterns.html" class="nav-link">Patterns</a></li>
          <li><a href="{SITE_URL}/shop.html" class="nav-link">Shop</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main>
    <div class="container" style="max-width:860px;padding:3rem 1.5rem;">
      <div style="margin-bottom:2rem;">
        <span style="background:#f4ede4;color:#C17B5C;font-size:.8rem;font-weight:700;padding:4px 12px;border-radius:100px;text-transform:uppercase;letter-spacing:.5px;">
          {seo.category}
        </span>
        <h1 style="margin-top:1rem;font-size:2.2rem;line-height:1.2;">{seo.seo_title}</h1>
        <p style="color:#888;font-size:.9rem;margin-top:.5rem;">
          By <strong>Sarah Weaver</strong> &bull; {datetime.utcnow().strftime("%B %d, %Y")} &bull; {seo.focus_keyword}
        </p>
        <div style="margin-top:1rem;">{hashtags_html}</div>
      </div>

      {article.html_content}

    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>&copy; {datetime.utcnow().year} {SITE_NAME}. All rights reserved.</p>
    </div>
  </footer>

  <script src="js/main.js"></script>
</body>
</html>"""


# ── WordPress publisher ────────────────────────────────────────────────────────

class WordPressPublisher(BasePublisher):
    """Posts the article via the WordPress REST API.

    Requires ``WORDPRESS_URL``, ``WORDPRESS_USERNAME``, and
    ``WORDPRESS_PASSWORD`` (application password) in the environment.
    """

    def __init__(self) -> None:
        self._base_url = settings.wordpress_url.rstrip("/")
        self._auth = (settings.wordpress_username, settings.wordpress_password)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
    def publish(self, article: BlogArticle) -> str:
        endpoint = f"{self._base_url}/wp-json/wp/v2/posts"
        payload = {
            "title": article.seo.seo_title,
            "slug": article.seo.slug,
            "content": article.html_content,
            "status": "publish",
            "excerpt": article.seo.meta_description,
            "meta": {
                "focus_keyword": article.seo.focus_keyword,
                "meta_description": article.seo.meta_description,
            },
        }

        log.debug("POSTing to WordPress: %s", endpoint)
        resp = requests.post(
            endpoint,
            json=payload,
            auth=self._auth,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        url: str = data.get("link", "")
        log.info("Published to WordPress: %s", url)
        return url


# ── Custom API publisher ───────────────────────────────────────────────────────

class APIPublisher(BasePublisher):
    """Posts the article to a custom REST endpoint.

    Requires ``WEBSITE_API`` (base URL) and ``WEBSITE_TOKEN`` (Bearer token).
    """

    def __init__(self) -> None:
        self._api_url = settings.website_api.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {settings.website_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True)
    def publish(self, article: BlogArticle) -> str:
        endpoint = f"{self._api_url}/posts"
        payload = {
            "title": article.seo.seo_title,
            "slug": article.seo.slug,
            "html": article.html_content,
            "markdown": article.markdown_content,
            "meta_title": article.seo.meta_title,
            "meta_description": article.seo.meta_description,
            "focus_keyword": article.seo.focus_keyword,
            "category": article.seo.category,
            "tags": article.seo.tags,
            "status": "published",
        }

        log.debug("POSTing to custom API: %s", endpoint)
        resp = requests.post(endpoint, json=payload, headers=self._headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        url: str = data.get("url", "")
        log.info("Published via API: %s", url)
        return url


# ── Factory ───────────────────────────────────────────────────────────────────

def get_publisher(mode: Optional[str] = None) -> BasePublisher:
    """Instantiate and return the publisher for *mode*.

    Args:
        mode: One of ``"static"``, ``"wordpress"``, or ``"api"``.
              Falls back to the ``PUBLISHER_MODE`` env var.

    Returns:
        Concrete :class:`BasePublisher` instance.

    Raises:
        ValueError: On unrecognised mode.
    """
    resolved = (mode or settings.publisher_mode).lower()
    log.info("Using publisher mode: %s", resolved)

    if resolved == "static":
        return StaticHTMLPublisher(settings.website_output_dir)
    if resolved == "wordpress":
        return WordPressPublisher()
    if resolved == "api":
        return APIPublisher()

    raise ValueError(f"Unknown PUBLISHER_MODE='{resolved}'. Choose: static | wordpress | api")
