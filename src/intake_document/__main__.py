"""Entry point for the intake-document application."""

import logging
from typing import List, Optional

# Local application imports
from intake_document.cli import app
from intake_document.utils.logger import setup_logger


def main(args: Optional[List[str]] = None) -> None:
    """Run the application CLI.

    Args:
        args: Command line arguments (defaults to sys.argv if None)
    """
    # Set up default logging
    setup_logger("INFO")
    logger = logging.getLogger(__name__)
    logger.debug("Starting application from __main__.py")

    try:
        # Use typer app
        app(args)
        logger.debug("Application completed successfully")
    except Exception:
        logger.exception("Application failed with an error")
        raise


if __name__ == "__main__":
    main()
