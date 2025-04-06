# intake-document

The purpose of this program is to convert documents into markdown format using the OCR capabilities provided by [Mistral.ai](https://mistral.ai/). 

- Use `batch` mode to save cost
- Upload the document to Mistral as a separate step
- Maintain document structure and hierarchy
- Preserve formatting like headers, paragraphs, lists and tables
- Returnr esults in markdown format for easy parsing and rendering
- Handle complex layouts including multi-column text and mixed content
- Maintain non-text images as images that can be downloaded separately

The OCR library is documented here: https://docs.mistral.ai/capabilities/document/

# Configuration

The application uses the XDG Base Directory specification for configuration:

- Configuration: `~/.config/intake-document/init.cfg`
- Data: `~/.local/share/intake-document/`
- Cache: `~/.cache/intake-document/`
- State: `~/.local/state/intake-document/`

# Usage

## Command Line Arguments

```
-i, --input PATH            Path to input file or directory
-o, --output-dir PATH       Output directory (default: ./output)
-c, --config PATH           Path to config file 
--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL} Set logging level (default: ERROR)
--show-config               Show current configuration and exit
-h, --help                  Show help message and exit
```
# Libraries

- [mistralai](https://github.com/mistralai/client-python) is the official python library provided by Le Mistral
- [pydantic](https://docs.pydantic.dev/latest/) data validation library
- [rich](https://rich.readthedocs.io/en/latest/) is a Python library for writing rich text (with color and style) to the terminal, and for displaying advanced content such as tables, markdown, and syntax highlighted code.
- [structlog](https://www.structlog.org/en/stable/) logging
- [cfg](https://docs.red-dove.com/cfg/) for configuration management
- [xdg-base-dirs](https://github.com/srstevenson/xdg-base-dirs) XDG Base Directory specification
