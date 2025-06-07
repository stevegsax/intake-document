"""Models related to file handling and API responses."""

from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field


class FilePurpose(str, Enum):
    """Purpose of the uploaded file."""
    
    OCR = "ocr"
    FINE_TUNING = "fine-tuning"
    BATCH_PROCESSING = "batch-processing"


class SampleType(str, Enum):
    """Type of sample data."""
    
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    OTHER = "other"
    OCR_INPUT = "ocr_input"


class Source(str, Enum):
    """Source of the uploaded file."""
    
    USER = "user"
    API = "api"
    SYSTEM = "system"
    UPLOAD = "upload"


class UploadFileOut(BaseModel):
    """Response model for file upload operations.
    
    This model represents the response returned by the Mistral API
    when a file is successfully uploaded.
    """
    
    id: str = Field(..., description="The unique identifier of the file")
    object: str = Field(..., description="The object type, which is always 'file'")
    size_bytes: int = Field(..., description="The size of the file, in bytes")
    created_at: int = Field(..., description="The UNIX timestamp (in seconds) of the event")
    filename: str = Field(..., description="The name of the uploaded file")
    purpose: FilePurpose = Field(..., description="The purpose of the file")
    sample_type: SampleType = Field(..., description="The type of sample data")
    source: Source = Field(..., description="The source of the uploaded file")
    num_lines: Optional[int] = Field(None, description="Number of lines in the file, if applicable")
