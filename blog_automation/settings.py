"""
settings.py – Loads and validates all environment variables via Pydantic BaseSettings.
Provides a single `settings` singleton used everywhere in the project.
"""

from __future__ import annotations

from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """All configurable values, loaded from .env / environment."""

    # --- OpenAI ---
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", alias="OPENAI_MODEL")

    # --- Publishing ---
    publisher_mode: str = Field("static", alias="PUBLISHER_MODE")
    website_output_dir: str = Field("../generated_posts", alias="WEBSITE_OUTPUT_DIR")
    website_api: str = Field("", alias="WEBSITE_API")
    website_token: str = Field("", alias="WEBSITE_TOKEN")
    wordpress_url: str = Field("", alias="WORDPRESS_URL")
    wordpress_username: str = Field("", alias="WORDPRESS_USERNAME")
    wordpress_password: str = Field("", alias="WORDPRESS_PASSWORD")

    # --- Pinterest ---
    pinterest_profile_url: str = Field(
        "https://www.pinterest.com/YarnoodleAmigurumi/_created/",
        alias="PINTEREST_PROFILE_URL",
    )

    # --- Scheduler ---
    schedule_time: str = Field("09:00", alias="SCHEDULE_TIME")
    posts_per_day: int = Field(1, alias="POSTS_PER_DAY")

    @field_validator("publisher_mode")
    @classmethod
    def _validate_publisher_mode(cls, v: str) -> str:
        allowed = {"static", "wordpress", "api"}
        if v not in allowed:
            raise ValueError(f"PUBLISHER_MODE must be one of {allowed}, got '{v}'")
        return v

    model_config = {"extra": "ignore", "populate_by_name": True}


# ── Singleton ────────────────────────────────────────────────────────────────
settings = Settings()
