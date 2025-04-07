"""Command-line interface for intake-document."""

# Standard library imports
import logging
from pathlib import Path
from typing import Optional

# Third-party imports
import click
import rich
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install as install_rich_traceback

# Local application imports
from intake_document.config import config
from intake_document.processor import DocumentProcessor
from intake_document.utils.exceptions import (
    ConfigError,
    DocumentError,
    FileTypeError,
    IntakeDocumentError,
    OCRError,
)
from intake_document.utils.logger import setup_logger

# Install rich traceback handler
install_rich_traceback(show_locals=True)

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
        "INFO",
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show verbose output"
    ),
) -> None:
    """Convert documents to markdown using Mistral.ai OCR."""
    # Setup logging
    setup_logger(log_level)
    logger = logging.getLogger(__name__)
    logger.debug("CLI initialized")

    try:
        logger.debug(
            "Command arguments: "
            + f"input_path={input_path}, "
            + f"output_dir={output_dir}, "
            + f"config_path={config_path}, "
            + f"log_level={log_level}, "
            + f"show_config={show_config}, "
            + f"verbose={verbose}"
        )

        # Adjust config if config path is specified
        if config_path:
            logger.info(f"Loading config from: {config_path}")
            # This would need implementation in config.py to load from a specific path
            # For now, just show a message that this isn't implemented yet
            console.print(
                "[yellow]Warning:[/] Custom config path not fully implemented yet"
            )

        # Show configuration if requested
        if show_config:
            logger.debug("Showing configuration")
            settings_dict = config.settings.model_dump()
            console.print(
                Panel.fit(
                    rich.pretty.Pretty(settings_dict),
                    title="Current Configuration",
                    border_style="blue",
                )
            )
            return

        # Process input files
        if input_path:
            # Override output_dir if specified
            if output_dir:
                logger.info(f"Setting output directory to: {output_dir}")
                config.settings.app.output_dir = str(output_dir)

            # Initialize processor
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Initializing document processor..."),
                transient=True,
            ) as progress:
                progress.add_task("init", total=None)
                processor = DocumentProcessor()

            if input_path.is_file():
                # Process a single file
                logger.info(f"Processing file: {input_path}")

                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        f"[bold blue]Processing [cyan]{input_path.name}[/cyan]..."
                    ),
                    transient=not verbose,
                ) as progress:
                    progress.add_task("processing", total=None)
                    result = processor.process_file(input_path)

                logger.info(f"Processed file: {input_path}")
                console.print(
                    f"[bold green]Success![/] Output saved to: {result}"
                )

            elif input_path.is_dir():
                # Process all files in directory
                logger.info(f"Processing directory: {input_path}")

                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        f"[bold blue]Processing files in [cyan]{input_path}[/cyan]..."
                    ),
                    transient=not verbose,
                ) as progress:
                    progress.add_task("processing", total=None)
                    results = processor.process_directory(input_path)

                logger.info(f"Processed directory: {input_path}")
                console.print(
                    f"[bold green]Success![/] Processed {len(results)} files. "
                    + f"Outputs saved to: {config.settings.app.output_dir}"
                )
            else:
                # Check if the path exists at all
                if not input_path.exists():
                    logger.error(f"Path does not exist: {input_path}")
                    console.print(
                        f"[bold red]Error:[/] {input_path} does not exist"
                    )
                else:
                    logger.error(f"Invalid path: {input_path}")
                    console.print(
                        f"[bold red]Error:[/] {input_path} is not a valid file or directory"
                    )
                raise typer.Exit(1)
        else:
            if not show_config:
                # If no input and not showing config, show help
                logger.debug("No action specified, showing help message")
                console.print(
                    "No input specified. Use --help to see available options."
                )
                raise typer.Exit(1)

    except FileNotFoundError as e:
        logger.exception("File not found:")
        console.print(f"[bold red]File not found:[/] {str(e)}")
        raise typer.Exit(1)

    except FileTypeError as e:
        logger.exception("Unsupported file type:")
        console.print(f"[bold red]Unsupported file type:[/] {e.message}")
        console.print(
            "[yellow]Tip:[/] Supported formats are: pdf, png, jpg, jpeg, tiff, docx"
        )
        raise typer.Exit(1)

    except OCRError as e:
        logger.exception("OCR processing error:")
        console.print(f"[bold red]OCR Error:[/] {e.message}")
        if e.detail:
            if verbose:
                console.print(f"[dim]{e.detail}[/dim]")
            logger.debug(f"OCR error detail: {e.detail}")
        raise typer.Exit(1)

    except ConfigError as e:
        logger.exception("Configuration error:")
        console.print(f"[bold red]Configuration Error:[/] {e.message}")
        if e.detail and verbose:
            console.print(f"[dim]{e.detail}[/dim]")
        raise typer.Exit(1)

    except DocumentError as e:
        logger.exception("Document processing error:")
        console.print(f"[bold red]Document Error:[/] {e.message}")
        if e.detail and verbose:
            console.print(f"[dim]{e.detail}[/dim]")
        raise typer.Exit(1)

    except IntakeDocumentError as e:
        # Catch any of our custom exceptions not caught by more specific handlers
        logger.exception("Application error:")
        console.print(f"[bold red]Error:[/] {e.message}")
        if e.detail and verbose:
            console.print(f"[dim]{e.detail}[/dim]")
        raise typer.Exit(1)

    except Exception as e:
        # Catch-all for any other exceptions
        logger.exception("Unexpected error:")
        console.print(
            "[bold red]Unexpected Error:[/] An unexpected error occurred"
        )
        console.print(f"[red]{str(e)}[/red]")

        if verbose:
            console.print("\n[bold]Traceback:[/]")
            console.print_exception(show_locals=True)

        raise typer.Exit(1)


if __name__ == "__main__":
    app()
