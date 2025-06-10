"""
Logging configuration for Hive reward claiming scripts.
Provides consistent logging setup across all modules.
"""

import logging
from typing import Optional

from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback


def setup_logging(level: Optional[int] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Optional logging level to set. If None, defaults to INFO.

    Returns:
        The configured logger instance.
    """
    # Get the root logger
    logger = logging.getLogger()

    # Clear any existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Install rich traceback handler for enhanced tracebacks
    install_rich_traceback()

    # Configure basic logging with RichHandler
    logging.basicConfig(
        level=level or logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_time=True)],
    )

    return logger


def set_debug_logging(logger: logging.Logger) -> None:
    """
    Enable debug logging for the given logger.

    Args:
        logger: The logger to configure.
    """
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled.")
