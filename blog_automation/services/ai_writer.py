"""
services/ai_writer.py – Generates a full SEO blog article using the OpenAI API.

Responsibilities:
  1. Build a structured system + user prompt from PinData.
  2. Call GPT-4o with JSON-mode response format.
  3. Parse the JSON into Pydantic models (SEOMetadata, BlogArticle, etc.).
  4. Validate word count and retry on failure.
"""

from __future__ import annotations

import json
import textwrap
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import DEFAULT_MODEL, MIN_WORD_COUNT, MAX_WORD_COUNT, SITE_NAME, SITE_URL
from logger import get_logger
from models import (
    BlogArticle,
    ImageAsset,
    PinData,
    PinterestMarketing,
    SEOMetadata,
    PublishStatus,
)
from services.images import ImageService
from services.markdown_converter import MarkdownConverter
from services.seo import SEOService
from settings import settings
from utils import compute_hash, make_slug, to_str_list, word_count

log = get_logger("ai_writer")


class AIWriter:
    """Orchestrates OpenAI to generate a complete blog article.

    Args:
        model: The OpenAI model to use (defaults to settings value).
    """

    def __init__(self, model: str | None = None) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = model or settings.openai_model or DEFAULT_MODEL
        self._seo = SEOService()
        self._img = ImageService()
        self._converter = MarkdownConverter()

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, pin: PinData) -> BlogArticle:
        """Generate a complete blog article from a Pinterest pin.

        Args:
            pin: Scraped :class:`PinData` from the Pinterest service.

        Returns:
            Fully populated :class:`BlogArticle`.

        Raises:
            ValueError: If the AI response cannot be parsed.
            RuntimeError: After all retries are exhausted.
        """
        log.info("Generating article for pin topic: '%s'", pin.topic)
        raw_json = self._call_openai(pin)
        article = self._parse_response(raw_json, pin)
        log.info(
            "Article generated: '%s' (%d words)",
            article.seo.seo_title,
            word_count(article.markdown_content),
        )
        return article

    # ── OpenAI call ───────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        reraise=True,
    )
    def _call_openai(self, pin: PinData) -> dict[str, Any]:
        """Call the OpenAI Chat API and return the parsed JSON dict.

        Args:
            pin: Source pin for the prompt.

        Returns:
            Parsed JSON dict from the API response.

        Raises:
            ValueError: If JSON cannot be decoded from the response.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(pin)

        log.debug("Calling OpenAI model=%s", self._model)

        response = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            temperature=0.75,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=120,
        )

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            log.error("Failed to decode JSON from OpenAI response: %s", exc)
            raise ValueError("OpenAI returned non-JSON content") from exc

    # ── Prompt builders ───────────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        return textwrap.dedent(f"""
            You are an expert SEO content writer, Pinterest marketing strategist,
            and crochet amigurumi specialist for the website "{SITE_NAME}" ({SITE_URL}).

            Your writing style:
            - Fluent, natural English
            - Friendly and encouraging – written for absolute beginners
            - Rich in practical detail and personal voice
            - Free of AI clichés ("delve", "tapestry of", "transformative", etc.)
            - Google EEAT compliant: show expertise, experience, authority, trust

            Output STRICTLY valid JSON matching the schema described below.
            Do NOT include markdown fences around the JSON.
        """).strip()

    def _build_user_prompt(self, pin: PinData) -> str:
        keywords_str = ", ".join(pin.keywords) if pin.keywords else pin.topic

        return textwrap.dedent(f"""
            Pinterest Pin Details:
            - Title: {pin.title}
            - Description: {pin.description}
            - Topic: {pin.topic}
            - Keywords: {keywords_str}

            Generate a blog article following the JSON schema EXACTLY:

            {{
              "seo_title": "Click-worthy SEO title (max 70 chars)",
              "slug": "url-slug-lowercase-hyphenated",
              "meta_title": "Meta title (max 60 chars)",
              "meta_description": "Meta description (max 160 chars)",
              "focus_keyword": "Primary keyword",
              "secondary_keywords": ["kw1","kw2",...],
              "pinterest_keywords": ["pk1","pk2",...],
              "category": "Animals | Fantasy | Tips & Tricks | Guides",
              "tags": ["tag1","tag2",...],
              "internal_links": [
                "Link text:URL",
                ...
              ],
              "pinterest_pin_title": "Pinterest pin title",
              "pinterest_pin_description": "Pin description 200 chars max",
              "hashtags": ["#crochet","#amigurumi",...],
              "social_caption": "Instagram/social caption 200 chars max",
              "markdown_content": "FULL article in Markdown 2000-3000 words. Use ## headings. Include sections: Introduction, Materials, Yarn Recommendation, Hook Size, Skill Level, Step-by-Step Guide (with ### sub-steps), Tips & Tricks, Common Mistakes to Avoid, FAQ (5 Q&As), Conclusion with CTA."
            }}

            Requirements for markdown_content:
            - Minimum {MIN_WORD_COUNT} words, maximum {MAX_WORD_COUNT} words
            - Begin with a warm, engaging Introduction
            - Include a Materials list (use markdown bullets)
            - Include a numbered Step-by-Step Guide
            - FAQ section with exactly 5 questions and detailed answers
            - Conclusion with a CTA linking to {SITE_URL}/index.html#newsletter
            - Mention "{SITE_NAME}" naturally within the text
            - Use SEO-optimised headings (include focus keyword in at least 2 headings)
            - Do NOT use placeholder text
        """).strip()

    # ── Response parser ───────────────────────────────────────────────────────

    def _parse_response(self, data: dict[str, Any], pin: PinData) -> BlogArticle:
        """Convert a raw OpenAI JSON dict into a :class:`BlogArticle`.

        Args:
            data: Parsed JSON dict from the OpenAI response.
            pin: Original pin (embedded in the article for traceability).

        Returns:
            Validated :class:`BlogArticle` instance.
        """
        # --- SEO ---
        raw_slug = self._seo.clean_slug(data.get("slug", make_slug(data.get("seo_title", pin.topic))))
        seo = SEOMetadata(
            seo_title=data.get("seo_title", pin.title),
            slug=raw_slug,
            meta_title=self._seo.normalise_meta_title(data.get("meta_title", pin.title)),
            meta_description=self._seo.normalise_meta_description(
                data.get("meta_description", pin.description[:160])
            ),
            focus_keyword=data.get("focus_keyword", pin.topic),
            secondary_keywords=to_str_list(data.get("secondary_keywords", [])),
            pinterest_keywords=to_str_list(data.get("pinterest_keywords", [])),
            category=data.get("category", "Animals"),
            tags=self._seo.validate_tags(to_str_list(data.get("tags", []))),
            internal_links=to_str_list(data.get("internal_links", [])),
        )

        # --- Markdown & HTML ---
        md_content = data.get("markdown_content", "")
        wc = word_count(md_content)
        if wc < MIN_WORD_COUNT:
            log.warning("Word count too low: %d (min %d)", wc, MIN_WORD_COUNT)

        html_content = self._converter.convert(
            md_content, title=seo.seo_title, slug=seo.slug
        )

        # --- Pinterest marketing ---
        pinterest = PinterestMarketing(
            pin_title=data.get("pinterest_pin_title", seo.seo_title),
            pin_description=data.get("pinterest_pin_description", seo.meta_description),
            hashtags=to_str_list(data.get("hashtags", [])),
            social_caption=data.get("social_caption", seo.meta_description),
        )

        # --- Images ---
        images = self._img.generate_prompts(pin, seo)

        # --- Hash ---
        content_hash = compute_hash(seo.seo_title, seo.slug, pin.topic)

        return BlogArticle(
            pin=pin,
            seo=seo,
            markdown_content=md_content,
            html_content=html_content,
            pinterest=pinterest,
            images=images,
            content_hash=content_hash,
            status=PublishStatus.PENDING,
        )
