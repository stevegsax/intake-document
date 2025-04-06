# intake-document

A Python application to convert documents into markdown format using the OCR capabilities provided by [Mistral.ai](https://mistral.ai/).

## Features

- Uses Mistral.ai's OCR API to analyze document content
- Processes document in `batch` mode to save cost
- Uploads documents to Mistral as a separate step
- Maintains document structure and hierarchy
- Preserves formatting including:
  - Headers and subheadings
  - Paragraphs
  - Lists (ordered and unordered)
  - Tables with headers and data
- Returns results in clean markdown format for easy parsing and rendering
- Handles complex layouts including multi-column text and mixed content
- Maintains non-text images as references that can be downloaded separately

## Installation

### Requirements

- Python 3.10 or higher
- Mistral.ai API key

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/intake-document.git
cd intake-document

# Install using pip in development mode
pip install -e .
```

### Environment setup

Set your Mistral.ai API key as an environment variable:

```bash
export MISTRAL_API_KEY="your-api-key-here"
```

## Configuration

The application follows the XDG Base Directory specification for configuration:

- Configuration: `~/.config/intake-document/init.cfg`
- Data: `~/.local/share/intake-document/`
- Cache: `~/.cache/intake-document/`
- State: `~/.local/state/intake-document/`

### Configuration file example

```ini
[mistral]
api_key = your-api-key-here
batch_size = 5
max_retries = 3
timeout = 60

[app]
output_dir = ./output
log_level = INFO
```

## Usage

The application can be used as a command-line tool to process documents:

```bash
# Process a single file
intake-document --input path/to/document.pdf --output-dir path/to/output

# Process all documents in a directory
intake-document --input path/to/document/folder --output-dir path/to/output

# Show the current configuration
intake-document --show-config

# Display help
intake-document --help
```

### Command Line Arguments

```
-i, --input PATH                  Path to input file or directory
-o, --output-dir PATH             Output directory (default: ./output)
-c, --config PATH                 Path to config file 
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}  Set logging level (default: ERROR)
--show-config                     Show current configuration and exit
-h, --help                        Show help message and exit
```

## Project Structure

```
intake-document/
├── src/                          # Source code
│   └── intake_document/         
│       ├── __init__.py           # Package initialization
│       ├── __main__.py           # Entry point
│       ├── cli.py                # Command-line interface
│       ├── config.py             # Configuration management
│       ├── ocr.py                # Mistral OCR integration
│       ├── processor.py          # Document processing logic
│       ├── renderer.py           # Markdown rendering
│       ├── models/               # Data models
│       │   ├── document.py       # Document structure models
│       │   └── settings.py       # Application settings models
│       └── utils/                # Utility modules
│           ├── logger.py         # Logging configuration
│           └── xdg.py            # XDG path utilities
├── tests/                        # Unit tests
├── docs/                         # Documentation
├── pyproject.toml                # Project metadata and configuration
└── README.md                     # This file
```

## Dependencies

- [mistralai](https://github.com/mistralai/client-python) - Official Python library for Mistral.ai
- [pydantic](https://docs.pydantic.dev/latest/) - Data validation and settings management
- [rich](https://rich.readthedocs.io/en/latest/) - Rich text and formatting for the terminal
- [structlog](https://www.structlog.org/en/stable/) - Structured logging
- [typer](https://typer.tiangolo.com/) - CLI creation with type hints
- [configparser](https://docs.python.org/3/library/configparser.html) - Configuration file parsing
- [xdg-base-dirs](https://github.com/srstevenson/xdg-base-dirs) - XDG Base Directory specification

## Development

### Testing

```bash
# Install development dependencies
pip install pytest

# Run tests
pytest
```

### Formatting and Linting

```bash
# Install development tools
pip install ruff mypy

# Run formatter
ruff format src/ tests/

# Run linter
ruff check src/ tests/

# Run type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## API Documentation

The Mistral.ai OCR API is documented at: https://docs.mistral.ai/capabilities/document/
