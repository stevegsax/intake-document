# Product Specification: intake-document

## Overview

**intake-document** is a Python command-line application that converts documents into structured markdown format using Mistral.ai's OCR capabilities. The application processes various document formats and maintains document structure while converting to clean, parseable markdown.

## Current Implementation Features

### Core Functionality

#### Document Processing
- **Single File Processing**: Process individual documents through OCR and conversion pipeline
- **Batch Directory Processing**: Process all supported documents in a directory with progress tracking
- **Format Support**: PDF, PNG, JPG, JPEG, TIFF, DOCX document types
- **Structure Preservation**: Maintains document hierarchy, formatting, and layout during conversion

#### OCR Integration
- **Mistral.ai API Integration**: Uses Mistral.ai's OCR API for document analysis
- **Document Upload**: Uploads documents to Mistral for processing
- **Structured Extraction**: Extracts document elements including:
  - Headers and subheadings (with level hierarchy)
  - Paragraphs
  - Lists (ordered and unordered)
  - Tables with headers and data rows
  - Image references with captions
- **Batch Processing**: Configurable batch size for cost optimization
- **Error Handling**: Robust error handling for API failures and timeouts

#### Markdown Rendering
- **Clean Output**: Generates clean, standardized markdown format
- **Structure Maintenance**: Preserves document hierarchy in markdown format
- **Element Support**: Renders all extracted elements appropriately:
  - Headings (`#`, `##`, etc.)
  - Paragraphs
  - Bulleted and numbered lists
  - Tables with proper formatting
  - Image references

### Configuration System

#### XDG Base Directory Compliance
- **Configuration**: `~/.config/intake-document/init.cfg`
- **Data Storage**: `~/.local/share/intake-document/`
- **Cache**: `~/.cache/intake-document/`
- **State**: `~/.local/state/intake-document/`

#### Configuration Options
- **Mistral API Settings**:
  - API key configuration
  - Batch size (default: 5)
  - Max retries (default: 3)
  - Timeout (default: 60s)
- **Application Settings**:
  - Output directory path
  - Log level configuration

#### Environment Variable Support
- `MISTRAL_API_KEY`: API key for Mistral.ai service
- `INTAKE_DOCUMENT_OUTPUT_DIR`: Override default output directory
- `INTAKE_DOCUMENT_LOG_LEVEL`: Set logging verbosity

### Command-Line Interface

#### Core Commands
```bash
# Process single file
intake-document --input path/to/document.pdf --output-dir path/to/output

# Process directory
intake-document --input path/to/documents/ --output-dir path/to/output

# Show current configuration
intake-document --show-config
```

#### Command-Line Options
- `-i, --input PATH`: Input file or directory path
- `-o, --output-dir PATH`: Output directory (default: ./output)
- `-c, --config PATH`: Custom config file path
- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Logging level
- `--show-config`: Display current configuration
- `-v, --verbose`: Show verbose output
- `-h, --help`: Help information

### Architecture Components

#### Data Models (Pydantic)

##### Core Document Models
**DocumentInstance** (`BaseModel`) - Represents a file instance:
```python
class DocumentInstance(BaseModel):
    path: Path                              # File system path to document
    file_type: DocumentType                 # Document format type
    checksum: str                           # SHA-512 hash of file content
    file_size: int                          # File size in bytes
    last_modified: datetime                 # File modification timestamp
    processed_at: Optional[datetime] = None # When this instance was processed
```

**Document** (`BaseModel`) - Represents processed content:
```python
class Document(BaseModel):
    checksum: str                           # SHA-512 hash linking to instances
    elements: List[DocumentElement] = []    # Extracted document elements
    markdown: Optional[str] = None          # Generated markdown content
    processed_at: datetime                  # When OCR processing completed
```

**DocumentType** (`str`, `Enum`):
```python
class DocumentType(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    DOCX = "docx"
```

**ElementType** (`str`, `Enum`):
```python
class ElementType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
```

##### Document Element Models
**DocumentElement** (`BaseModel`) - Base class:
```python
class DocumentElement(BaseModel):
    element_type: ElementType               # Type identifier for element
    element_index: int                      # Position in original document (0-based)
```

**TextElement** (`DocumentElement`):
```python
class TextElement(DocumentElement):
    element_type: str = "text"              # Fixed type identifier
    content: str                            # Text content
    level: Optional[int] = None             # Heading level (1-6) if applicable
    is_list_item: bool = False             # True if element is a list item
```

