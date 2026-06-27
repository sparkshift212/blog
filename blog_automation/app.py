"""
app.py – CLI entry point for the Yarnoodle AI Blog Automation system.

Commands:
  run       – Full pipeline: scrape → generate → publish.
  generate  – Scrape Pinterest and generate article (no publish).
  publish   – Publish the latest generated article.
  schedule  – Start the daily scheduler.
  logs      – Tail the current day's log file.

Usage:
  python app.py run
  python app.py generate
  python app.py publish --slug crochet-fox-amigurumi
  python app.py schedule
  python app.py logs
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from config import GENERATED_DIR, LOGS_DIR
from database import article_repo
from logger import get_logger
from models import ArticleRecord, PublishStatus
from pipeline import Pipeline
from scheduler import start_scheduler
from settings import settings

app = typer.Typer(
    name="yarnoodle",
    help="Yarnoodle AI Blog Automation CLI",
    add_completion=False,
)
console = Console()
log = get_logger("app")


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def run() -> None:
    """Run the complete pipeline: scrape Pinterest → generate → publish."""
    console.rule("[bold cyan]Yarnoodle Blog Automation[/bold cyan]")
    console.print("[bold]Mode:[/bold] full pipeline")
    console.print(f"[bold]Publisher:[/bold] {settings.publisher_mode}\n")

    pipeline = Pipeline()
    try:
        article = pipeline.execute()
        if article:
            console.print(
                f"\n[green]✓ Published:[/green] [bold]{article.seo.seo_title}[/bold]"
            )
            console.print(f"  Slug: {article.seo.slug}")
            console.print(f"  URL:  {article.published_url}")
        else:
            console.print("[yellow]⚠ No article published (possible duplicate).[/yellow]")
    except Exception as exc:
        log.error("Pipeline failed: %s", exc, exc_info=True)
        console.print(f"[red]✗ Pipeline error: {exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command()
def generate() -> None:
    """Scrape Pinterest and generate the article (does NOT publish)."""
    console.rule("[bold cyan]Generate Only[/bold cyan]")

    pipeline = Pipeline(publish=False)
    try:
        article = pipeline.execute()
        if article:
            out_dir = Path(GENERATED_DIR)
            out_dir.mkdir(parents=True, exist_ok=True)
            slug = article.seo.slug
            md_file = out_dir / f"{slug}.md"
            md_file.write_text(article.markdown_content, encoding="utf-8")
            json_file = out_dir / f"{slug}.json"
            json_file.write_text(
                json.dumps(article.model_dump(exclude={"html_content", "markdown_content"}),
                           indent=2, default=str),
                encoding="utf-8",
            )
            console.print(f"[green]✓ Generated:[/green] {slug}")
            console.print(f"  Markdown → {md_file}")
            console.print(f"  Metadata → {json_file}")
        else:
            console.print("[yellow]⚠ Nothing generated (possible duplicate).[/yellow]")
    except Exception as exc:
        log.error("Generate failed: %s", exc, exc_info=True)
        console.print(f"[red]✗ Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command()
def publish(
    slug: Optional[str] = typer.Option(None, "--slug", help="Slug of generated article to publish"),
) -> None:
    """Publish a previously generated article to the website."""
    console.rule("[bold cyan]Publish[/bold cyan]")

    if slug:
        # Look for the generated files
        md_file = Path(GENERATED_DIR) / f"{slug}.md"
        json_file = Path(GENERATED_DIR) / f"{slug}.json"
        if not md_file.exists():
            console.print(f"[red]✗ No generated article found for slug: {slug}[/red]")
            raise typer.Exit(code=1)
        console.print(f"Publishing slug: [bold]{slug}[/bold]")
    else:
        # Default: run full pipeline in publish-only mode
        console.print("No slug provided – running full pipeline.")

    pipeline = Pipeline()
    try:
        article = pipeline.execute()
        if article:
            console.print(f"[green]✓ Published:[/green] {article.published_url}")
        else:
            console.print("[yellow]Nothing to publish.[/yellow]")
    except Exception as exc:
        log.error("Publish failed: %s", exc, exc_info=True)
        console.print(f"[red]✗ Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command()
def schedule() -> None:
    """Start the daily scheduler (runs continuously at the configured time)."""
    console.print(
        f"[bold cyan]Starting scheduler[/bold cyan] "
        f"– will run every day at [bold]{settings.schedule_time}[/bold]"
    )
    console.print("Press Ctrl+C to stop.\n")

    pipeline = Pipeline()
    start_scheduler(pipeline.execute)


@app.command()
def logs(
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show"),
) -> None:
    """Print the last N lines from today's log file."""
    log_dir = Path(LOGS_DIR)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.log"

    if not log_file.exists():
        console.print(f"[yellow]No log file found for today ({today}).[/yellow]")
        raise typer.Exit()

    lines = log_file.read_text(encoding="utf-8").splitlines()
    for line in lines[-tail:]:
        console.print(line)


@app.command()
def status() -> None:
    """Show the last 20 articles from the database."""
    records = article_repo.get_all(limit=20)
    if not records:
        console.print("[yellow]No articles in database yet.[/yellow]")
        return

    table = Table(title="Published Articles", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", min_width=30)
    table.add_column("Slug", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Date", style="dim")

    for i, rec in enumerate(records, 1):
        status_color = {
            PublishStatus.PUBLISHED: "green",
            PublishStatus.FAILED: "red",
            PublishStatus.SKIPPED: "yellow",
            PublishStatus.PENDING: "white",
        }.get(rec.status, "white")
        table.add_row(
            str(i),
            rec.title,
            rec.slug,
            f"[{status_color}]{rec.status.value}[/{status_color}]",
            rec.created_at.strftime("%Y-%m-%d"),
        )

    console.print(table)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
