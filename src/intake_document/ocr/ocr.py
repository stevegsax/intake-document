"""OCR processing for document extraction."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from intake_document.config import config
from intake_document.models.document import Document, DocumentElement
from intake_document.ocr.api import MistralAPI
from intake_document.ocr.extraction import ElementExtractor
from intake_document.ocr.pdf import PDFTextExtractor
from intake_document.utils.exceptions import (
    OCRError,
    OCRTextExtractionError,
    FileNotFoundError,
    FileTypeError
)


class MistralOCR:
    """Client for Mistral.ai's OCR capabilities."""

    def __init__(self) -> None:
        """Initialize the Mistral OCR client."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.api = MistralAPI()
        self.extractor = ElementExtractor()
        self.pdf_extractor = PDFTextExtractor()
        
        # OCR configuration
        self.batch_size = config.settings.mistral.batch_size

    def process_documents_batch(self, documents: List[Document]) -> List[Document]:
        """Process multiple documents through Mistral.ai OCR in batch.

        Args:
            documents: The list of documents to process

        Returns:
            List[Document]: The processed documents with extracted elements

        Raises:
            OCRError: If document processing fails
        """
        self.logger.info(f"Processing batch of {len(documents)} documents with OCR")
        
        # Process documents in batches according to batch_size setting
        processed_documents = []
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i // self.batch_size + 1}: {len(batch)} documents")
            
            try:
                # Process each document in the batch individually
                # This is because Mistral's API doesn't support true batch processing for documents
                for doc in batch:
                    self.logger.debug(f"Processing document in batch: {doc.path}")
                    processed_doc = self.process_document(doc)
                    processed_documents.append(processed_doc)
                    
            except Exception as e:
                error_msg = f"Error processing batch of documents"
                self.logger.error(f"{error_msg}: {str(e)}")
                raise OCRError(error_msg, detail=str(e))
        
        self.logger.info(f"Completed processing batch of {len(documents)} documents")
        return processed_documents

    def process_document(self, document: Document) -> Document:
        """Process a document through Mistral.ai OCR.

        Args:
            document: The document to process

        Returns:
            Document: The processed document with extracted elements

        Raises:
            OCRError: If document processing fails
        """
        self.logger.info(f"Processing document with OCR: {document.path}")
        self.logger.debug(f"Document file type: {document.file_type}")

        try:
            # Prepare document for processing
            self.logger.debug("Preparing document for Mistral.ai")
            file_info = self._prepare_document(document.path)

            # Process with OCR
            self.logger.debug("Extracting document elements using OCR")
            elements = self._extract_document_elements(file_info)
            self.logger.debug(f"Extracted {len(elements)} elements from document")

            # Log element types for debugging
            element_types: Dict[str, int] = {}
            for elem in elements:
                elem_type = elem.element_type
                element_types[elem_type] = element_types.get(elem_type, 0) + 1

            self.logger.debug(f"Element types: {element_types}")

            # Update document with extracted elements
            document.elements = elements
            self.logger.info(f"OCR processing complete for {document.path}")

            return document

        except Exception as e:
            error_msg = f"Error processing document with OCR: {document.path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))

    def _prepare_document(self, file_path: Path) -> Dict[str, Any]:
        """Prepare a document for processing with Mistral.ai.

        Args:
            file_path: Path to the document file

        Returns:
            Dict[str, Any]: Dictionary with file information

        Raises:
            FileNotFoundError: If the file doesn't exist
            FileTypeError: If the file type is not supported
            OCRError: If the file preparation fails
        """
        self.logger.debug(f"Preparing document: {file_path}")

        # Check file exists and is readable
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise FileTypeError(f"Not a file: {file_path}")

        try:
            # Check file size
            file_size = file_path.stat().st_size
            self.logger.debug(f"File size: {file_size / 1024:.2f} KB")

            # Read the file as binary
            self.logger.debug(f"Reading file content: {file_path}")
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # For PDFs, try to extract text directly as a fallback option
            extracted_text = None
            if file_path.suffix.lower() == '.pdf':
                try:
                    self.logger.debug("Attempting to extract text directly from PDF")
                    extracted_text = self.pdf_extractor.extract_text_from_pdf(file_content)
                    if extracted_text:
                        self.logger.debug(f"Successfully extracted {len(extracted_text)} chars of text from PDF")
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from PDF: {str(e)}")
            
            # Return file information
            return {
                "content": file_content,
                "filename": file_path.name,
                "file_path": file_path,
                "extracted_text": extracted_text
            }

        except Exception as e:
            error_msg = f"Failed to prepare document: {file_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))

    def _extract_document_elements(self, file_info: Dict[str, Any]) -> List[DocumentElement]:
        """Extract document elements from OCR results.

        Args:
            file_info: Dictionary with file information

        Returns:
            List[DocumentElement]: List of extracted elements

        Raises:
            OCRError: If extraction fails
        """
        file_path = file_info["file_path"]
        self.logger.debug(f"Extracting elements from document: {file_path}")

        # Generate extraction prompt
        prompt = self.api.generate_extraction_prompt(file_path.name)
        
        # Try first with extracted text if available (faster and cheaper)
        extracted_text = file_info.get("extracted_text")
        if extracted_text:
            try:
                self.logger.debug("Using pre-extracted text for OCR processing")
                response = self.api.send_text_ocr_request(extracted_text, file_info["filename"], prompt)
                if response and "content" in response:
                    return self._process_api_response(response["content"])
                self.logger.debug("Pre-extracted text processing failed, falling back to direct OCR")
            except Exception as e:
                self.logger.warning(f"Error processing pre-extracted text: {str(e)}")
                self.logger.debug("Falling back to direct OCR")
        
        # Fall back to full document OCR
        try:
            self.logger.debug("Sending document content for OCR processing")
            response = self.api.send_document_ocr_request(
                file_info["content"], file_info["filename"], prompt
            )
            return self._process_api_response(response["content"])
        except Exception as e:
            error_msg = f"Failed to extract document elements from {file_info['file_path']}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))
    
    def _process_api_response(self, text_content: str) -> List[DocumentElement]:
        """Process API response text to extract document elements.
        
        Args:
            text_content: Text content from API response
            
        Returns:
            List[DocumentElement]: Extracted document elements
            
        Raises:
            OCRTextExtractionError: If extraction fails
        """
        try:
            # Extract structured elements from the text response
            element_dicts = self.extractor.extract_elements_from_text(text_content)

            if not element_dicts:
                self.logger.warning("Failed to extract structured elements, using text as paragraph")
                # Fallback: treat the entire response as a single paragraph
                element_dicts = [{"type": "paragraph", "content": text_content}]

            # Parse response into document elements
            self.logger.debug("Parsing response into document elements")
            elements = self.extractor.parse_response({"elements": element_dicts})
            self.logger.debug(f"Extracted {len(elements)} document elements")

            return elements
        except Exception as e:
            self.logger.error(f"Error processing API response: {str(e)}")
            raise OCRTextExtractionError("Failed to process API response", detail=str(e))

    def _get_mime_type(self, filename: str) -> str:
        """Determine the MIME type based on file extension.

        Args:
            filename: The name of the file

        Returns:
            str: The MIME type for the file
        """
        ext = filename.lower().split(".")[-1]
        mime_types = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "tiff": "image/tiff",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mime_types.get(ext, "application/octet-stream")