**TableElement** (`DocumentElement`):
```python
class TableElement(DocumentElement):
    element_type: str = "table"             # Fixed type identifier
    headers: List[str]                      # Column headers
    rows: List[List[str]]                   # Table data rows
```

**ImageElement** (`DocumentElement`):
```python
class ImageElement(DocumentElement):
    element_type: str = "image"             # Fixed type identifier
    image_id: str                           # Unique image identifier
    caption: Optional[str] = None           # Image caption/alt text
```

##### Configuration Models
**Settings** (`BaseModel`) - Main configuration container:
```python
class Settings(BaseModel):
    mistral: MistralConfig = Field(default_factory=MistralConfig)
    app: AppConfig = Field(default_factory=AppConfig)
```

**MistralConfig** (`BaseModel`) - API configuration:
```python
class MistralConfig(BaseModel):
    api_key: Optional[str] = None           # Mistral.ai API key
    batch_size: int = Field(default=5, ge=1, le=20)      # Batch processing size
    max_retries: int = Field(default=3, ge=0, le=10)     # API retry attempts
    timeout: int = Field(default=60, ge=10, le=300)      # Request timeout (seconds)
```

**AppConfig** (`BaseModel`) - Application settings:
```python
class AppConfig(BaseModel):
    output_dir: str = "./output"            # Default output directory
    log_level: str = "ERROR"                # Logging verbosity level
```

##### Error Models
**ErrorCode** (`Enum`) - Structured error classification:
```python
class ErrorCode(Enum):
    # General errors (1000-1999)
    UNKNOWN_ERROR = 1000
    
    # Configuration errors (2000-2999)
    CONFIG_NOT_FOUND = 2000
    CONFIG_INVALID = 2001
    CONFIG_PERMISSION_DENIED = 2002
    
    # XDG errors (3000-3999)
    XDG_PATH_NOT_FOUND = 3000
    XDG_PERMISSION_DENIED = 3001
    
    # File errors (4000-4999)
    FILE_NOT_FOUND = 4000
    FILE_PERMISSION_DENIED = 4001
    FILE_TYPE_UNSUPPORTED = 4002
    FILE_TOO_LARGE = 4003
    FILE_CORRUPT = 4004
    
    # Document processing errors (5000-5999)
    DOCUMENT_PARSE_ERROR = 5000
    DOCUMENT_ELEMENT_ERROR = 5001
    DOCUMENT_STRUCTURE_ERROR = 5002
    
    # OCR errors (6000-6999)
    OCR_EXTRACTION_ERROR = 6000
    OCR_TEXT_EXTRACTION_ERROR = 6001
    OCR_TABLE_EXTRACTION_ERROR = 6002
    OCR_IMAGE_EXTRACTION_ERROR = 6003
    
    # API errors (7000-7999)
    API_CONNECTION_ERROR = 7000
    API_AUTHENTICATION_ERROR = 7001
    API_QUOTA_ERROR = 7002
    API_TIMEOUT_ERROR = 7003
    API_RESPONSE_ERROR = 7004
    
    # Rendering errors (8000-8999)
    RENDER_MARKDOWN_ERROR = 8000
    RENDER_TABLE_ERROR = 8001
    RENDER_IMAGE_ERROR = 8002
```

**IntakeDocumentError** - Base exception class:
```python
class IntakeDocumentError(Exception):
    def __init__(
        self, 
        message: str = "An error occurred", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR
    ):
        self.message = message              # Primary error message
        self.detail = detail                # Additional error details
        self.error_code = error_code        # Structured error classification
```

#### Model Validation Features
- **Type Safety**: Full type annotation with runtime validation
- **Field Constraints**: Validation rules for numeric ranges and string formats
- **Default Values**: Sensible defaults for optional configuration parameters
- **Enum Validation**: Strict validation of allowed values for document types and error codes
- **Nested Models**: Hierarchical configuration structure with automatic validation
- **Error Context**: Rich error information with codes, messages, and additional details

#### Processing Pipeline
1. **Input Validation**: File type checking and path validation
2. **Document Upload**: Secure upload to Mistral.ai API
3. **OCR Processing**: Document analysis and element extraction
4. **Markdown Conversion**: Structured rendering to markdown format
5. **Output Generation**: File writing with error handling

