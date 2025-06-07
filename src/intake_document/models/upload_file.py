"""Models for Mistral API file upload responses."""

from typing import Optional
from pydantic import BaseModel, Field

from intake_document.models.file_models import FilePurpose, SampleType, Source


class UploadFileOut(BaseModel):
    """Response model for file upload operations.
    
    This model represents the response returned by the Mistral API
    when a file is successfully uploaded.
    """
    
    id: str = Field(..., description="The unique identifier of the file")
    object: str = Field(..., description="The object type, which is always 'file'")
    size_bytes: Optional[int] = Field(None, description="The size of the file, in bytes")
    created_at: int = Field(..., description="The UNIX timestamp (in seconds) of the event")
    filename: str = Field(..., description="The name of the uploaded file")
    purpose: FilePurpose = Field(..., description="The purpose of the file")
    sample_type: SampleType = Field(..., description="The type of sample data")
    source: Source = Field(..., description="The source of the uploaded file")
    num_lines: Optional[int] = Field(None, description="Number of lines in the file, if applicable")
    signed_url: Optional[str] = Field(None, description="The signed URL for accessing the file")
