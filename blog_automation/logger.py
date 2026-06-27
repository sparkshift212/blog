"""
logger.py – Structured logging for every subsystem.
Creates dated log files in /logs and streams coloured output to the console.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows to avoid cp1252 encoding crashes
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.logging import RichHandler

from config import LOGS_DIR

# ── Ensure log directory exists ───────────────────────────────────────────────
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

_LOG_FILE = Path(LOGS_DIR) / f"{datetime.now().strftime('%Y-%m-%d')}.log"

_LOGGERS: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Return (or create) a named logger writing to both file and console.

    Args:
        name: Logical name for the component (e.g. "pinterest", "ai_writer").

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # -- Rich console handler ---------------------------------------------------
    _console = Console(stderr=True, highlight=False, markup=True)
    console_handler = RichHandler(
        console=_console,
        show_time=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)

    # -- File handler (rotating by day) ----------------------------------------
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    _LOGGERS[name] = logger
    return logger


# Module-level convenience logger
log = get_logger("core")