#### Error Handling
- **Custom Exceptions**: Specific exception types for different error categories
  - `ConfigError`: Configuration-related issues
  - `DocumentError`: Document processing failures
  - `FileTypeError`: Unsupported file format errors
  - `OCRError`: API and processing errors
  - `APIError`: Network and service communication errors
- **Graceful Degradation**: Continues processing other files when individual files fail
- **Detailed Logging**: Comprehensive logging with configurable verbosity

### Quality Assurance

#### Code Quality
- **Type Hints**: Full type annotation coverage
- **Pydantic Validation**: Data model validation and serialization
- **Structured Logging**: Comprehensive logging with structured output
- **Error Recovery**: Robust error handling and recovery mechanisms

#### Development Tools
- **Formatting**: Ruff code formatting (79 character line limit)
- **Linting**: Ruff linting with E, F, B, I rule sets
- **Type Checking**: MyPy static type analysis
- **Testing**: pytest framework with coverage reporting

## Technical Requirements

### Runtime Dependencies
- Python 3.10+
- mistralai (Mistral.ai Python client)
- pydantic (data validation)
- rich (terminal formatting)
- structlog (structured logging)
- typer (CLI framework)
- configparser (configuration management)
- xdg-base-dirs (XDG specification compliance)

### Development Dependencies
- pytest (testing framework)
- ruff (formatting and linting)
- mypy (type checking)

## Current Limitations

### Implementation Status
- **OCR Processing**: Currently uses placeholder implementation for document upload and processing
- **API Integration**: Mistral.ai API calls are stubbed with sample data structure
- **Batch Processing**: Basic batch processing without advanced queue management
- **Database Storage**: No persistent storage of document metadata or processing history

### Known Constraints
- **File Size**: Large files (>10MB) may have performance implications
- **Network Dependency**: Requires internet connection for Mistral.ai API access
- **API Rate Limits**: Subject to Mistral.ai API rate limiting and quotas
- **Format Support**: Limited to specific document formats supported by Mistral.ai

## Mistral.ai API Integration Details

### JSON Output Capabilities

#### JSON Mode Configuration
- **Basic JSON Mode**: Set `response_format = {"type": "json_object"}`
- **Schema-Based Output**: Direct output to Pydantic/Zod schemas (`response_format=YourSchema`)
- **Document-as-Prompt**: Query documents for specific information with structured JSON responses

#### OCR-Specific Annotation Features

**BBox Annotation**: Extracts structured information about specific regions/elements
- Chart and figure analysis with bounding box coordinates
- Image region descriptions and categorization
- Visual element metadata extraction

**Document Annotation**: Extracts document-level metadata
- Document language detection
- Section headings and chapter titles
- URL extraction and categorization
- Limited to documents with 8 pages or fewer

#### Structured Element Extraction
The API supports extracting document elements in reading order with full structural preservation:
- **Text Elements**: Headings (with levels 1-6), paragraphs, list items
- **Table Elements**: Complete table structure with headers and data rows
- **Image Elements**: Bounding box coordinates, descriptions, and downloadable references
- **Ordering**: All elements include `element_index` for maintaining document order

### Asset Download Capabilities
- **Images**: Download via image_id or bounding box coordinates
- **Tables**: Export as CSV, Excel, or structured JSON
- **Text Content**: Preserve markdown formatting and hierarchy
- **Complete Reconstruction**: Reassemble documents maintaining original order

## Future Enhancement Opportunities

### Planned Improvements
- Complete Mistral.ai API integration implementation
- Advanced batch processing with queue management
- Document metadata persistence with checksum-based deduplication
- Enhanced error recovery and retry mechanisms
- Additional output formats beyond markdown
- Local OCR fallback options
- Web-based interface
- Document comparison and versioning capabilities
- Asset download and management system

## API Integration Examples

### Complete Document Structure Extraction

#### Custom Pydantic Schema
```python
from pydantic import BaseModel
from typing import List, Optional, Union

class DocumentElement(BaseModel):
    element_type: str  # "text", "table", "image", "heading"
    element_index: int  # Position in document
    content: Optional[str] = None
    
class TextElement(DocumentElement):
    element_type: str = "text"
    content: str
    heading_level: Optional[int] = None  # 1-6 for headings
    is_list_item: bool = False

class TableElement(DocumentElement):
    element_type: str = "table"
    headers: List[str]
    rows: List[List[str]]
    
class ImageElement(DocumentElement):
    element_type: str = "image"
    image_id: str
    bbox: List[float]  # [x1, y1, x2, y2]
    description: Optional[str] = None
    
class DocumentStructure(BaseModel):
    elements: List[Union[TextElement, TableElement, ImageElement]]
    page_count: int
    language: str
```

#### API Request Example
```python
# Complete document extraction with structured output
response = mistral_client.chat.complete(
    model="mistral-large-latest",
    messages=[{
        "role": "user", 
        "content": "Extract all document elements in reading order and return as structured JSON"
    }],
    response_format=DocumentStructure,
    # Attach document file
)
```

### Document-as-Prompt Examples

#### Extract All Tables
```python
prompt = """
Extract all tables from this document and return as JSON array. 
For each table, include:
- Position in document (element_index)
- Headers
- All rows of data
- Any table title or caption
"""
```

#### Extract All Images
```python
prompt = """
Extract all images, charts, and figures from this document.
For each image, provide:
- Position in document (element_index) 
- Bounding box coordinates
- Image description/caption
- Image type (photo, chart, diagram, etc.)
"""
```

#### Complete Structured Extraction
```python
prompt = """
Extract the complete document structure in reading order:
- All text content with heading levels
- All tables with full data
- All images with descriptions and positions
- Maintain original document order using element_index
Return as structured JSON.
"""
```

### Asset Processing Workflow

#### Image Download and Management
```python
# Extract images using bbox annotations
for element in response.elements:
    if element.element_type == "image":
        # Download image using provided image_id or bbox
        image_url = f"https://api.mistral.ai/documents/{document_id}/images/{element.image_id}"
        # Save locally with element_index for ordering
        save_path = f"images/{element.element_index:03d}_{element.image_id}.png"
```

#### Table Export
```python
import pandas as pd

for element in response.elements:
    if element.element_type == "table":
        # Create DataFrame from extracted table
        df = pd.DataFrame(element.rows, columns=element.headers)
        # Save as CSV, Excel, or other format
        df.to_csv(f"tables/{element.element_index:03d}_table.csv", index=False)
        df.to_excel(f"tables/{element.element_index:03d}_table.xlsx", index=False)
```

### File Organization Structure
```
document_output/
├── elements.json           # Complete structured data
├── metadata.json          # Document metadata and checksums
├── text/
│   ├── 001_heading.md     # Individual text elements
│   ├── 002_paragraph.md
│   └── 003_list.md
├── tables/
│   ├── 004_table.csv      # Exported tables
│   ├── 004_table.xlsx
│   └── 007_table.csv
├── images/
│   ├── 005_chart.png      # Downloaded images
│   ├── 006_diagram.jpg
│   └── 008_photo.png
└── output.md              # Reconstructed markdown document
```

### JSON Response Examples

#### Invoice Processing
```json
{
  "invoice_number": "INV-2024-001",
  "date": "2024-01-15",
  "vendor": "ABC Company",
  "total": 1250.00,
  "line_items": [
    {
      "element_index": 5,
      "description": "Widget A", 
      "quantity": 10, 
      "price": 125.00
    }
  ]
}
```

#### Table Extraction
```json
{
  "tables": [
    {
      "element_index": 3,
      "headers": ["Product", "Quantity", "Price"],
      "rows": [
        ["Widget A", "10", "$125.00"],
        ["Widget B", "5", "$200.00"]
      ],
      "caption": "Product Pricing Table"
    }
  ]
}
```

#### Document Structure Analysis
```json
{
  "document_type": "research_paper",
  "title": "AI in Document Processing",
  "elements": [
    {
      "element_type": "heading",
      "element_index": 0,
      "content": "Abstract",
      "heading_level": 1
    },
    {
      "element_type": "text", 
      "element_index": 1,
      "content": "This paper presents..."
    },
    {
      "element_type": "table",
      "element_index": 2,
      "headers": ["Method", "Accuracy", "Speed"],
      "rows": [["OCR-A", "95%", "Fast"], ["OCR-B", "98%", "Medium"]]
    },
    {
      "element_type": "image",
      "element_index": 3,
      "image_id": "fig_001",
      "bbox": [100, 200, 400, 350],
      "description": "Performance comparison chart"
    }
  ],
  "page_count": 12,
  "language": "en"
}
```