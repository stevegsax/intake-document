"""Entry point for the intake-document application."""

from typing import List, Optional

from src.intake_document.cli import app


def main(args: Optional[List[str]] = None) -> None:
    """Run the application CLI.

    Args:
        args: Command line arguments (defaults to sys.argv if None)
    """
    # Use typer app
    app(args)


if __name__ == "__main__":
    main()
