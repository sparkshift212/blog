"""
services/markdown_converter.py – Converts Markdown to clean, semantic HTML
suitable for injection into the Yarnoodle Amigurumi website.

Applies:
  - Python-Markdown with useful extensions.
  - Post-processing to wrap the output in an article scaffold.
  - Adds Yarnoodle-specific CSS class names.
"""

from __future__ import annotations

import markdown
from markdown.extensions.toc import TocExtension

from config import SITE_NAME, SITE_URL
from logger import get_logger

log = get_logger("markdown_converter")

# Extensions loaded by default for every conversion
_EXTENSIONS = [
    "markdown.extensions.extra",       # tables, fenced code, footnotes, etc.
    "markdown.extensions.smarty",      # smart quotes & dashes
    "markdown.extensions.nl2br",       # newlines → <br>
    TocExtension(permalink=True),      # anchored headings
]


class MarkdownConverter:
    """Converts a Markdown string to clean semantic HTML."""

    def convert(self, md_text: str, title: str = "", slug: str = "") -> str:
        """Transform *md_text* into a full article HTML fragment.

        Args:
            md_text: Full Markdown content of the blog post.
            title: Article title (used in the HTML article header).
            slug: URL slug (used to set the article ``id`` attribute).

        Returns:
            Semantic HTML string ready to embed in a page template.
        """
        log.debug("Converting markdown to HTML (chars=%d)", len(md_text))

        # Convert markdown → HTML
        md = markdown.Markdown(extensions=_EXTENSIONS)
        body_html = md.convert(md_text)

        # Wrap in article scaffold with Yarnoodle CSS classes
        html = self._wrap(body_html, title=title, slug=slug)
        log.debug("Conversion complete (html chars=%d)", len(html))
        return html

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _wrap(body_html: str, title: str, slug: str) -> str:
        """Wrap *body_html* in the Yarnoodle article scaffold.

        Args:
            body_html: Raw converted HTML from python-markdown.
            title: Article title string (may be empty).
            slug: URL slug for the article ``id``.

        Returns:
            Fully scaffolded HTML string.
        """
        article_id = slug if slug else "generated-post"
        site_name_attr = SITE_NAME.replace('"', "&quot;")

        return f"""<article id="{article_id}" class="blog-post-content" itemscope itemtype="https://schema.org/BlogPosting">
  <meta itemprop="publisher" content="{site_name_attr}">
  <div class="post-body">
    {body_html}
  </div>
  <!-- CTA -->
  <div class="post-cta" style="
    background: linear-gradient(135deg,#f4ede4 0%,#e8d5c4 100%);
    border-radius: 16px; padding: 2rem; margin-top: 3rem; text-align: center;">
    <h3 style="color:#8B4513; margin-bottom: 0.75rem;">
      🧶 Join the Yarnoodle Cozy Club!
    </h3>
    <p style="color:#5a4a42; margin-bottom: 1.25rem;">
      Get a free mini pattern + weekly crochet tips delivered straight to your inbox.
    </p>
    <a href="{SITE_URL}/index.html#newsletter"
       class="btn btn-primary"
       style="display:inline-block; padding: 12px 28px;">
      Subscribe Free
    </a>
  </div>
</article>"""
