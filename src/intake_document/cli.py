"""Command-line interface for intake-document."""

import json
import logging
from pathlib import Path
from typing import Optional

import click
import rich
import typer
from rich.console import Console

from src.intake_document.config import config
from src.intake_document.processor import DocumentProcessor
from src.intake_document.utils.logger import setup_logger

# Create typer app
app = typer.Typer(
    name="intake-document",
    help="Convert documents into markdown format using Mistral.ai OCR",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    input_path: Optional[Path] = typer.Option(
        None, "--input", "-i", help="Path to input file or directory"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Output directory"
    ),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
    log_level: str = typer.Option(
        "ERROR",
        "--log-level",
        help="Set logging level",
        case_sensitive=False,
        click_type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ),
    ),
    show_config: bool = typer.Option(
        False, "--show-config", help="Show current configuration and exit"
    ),
) -> None:
    """Convert documents to markdown using Mistral.ai OCR."""
    # Setup logging
    setup_logger(log_level)
    logger = logging.getLogger(__name__)

    try:
        # Show configuration if requested
        if show_config:
            rich.print_json(json.dumps(config.settings.model_dump()))
            return

        # Process input files
        if input_path:
            # Override output_dir if specified
            if output_dir:
                config.settings.app.output_dir = str(output_dir)

            processor = DocumentProcessor()

            if input_path.is_file():
                # Process a single file
                result = processor.process_file(input_path)
                logger.info(f"Processed file: {input_path}")
                console.print(f"Output saved to: {result}")
            elif input_path.is_dir():
                # Process all files in directory
                results = processor.process_directory(input_path)
                logger.info(f"Processed directory: {input_path}")
                console.print(
                    f"Processed {len(results)} files. Outputs saved to: {config.settings.app.output_dir}"
                )
            else:
                console.print(
                    f"[bold red]Error:[/] {input_path} is not a valid file or directory"
                )
                raise typer.Exit(1)
        else:
            if not show_config:
                # If no input and not showing config, show help
                console.print(
                    "No input specified. Use --help to see available options."
                )
                raise typer.Exit(1)

    except Exception as e:
        logger.exception("An error occurred:")
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
