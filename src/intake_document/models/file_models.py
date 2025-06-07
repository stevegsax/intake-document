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


