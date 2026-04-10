"""Placeholder hook for user-defined behavior when OCR text is accepted."""

from __future__ import annotations

import logging

from .detector import AcceptedTextEvent


logger = logging.getLogger(__name__)


def handle_accepted_text(event: AcceptedTextEvent) -> None:
    """Hook called whenever new OCR text has been accepted."""

    logger.info(
        "Action hook received %d characters of accepted text.",
        len(event.normalized_text),
    )
