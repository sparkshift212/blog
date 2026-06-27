"""
database.py – Repository layer wrapping SQLite via the standard library.
Uses the Repository pattern so the rest of the code is storage-agnostic.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from config import DB_PATH
from logger import get_logger
from models import ArticleRecord, PublishStatus

log = get_logger("database")


# ── Database initialisation ───────────────────────────────────────────────────

def _init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't already exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT    NOT NULL,
            slug         TEXT    NOT NULL UNIQUE,
            topic        TEXT    NOT NULL,
            focus_keyword TEXT   NOT NULL,
            category     TEXT    NOT NULL DEFAULT '',
            pinterest_url TEXT   NOT NULL DEFAULT '',
            content_hash TEXT    NOT NULL UNIQUE,
            status       TEXT    NOT NULL DEFAULT 'pending',
            published_url TEXT   NOT NULL DEFAULT '',
            published_at  TEXT,
            created_at   TEXT    NOT NULL
        )
        """
    )
    conn.commit()


@contextmanager
def _get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields a connected :class:`sqlite3.Connection`.

    Ensures the storage directory exists and the schema is initialised on
    first use.

    Yields:
        An open :class:`sqlite3.Connection` with ``row_factory`` set.
    """
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        _init_db(conn)
        yield conn
    finally:
        conn.close()


# ── Repository ────────────────────────────────────────────────────────────────

class ArticleRepository:
    """CRUD operations for :class:`ArticleRecord`.

    All public methods open and close their own connection, making the class
    safe for use across threads (one connection per call).
    """

    # -- Write operations ------------------------------------------------------

    def insert(self, record: ArticleRecord) -> int:
        """Persist a new article record.

        Args:
            record: Populated :class:`ArticleRecord` to save.

        Returns:
            The auto-assigned database row ID.
        """
        with _get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO articles
                    (title, slug, topic, focus_keyword, category,
                     pinterest_url, content_hash, status,
                     published_url, published_at, created_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.title,
                    record.slug,
                    record.topic,
                    record.focus_keyword,
                    record.category,
                    record.pinterest_url,
                    record.content_hash,
                    record.status.value,
                    record.published_url,
                    record.published_at.isoformat() if record.published_at else None,
                    record.created_at.isoformat(),
                ),
            )
            conn.commit()
            row_id: int = cursor.lastrowid or 0
            log.debug("Inserted article id=%d slug=%s", row_id, record.slug)
            return row_id

    def update_status(
        self,
        slug: str,
        status: PublishStatus,
        published_url: str = "",
        published_at: Optional[datetime] = None,
    ) -> None:
        """Update the publish status of an article identified by *slug*.

        Args:
            slug: URL slug (unique identifier).
            status: New :class:`PublishStatus`.
            published_url: Live URL if successfully published.
            published_at: Timestamp of publication.
        """
        with _get_conn() as conn:
            conn.execute(
                """
                UPDATE articles
                SET status=?, published_url=?, published_at=?
                WHERE slug=?
                """,
                (
                    status.value,
                    published_url,
                    published_at.isoformat() if published_at else None,
                    slug,
                ),
            )
            conn.commit()
            log.debug("Updated status slug=%s status=%s", slug, status.value)

    # -- Read operations -------------------------------------------------------

    def exists_by_slug(self, slug: str) -> bool:
        """Return ``True`` if an article with *slug* already exists."""
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM articles WHERE slug=?", (slug,)
            ).fetchone()
            return row is not None

    def exists_by_hash(self, content_hash: str) -> bool:
        """Return ``True`` if an article with *content_hash* already exists."""
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM articles WHERE content_hash=?", (content_hash,)
            ).fetchone()
            return row is not None

    def exists_by_topic(self, topic: str) -> bool:
        """Return ``True`` if a very similar topic has been published."""
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM articles WHERE LOWER(topic)=?", (topic.lower(),)
            ).fetchone()
            return row is not None

    def get_all(self, limit: int = 50) -> List[ArticleRecord]:
        """Retrieve the most recent *limit* article records.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            List of :class:`ArticleRecord` sorted newest-first.
        """
        with _get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM articles ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [_row_to_record(r) for r in rows]

    def get_by_slug(self, slug: str) -> Optional[ArticleRecord]:
        """Fetch a single record by slug, or ``None`` if not found."""
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM articles WHERE slug=?", (slug,)
            ).fetchone()
            return _row_to_record(row) if row else None


# ── Helper ────────────────────────────────────────────────────────────────────

def _row_to_record(row: sqlite3.Row) -> ArticleRecord:
    """Convert a :class:`sqlite3.Row` to an :class:`ArticleRecord`."""
    return ArticleRecord(
        id=row["id"],
        title=row["title"],
        slug=row["slug"],
        topic=row["topic"],
        focus_keyword=row["focus_keyword"],
        category=row["category"],
        pinterest_url=row["pinterest_url"],
        content_hash=row["content_hash"],
        status=PublishStatus(row["status"]),
        published_url=row["published_url"] or "",
        published_at=(
            datetime.fromisoformat(row["published_at"]) if row["published_at"] else None
        ),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# ── Module-level singleton ────────────────────────────────────────────────────
article_repo = ArticleRepository()
