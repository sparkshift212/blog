"""
services/images.py – Generates image prompt objects for the AI-written article.
The actual images are NOT generated here (that requires a separate image API).
Instead, we produce structured :class:`ImageAsset` objects that can be:
  1. Handed to DALL-E / Stable Diffusion via another service.
  2. Embedded as AI prompt text in the blog for later production.
"""

from __future__ import annotations

from typing import List

from models import ImageAsset, PinData, SEOMetadata
from logger import get_logger

log = get_logger("images")


class ImageService:
    """Generates descriptive image prompts based on the article content."""

    def generate_prompts(
        self, pin: PinData, seo: SEOMetadata
    ) -> List[ImageAsset]:
        """Produce a list of image prompts for the article.

        The list includes:
        - A featured hero image.
        - A Pinterest-optimised vertical pin image.
        - 5 supporting in-article step/lifestyle images.

        Args:
            pin: The source Pinterest pin data.
            seo: The SEO metadata for the article.

        Returns:
            List of :class:`ImageAsset` instances ready to be embedded.
        """
        topic = pin.topic
        keyword = seo.focus_keyword
        style_prefix = (
            "Soft, warm, cozy photography style. "
            "Pastel colour palette. Rustic wooden surface. Natural window light."
        )

        assets: List[ImageAsset] = [
            # 1 – Featured hero
            ImageAsset(
                label="featured",
                prompt=(
                    f"{style_prefix} A beautifully lit, high-resolution photo of a completed "
                    f"handmade crochet {topic} amigurumi sitting on a wooden table surrounded "
                    f"by balls of yarn and a crochet hook. Premium Pinterest-worthy aesthetic."
                ),
                alt_text=f"Completed crochet {topic} amigurumi on a wooden table",
            ),
            # 2 – Pinterest vertical pin
            ImageAsset(
                label="pinterest_pin",
                prompt=(
                    f"Vertical 2:3 ratio Pinterest pin image. Bright, clean, white background. "
                    f"Large bold readable title text overlay: '{seo.seo_title}'. "
                    f"A cute crochet {topic} amigurumi centred in the image. "
                    f"Terracotta and sage green colour accents. Premium crochet blog aesthetic."
                ),
                alt_text=f"Pinterest pin for {seo.seo_title}",
            ),
            # 3 – Materials flat lay
            ImageAsset(
                label="materials",
                prompt=(
                    f"{style_prefix} Flat lay of crochet materials: yarn skeins, a 3.5mm "
                    f"crochet hook, safety eyes, fiberfill stuffing, and scissors arranged "
                    f"artfully on a cream linen background."
                ),
                alt_text=f"Materials needed for crochet {topic} amigurumi pattern",
            ),
            # 4 – Hands crocheting
            ImageAsset(
                label="in_progress",
                prompt=(
                    f"{style_prefix} Close-up of hands crocheting a small orange/beige yarn "
                    f"amigurumi piece. Shallow depth of field. Warm golden hour light."
                ),
                alt_text=f"Hands crocheting an amigurumi {topic} step by step",
            ),
            # 5 – Finished product lifestyle
            ImageAsset(
                label="lifestyle",
                prompt=(
                    f"{style_prefix} A finished crochet {topic} amigurumi displayed next to a "
                    f"warm cup of coffee and an open notebook on a cozy blanket. "
                    f"Lifestyle photography, homey atmosphere."
                ),
                alt_text=f"Crochet {topic} amigurumi in a cozy lifestyle setting",
            ),
            # 6 – Step-by-step collage
            ImageAsset(
                label="steps_collage",
                prompt=(
                    f"{style_prefix} A 4-panel collage showing the stages of crocheting a "
                    f"{topic} amigurumi: 1) magic ring, 2) body forming, 3) stuffing, "
                    f"4) finished result. Clean, editorial style."
                ),
                alt_text=f"Step-by-step crochet {topic} amigurumi process photos",
            ),
            # 7 – Focus on details
            ImageAsset(
                label="detail_shot",
                prompt=(
                    f"Extreme close-up macro photograph of the fine crochet stitches on a "
                    f"handmade {topic} amigurumi, showing the texture and craftsmanship. "
                    f"Soft focus background."
                ),
                alt_text=f"Close-up of crochet stitches on {topic} amigurumi",
            ),
        ]

        log.debug("Generated %d image prompts for topic='%s'", len(assets), topic)
        return assets
