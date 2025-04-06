"""Document models for the application."""

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


class DocumentElement(BaseModel):
    """Base class for document elements."""

    element_type: str


class TextElement(DocumentElement):
    """Text element in a document."""

    element_type: str = "text"
    content: str
    level: Optional[int] = None  # For headings (1-6)
    is_list_item: bool = False


class TableElement(DocumentElement):
    """Table element in a document."""

    element_type: str = "table"
    headers: List[str]
    rows: List[List[str]]


class ImageElement(DocumentElement):
    """Image element in a document."""

    element_type: str = "image"
    image_id: str
    caption: Optional[str] = None


class Document(BaseModel):
    """Represents a document with its elements."""

    path: Path
    file_type: DocumentType
    elements: List[DocumentElement] = Field(default_factory=list)
    markdown: Optional[str] = None
