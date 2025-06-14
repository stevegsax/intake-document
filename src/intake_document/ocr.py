"""Integration with Mistral.ai OCR API."""

import base64
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

from mistralai import Mistral
from mistralai.client import MistralClient
from PIL import Image

from intake_document.config import config
from intake_document.models.document import (
    Document,
    DocumentElement,
    DocumentInstance,
    ElementType,
    ImageElement,
    TableElement,
    TextElement,
)
from intake_document.models.upload_file import UploadFileOut
from intake_document.utils.exceptions import APIError, OCRError


class MistralOCR:
    """Client for Mistral.ai's OCR capabilities."""

    def __init__(self) -> None:
        """Initialize the Mistral OCR client."""
        self.logger = logging.getLogger(__name__)

        # Get API key from settings
        self.api_key = config.settings.mistral.api_key
        if not self.api_key:
            self.logger.warning(
                "No Mistral API key found. Set MISTRAL_API_KEY environment variable "
                "or configure it in the config file."
            )

        # Initialize client (will be None if no API key)
        self.client = Mistral(api_key=self.api_key) if self.api_key else None

        # OCR configuration
        self.model = (
            "mistral-ocr-latest"  # Use the OCR-specific model
        )
        self.batch_size = config.settings.mistral.batch_size
        self.max_retries = config.settings.mistral.max_retries
        self.timeout = config.settings.mistral.timeout

    def process_document(
        self, document_instance: DocumentInstance
    ) -> Document:
        """Process a document through Mistral.ai OCR.

        Args:
            document_instance: The document instance to process

        Returns:
            Document: The processed document with extracted elements

        Raises:
            OCRError: If no API key is configured or document processing fails
            APIError: If API communication fails
        """
        # Check if client is initialized
        if self.client is None:
            error_msg = "Mistral client not initialized"
            self.logger.error(f"{error_msg}. Please provide an API key.")
            raise OCRError(
                error_msg,
                detail="Set MISTRAL_API_KEY environment variable or configure it in the config file.",
            )

        self.logger.debug(
            f"Processing {document_instance.file_type.value}: {document_instance.path.name}"
        )

        try:
            # Process document with OCR API
            elements = self._process_with_ocr_api(document_instance.path)

            # Create processed document
            document = Document(
                checksum=document_instance.checksum,
                elements=elements,
                processed_at=datetime.now(),
            )

            return document

        except APIError:
            # Re-raise API errors directly
            raise
        except Exception as e:
            error_msg = (
                f"Error processing document with OCR: {document_instance.path}"
            )
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))

    def _process_with_ocr_api(self, file_path: Path) -> List[DocumentElement]:
        """Process document using Mistral OCR API.

        Args:
            file_path: Path to the document file

        Returns:
            List[DocumentElement]: List of extracted document elements

        Raises:
            APIError: If the OCR API call fails
            OCRError: If document processing fails for other reasons
        """
        self.logger.debug(f"Processing document with OCR API: {file_path}")
        
        temp_file = None
        
        try:
            # Convert file if needed (images to PDF)
            file_to_upload, temp_file = self._prepare_file_for_upload(file_path)
            
            # Upload file and get signed URL
            upload_info = self._upload_file_and_get_url(file_to_upload, file_path)
            
            # Save upload info to JSON
            self._save_upload_info(upload_info, file_path)
            
            # Perform OCR using the signed URL
            elements = self._perform_ocr(upload_info.signed_url)
            
            return elements
            
        except Exception as e:
            self._handle_ocr_error(e, file_path)
        finally:
            self._cleanup_temp_file(temp_file)


    def _prepare_file_for_upload(self, file_path: Path) -> tuple[Path, tempfile._TemporaryFileWrapper]:
        """Prepare file for upload, converting if necessary.
        
        Args:
            file_path: Path to the original file
            
        Returns:
            tuple: (Path to file to upload, Temporary file if created or None)
        """
        # Check if we need to convert the file
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            self.logger.info(f"Converting image file to PDF: {file_path}")
            # Create a temporary PDF file
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.close()
            
            # Convert image to PDF
            img = Image.open(file_path)
            img.save(temp_file.name, 'PDF', resolution=100.0)
            
            # Use the temporary file for processing
            file_to_upload = Path(temp_file.name)
            self.logger.debug(f"Image converted to PDF: {file_to_upload}")
            return file_to_upload, temp_file
        
        return file_path, None
    
    def _upload_file_and_get_url(self, file_to_upload: Path, original_path: Path) -> UploadFileOut:
        """Upload file to Mistral API and get signed URL.
        
        Args:
            file_to_upload: Path to the file to upload
            original_path: Original file path
            
        Returns:
            UploadFileOut: Upload information including signed URL
        """
        # Step 1: Upload the file to Mistral server
        self.logger.debug(f"Uploading file to Mistral server: {file_to_upload}")
        
        uploaded_file = self.client.files.upload(
            file={
                "file_name": file_to_upload.name,
                "content": open(file_to_upload, "rb"),
            },
            purpose="ocr"
        )
        
        # Get file data from upload response
        file_data = uploaded_file.model_dump()
        
        # Use file size if size_bytes is not available
        if "size_bytes" not in file_data or file_data["size_bytes"] is None:
            file_size = file_to_upload.stat().st_size
            file_data["size_bytes"] = file_size
            self.logger.debug(f"Using file size as fallback: {file_size} bytes")
        
        # Step 2: Get the signed URL of the uploaded file
        self.logger.debug(f"Getting signed URL for uploaded file: {uploaded_file.id}")
        signed_url_response = self.client.files.get_signed_url(file_id=uploaded_file.id)
        
        # Add signed URL to the upload file info
        file_data["signed_url"] = signed_url_response.url
        
        # Create UploadFileOut object with all data including signed URL
        return UploadFileOut.model_validate(file_data)
    
    def _save_upload_info(self, upload_info: UploadFileOut, original_path: Path) -> None:
        """Save upload info to JSON file.
        
        Args:
            upload_info: The upload information to save
            original_path: Original file path
        """
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        json_file_path = output_dir / f"{original_path.stem}_upload_info.json"
        
        with open(json_file_path, "w") as f:
            f.write(upload_info.as_json())
        
        self.logger.info(f"Saved file upload info to: {json_file_path}")
    
    def _perform_ocr(self, signed_url: str) -> List[DocumentElement]:
        """Perform OCR using the signed URL.
        
        Args:
            signed_url: The signed URL to access the file
            
        Returns:
            List[DocumentElement]: Extracted document elements
        """
        self.logger.debug("Calling Mistral OCR API with signed URL")
        
        with Mistral(api_key=self.api_key) as mistral:
            ocr_response = mistral.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "document_url": signed_url,
                    "type": "document_url"
                },
                include_image_base64=True
            )

        # Parse the OCR response into document elements
        elements = self._parse_ocr_response(ocr_response)
        self.logger.debug(f"Extracted {len(elements)} document elements")
        
        return elements
    
    def _handle_ocr_error(self, exception: Exception, file_path: Path) -> None:
        """Handle OCR processing errors.
        
        Args:
            exception: The exception that occurred
            file_path: Path to the original file
            
        Raises:
            APIError: If it's an API-related error
            OCRError: For other types of errors
        """
        error_msg = f"Failed to process document with OCR API: {file_path}"
        self.logger.error(f"{error_msg}: {str(exception)}")
        
        # Determine if it's an API error or another type of error
        if (
            "ConnectionError" in str(exception)
            or "Timeout" in str(exception)
            or "Status code" in str(exception)
            or "API" in str(exception)
        ):
            raise APIError(error_msg, detail=str(exception))
        else:
            raise OCRError(error_msg, detail=str(exception))
    
    def _cleanup_temp_file(self, temp_file) -> None:
        """Clean up temporary file if it exists.
        
        Args:
            temp_file: Temporary file to clean up
        """
        if temp_file and Path(temp_file.name).exists():
            try:
                Path(temp_file.name).unlink()
                self.logger.debug(f"Temporary file deleted: {temp_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to delete temporary file {temp_file.name}: {str(e)}")
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file extension.

        Args:
            file_path: Path to the file

        Returns:
            str: MIME type string
        """
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mime_types.get(
            file_path.suffix.lower(), "application/octet-stream"
        )



    def _parse_ocr_response(self, ocr_response) -> List[DocumentElement]:
        """Parse the Mistral OCR response into document elements.

        Args:
            ocr_response: The OCR API response object

        Returns:
            List[DocumentElement]: List of parsed document elements
        """
        self.logger.debug("Parsing OCR response into document elements")

        elements: List[DocumentElement] = []

        # The OCR response structure may vary, so we need to adapt based on
        # the actual response format from mistral-ocr-latest
        try:
            # Try to access the content from the OCR response
            if hasattr(ocr_response, 'content'):
                content = ocr_response.content
            elif hasattr(ocr_response, 'text'):
                content = ocr_response.text
            elif isinstance(ocr_response, dict):
                content = ocr_response.get('content') or ocr_response.get('text', '')
            else:
                content = str(ocr_response)

            # For now, create a simple text element with the extracted content
            # This can be enhanced later to parse structured content
            if content:
                elements.append(
                    TextElement(
                        element_type=ElementType.TEXT,
                        element_index=0,
                        content=content.strip(),
                    )
                )

            self.logger.debug(f"Parsed OCR response into {len(elements)} elements")
            return elements

        except Exception as e:
            self.logger.warning(f"Failed to parse OCR response: {str(e)}")
            # Return empty list if parsing fails
            return []
