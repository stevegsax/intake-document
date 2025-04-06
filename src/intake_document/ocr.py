"""Integration with Mistral.ai OCR API."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from mistralai import Mistral
from mistralai.models import UserMessage

from intake_document.config import config
from intake_document.models.document import (
    Document,
    DocumentElement,
    ImageElement,
    TableElement,
    TextElement,
)
from intake_document.utils.exceptions import APIError, OCRError


class MistralOCR:
    """Client for Mistral.ai's OCR capabilities."""

    def __init__(self) -> None:
        """Initialize the Mistral OCR client."""
        self.logger = logging.getLogger(__name__)

        # Get API key from settings
        api_key = config.settings.mistral.api_key
        if not api_key:
            self.logger.warning(
                "No Mistral API key found. Set MISTRAL_API_KEY environment variable "
                "or configure it in the config file."
            )

        # Initialize client (will be None if no API key)
        self.client = Mistral(api_key=api_key) if api_key else None

        # OCR configuration
        self.model = (
            "mistral-large-latest"  # Use the latest model for best OCR
        )
        self.batch_size = config.settings.mistral.batch_size
        self.max_retries = config.settings.mistral.max_retries
        self.timeout = config.settings.mistral.timeout

    def process_document(self, document: Document) -> Document:
        """Process a document through Mistral.ai OCR.

        Args:
            document: The document to process

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

        self.logger.info(f"Processing document with OCR: {document.path}")
        self.logger.debug(f"Document file type: {document.file_type}")

        try:
            # Upload document to Mistral
            self.logger.debug("Uploading document to Mistral.ai")
            document_id = self._upload_document(document.path)
            self.logger.debug(
                f"Document uploaded successfully, ID: {document_id}"
            )

            # Process with OCR
            self.logger.debug("Extracting document elements from OCR results")
            elements = self._extract_document_elements(document_id)
            self.logger.debug(
                f"Extracted {len(elements)} elements from document"
            )

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

        except APIError:
            # Re-raise API errors directly
            raise
        except Exception as e:
            error_msg = f"Error processing document with OCR: {document.path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))

    def _upload_document(self, file_path: Path) -> str:
        """Upload a document to Mistral.ai.

        Args:
            file_path: Path to the document file

        Returns:
            str: The document ID returned by Mistral

        Raises:
            APIError: If the upload fails due to API issues
            OCRError: If the upload fails for other reasons
        """
        self.logger.debug(f"Uploading document: {file_path}")

        # This is a placeholder for the actual upload implementation
        # We'd need to use the Mistral API endpoint for document upload
        try:
            # Check file exists and is readable
            if not file_path.exists():
                raise OCRError(f"File not found: {file_path}")

            if not file_path.is_file():
                raise OCRError(f"Not a file: {file_path}")

            # Check file size
            try:
                file_size = file_path.stat().st_size
                self.logger.debug(f"File size: {file_size / 1024:.2f} KB")
            except OSError as e:
                self.logger.warning(f"Could not determine file size: {str(e)}")

            # In a real implementation, we would:
            # 1. Read the file
            # 2. Send it to Mistral's upload endpoint
            # 3. Get back a document ID

            # For now, we'll simulate this with a placeholder
            # In a real implementation, replace this with actual API call
            # document_id = self.client.upload_document(file_path)

            # Placeholder
            document_id = f"doc_{file_path.stem}_{file_path.stat().st_mtime}"
            self.logger.debug(f"Document uploaded, ID: {document_id}")

            return document_id

        except OCRError:
            # Re-raise OCR errors
            raise
        except Exception as e:
            error_msg = f"Failed to upload document: {file_path}"
            self.logger.error(f"{error_msg}: {str(e)}")

            # Determine if it's an API error or another type of error
            if (
                "ConnectionError" in str(e)
                or "Timeout" in str(e)
                or "Status code" in str(e)
            ):
                raise APIError(error_msg, detail=str(e))
            else:
                raise OCRError(error_msg, detail=str(e))

    def _extract_document_elements(
        self, document_id: str
    ) -> List[DocumentElement]:
        """Extract document elements from OCR results.

        Args:
            document_id: The document ID from upload

        Returns:
            List[DocumentElement]: List of extracted elements

        Raises:
            APIError: If extraction fails due to API issues
            OCRError: If extraction fails for other reasons
        """
        self.logger.debug(f"Extracting elements from document: {document_id}")

        # This is a placeholder for the actual extraction implementation
        # We'd need to use the Mistral API to process the document
        try:
            # Validate document ID
            if not document_id:
                error_msg = "Invalid document ID: empty or None"
                self.logger.error(error_msg)
                raise OCRError(error_msg)

            self.logger.debug(
                f"Generating extraction prompt for document: {document_id}"
            )

            # In a real implementation, we would:
            # 1. Send a request to Mistral to process the document
            # 2. Get back structured data
            # 3. Parse into our document elements

            # Generate prompt for document extraction
            prompt = self._generate_extraction_prompt(document_id)
            self.logger.debug("Extraction prompt generated")

            # Call Mistral API
            self.logger.debug("Calling Mistral API for document analysis")
            response = self._call_mistral_api(prompt)
            self.logger.debug("Received response from Mistral API")

            # Parse response into document elements
            self.logger.debug("Parsing response into document elements")
            elements = self._parse_response(response)
            self.logger.debug(f"Extracted {len(elements)} document elements")

            return elements

        except (APIError, OCRError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = (
                f"Failed to extract document elements from {document_id}"
            )
            self.logger.error(f"{error_msg}: {str(e)}")

            # Determine if it's an API error or another type of error
            if (
                "ConnectionError" in str(e)
                or "Timeout" in str(e)
                or "Status code" in str(e)
            ):
                raise APIError(error_msg, detail=str(e))
            else:
                raise OCRError(error_msg, detail=str(e))

    def _generate_extraction_prompt(self, document_id: str) -> str:
        """Generate a prompt for document extraction.

        Args:
            document_id: The document ID to reference

        Returns:
            str: The generated prompt
        """
        return f"""
        Extract the content from the document with ID '{document_id}'.
        
        Please analyze the document and extract all of its content, maintaining the 
        document's structure and hierarchy. Identify and properly format:
        
        1. Headings and subheadings with their appropriate levels
        2. Paragraphs of text
        3. Lists (both ordered and unordered)
        4. Tables with their headers and data
        5. Images (provide image references)
        
        For each element, specify its type and content in a structured format.
        Maintain the reading order of the document, including multi-column layouts.
        Identify and preserve formatting of special elements.
        """

    def _call_mistral_api(self, prompt: str) -> Dict[str, Any]:
        """Call the Mistral API with the given prompt.

        Args:
            prompt: The prompt to send to Mistral

        Returns:
            Dict[str, Any]: The API response

        Raises:
            ValueError: If the API call fails
        """
        self.logger.debug("Calling Mistral API")

        try:
            # Create messages for the chat completion
            messages = [UserMessage(content=prompt)]

            # Call the Mistral API
            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.1,  # Low temperature for more consistent results
            )

            # Extract and return the response content
            # In a real implementation, we'd properly parse the response from response.content
            # For larger documents, consider using streaming:
            #
            # stream = self.client.chat.stream(
            #     model=self.model,
            #     messages=messages,
            #     max_tokens=4096,
            #     temperature=0.1,
            # )
            # full_response = ""
            # for chunk in stream:
            #     if chunk.data.choices[0].delta.content:
            #         content = chunk.data.choices[0].delta.content
            #         full_response += content
            # Then parse full_response

            # Placeholder structure that would come from the API
            return {
                "elements": [
                    {
                        "type": "heading",
                        "level": 1,
                        "content": "Sample Document",
                    },
                    {
                        "type": "paragraph",
                        "content": "This is a sample paragraph extracted from the document.",
                    },
                    {"type": "list_item", "content": "Sample list item 1"},
                    {"type": "list_item", "content": "Sample list item 2"},
                    {
                        "type": "table",
                        "headers": ["Column 1", "Column 2"],
                        "rows": [
                            ["Data 1,1", "Data 1,2"],
                            ["Data 2,1", "Data 2,2"],
                        ],
                    },
                    {
                        "type": "image",
                        "id": "img_001",
                        "caption": "Sample image",
                    },
                ]
            }

        except Exception as e:
            self.logger.error(f"Error calling Mistral API: {str(e)}")
            raise ValueError(f"Failed to call Mistral API: {str(e)}")

    def _parse_response(
        self, response: Dict[str, Any]
    ) -> List[DocumentElement]:
        """Parse the Mistral API response into document elements.

        Args:
            response: The API response to parse

        Returns:
            List[DocumentElement]: List of parsed document elements
        """
        self.logger.debug("Parsing API response into document elements")

        elements: List[DocumentElement] = []

        # Parse each element from the response
        for elem in response.get("elements", []):
            elem_type = elem.get("type", "")

            if elem_type == "heading":
                elements.append(
                    TextElement(
                        content=elem["content"],
                        level=elem["level"],
                    )
                )
            elif elem_type == "paragraph":
                elements.append(
                    TextElement(
                        content=elem["content"],
                    )
                )
            elif elem_type == "list_item":
                elements.append(
                    TextElement(
                        content=elem["content"],
                        is_list_item=True,
                    )
                )
            elif elem_type == "table":
                elements.append(
                    TableElement(
                        headers=elem["headers"],
                        rows=elem["rows"],
                    )
                )
            elif elem_type == "image":
                elements.append(
                    ImageElement(
                        image_id=elem["id"],
                        caption=elem.get("caption"),
                    )
                )

        return elements
