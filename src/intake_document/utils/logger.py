"""Logging configuration for the application."""

import logging
from typing import Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    level: str = "ERROR", log_to_file: Optional[str] = None
) -> None:
    """Set up application logging with structlog and rich.

    Args:
        level: The log level to use
        log_to_file: Optional path to a log file
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.ERROR)

    # Configure rich handler
    rich_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        console=Console(stderr=True),
        tracebacks_show_locals=True,
    )

    # Basic logging configuration
    handlers = [rich_handler]

    # Add file handler if requested
    if log_to_file:
        file_handler = logging.FileHandler(log_to_file)
        handlers.append(file_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set basic logging configuration
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )
