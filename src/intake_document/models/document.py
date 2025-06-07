"""Document models for the application."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    DOCX = "docx"


class ElementType(str, Enum):
    """Document element types."""

    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"


class DocumentElement(BaseModel):
    """Base class for document elements."""

    element_type: ElementType
    element_index: int


class TextElement(DocumentElement):
    """Text element in a document."""

    element_type: ElementType = ElementType.TEXT
    content: str
    level: Optional[int] = None  # For headings (1-6)
    is_list_item: bool = False


class TableElement(DocumentElement):
    """Table element in a document."""

    element_type: ElementType = ElementType.TABLE
    headers: List[str]
    rows: List[List[str]]


class ImageElement(DocumentElement):
    """Image element in a document."""

    element_type: ElementType = ElementType.IMAGE
    image_id: str
    caption: Optional[str] = None


class DocumentInstance(BaseModel):
    """Represents a specific instance/copy of a document at a particular location."""

    path: Path
    file_type: DocumentType
    checksum: str
    file_size: int
    last_modified: datetime
    processed_at: Optional[datetime] = None


class Document(BaseModel):
    """Represents processed document content with extracted elements."""

    checksum: str
    elements: List[DocumentElement] = Field(default_factory=list)
    markdown: Optional[str] = None
    processed_at: datetime
