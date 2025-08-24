"""Notification helpers for Alchohalt.

These are placeholders for future scheduling logic. On systems where
APScheduler or desktop notification libraries are unavailable, the
functions simply log their intent.
"""
from __future__ import annotations

from typing import Optional
import logging


logger = logging.getLogger(__name__)


def schedule(hour: int, minute: int) -> None:
    """Schedule a daily reminder at the given hour and minute.

    This is a stub; real scheduling will hook into APScheduler or
    platform-specific notification APIs.
    """
    logger.info("schedule reminder at %02d:%02d", hour, minute)


def cancel() -> None:
    """Cancel any scheduled reminder (stub)."""
    logger.info("cancel reminder")
