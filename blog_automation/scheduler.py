"""
scheduler.py – Daily job scheduler using the ``schedule`` library.

Runs the full pipeline once per day at the configured time.
Supports graceful shutdown via KeyboardInterrupt.
"""

from __future__ import annotations

import signal
import time
from typing import Callable

import schedule

from config import DEFAULT_SCHEDULE_TIME
from logger import get_logger
from settings import settings

log = get_logger("scheduler")

_running = True


def _signal_handler(signum: int, _frame: object) -> None:
    """Handle SIGTERM / SIGINT for graceful shutdown."""
    global _running
    log.info("Received signal %d – shutting down scheduler.", signum)
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def start_scheduler(job: Callable[[], None]) -> None:
    """Start the blocking scheduler that runs *job* daily.

    The schedule time is read from ``settings.schedule_time``
    (defaults to ``09:00``).

    Args:
        job: Callable to invoke on each scheduled trigger.
    """
    run_time = settings.schedule_time or DEFAULT_SCHEDULE_TIME
    log.info("Scheduler starting – job will run every day at %s", run_time)

    schedule.every().day.at(run_time).do(_safe_run, job)

    while _running:
        schedule.run_pending()
        time.sleep(30)

    log.info("Scheduler stopped.")


def _safe_run(job: Callable[[], None]) -> None:
    """Execute *job* with error isolation so the scheduler keeps running."""
    try:
        log.info("Scheduler: triggering daily job.")
        job()
    except Exception as exc:  # noqa: BLE001
        log.error("Scheduled job raised an exception: %s", exc, exc_info=True)
