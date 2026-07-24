"""Structured logging setup — owned by Contributor E."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Configure root logging once at application startup."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
