"""Integration with Mistral.ai OCR API."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
            # Prepare document for processing
            self.logger.debug("Preparing document for Mistral.ai")
            file_info = self._prepare_document(document.path)
            
            # Process with OCR directly
            self.logger.debug("Extracting document elements using OCR")
            elements = self._extract_document_elements(file_info)
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

    def _prepare_document(self, file_path: Path) -> Dict[str, Any]:
        """Prepare a document for processing with Mistral.ai.

        Args:
            file_path: Path to the document file

        Returns:
            Dict[str, Any]: Dictionary with file information

        Raises:
            OCRError: If the file preparation fails
        """
        self.logger.debug(f"Preparing document: {file_path}")

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

            # Read the file as binary
            self.logger.debug(f"Reading file content: {file_path}")
            with open(file_path, "rb") as f:
                file_content = f.read()
                
            # Return file information
            return {
                "content": file_content,
                "filename": file_path.name,
                "file_path": file_path
            }

        except OCRError:
            # Re-raise OCR errors
            raise
        except Exception as e:
            error_msg = f"Failed to prepare document: {file_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise OCRError(error_msg, detail=str(e))

    def _extract_document_elements(
        self, file_info: Dict[str, Any]
    ) -> List[DocumentElement]:
        """Extract document elements from OCR results.

        Args:
            file_info: Dictionary with file information

        Returns:
            List[DocumentElement]: List of extracted elements

        Raises:
            APIError: If extraction fails due to API issues
            OCRError: If extraction fails for other reasons
        """
        file_path = file_info["file_path"]
        self.logger.debug(f"Extracting elements from document: {file_path}")

        try:
            # Generate extraction prompt
            prompt = self._generate_extraction_prompt(file_path.name)
            
            if self.client is None:
                self.logger.error("Mistral client is not initialized")
                raise OCRError("Mistral client is not initialized")
                
            # Send a request to the Mistral API
            self.logger.debug("Sending OCR request to Mistral API")
            
            try:
                # Call Mistral API with the file content and prompt
                # Use the chat method with file attachments
                messages = [
                    UserMessage(
                        content=prompt,
                        attachments=[
                            {"data": file_info["content"], "type": self._get_mime_type(file_info["filename"])}
                        ]
                    )
                ]
                
                # Call the Mistral API correctly
                response = self.client.chat_completions(
                    model=self.model,
                    messages=messages
                )
                
                # Extract text content from response
                text_content = response.choices[0].message.content
                
                # Extract structured elements from the text response
                element_dicts = self._extract_elements_from_text(text_content)
                
                if not element_dicts:
                    self.logger.warning("Failed to extract structured elements, using text as paragraph")
                    # Fallback: treat the entire response as a single paragraph
                    element_dicts = [{"type": "paragraph", "content": text_content}]
                
                # Parse response into document elements
                self.logger.debug("Parsing response into document elements")
                elements = self._parse_response({"elements": element_dicts})
                self.logger.debug(f"Extracted {len(elements)} document elements")

                return elements
                
            except Exception as e:
                self.logger.error(f"API request failed: {str(e)}")
                raise APIError(f"Failed to process document with API: {str(e)}")

        except (APIError, OCRError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Failed to extract document elements from {file_info['file_path']}"
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

    def _get_mime_type(self, filename: str) -> str:
        """Determine the MIME type based on file extension.
        
        Args:
            filename: The name of the file
            
        Returns:
            str: The MIME type for the file
        """
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'tiff': 'image/tiff',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(ext, 'application/octet-stream')
        
    def _generate_extraction_prompt(self, filename: str) -> str:
        """Generate a prompt for document extraction.

        Args:
            filename: The name of the file being processed

        Returns:
            str: The generated prompt
        """
        return f"""
        Extract the content from the attached document '{filename}'.
        
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
        
    def _extract_elements_from_text(
        self, text: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract structured document elements from text response.
        
        This method analyzes the text response from the API and tries to
        extract structured document elements.
        
        Args:
            text: The text content to process
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of document elements if extraction
                was successful, None otherwise
        """
        self.logger.debug(f"Extracting elements from text of length {len(text)}")
        
        if not text or len(text) < 50:
            self.logger.warning("Text too short for meaningful extraction")
            return None
            
        try:
            # Try to identify headers using patterns (e.g., lines with # markdown syntax)
            import re
            
            elements: List[Dict[str, Any]] = []
            lines = text.split("\n")
            
            current_text = ""
            in_list = False
            in_table = False
            table_headers = []
            table_rows = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    if current_text:
                        # Finish current paragraph if we have one
                        elements.append({"type": "paragraph", "content": current_text})
                        current_text = ""
                    continue
                    
                # Check for headings (# heading)
                heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
                if heading_match:
                    # If we have accumulated text, add it first
                    if current_text:
                        elements.append({"type": "paragraph", "content": current_text})
                        current_text = ""
                        
                    level = len(heading_match.group(1))
                    content = heading_match.group(2).strip()
                    elements.append({
                        "type": "heading",
                        "level": level,
                        "content": content
                    })
                    continue
                
                # Check for list items
                list_match = re.match(r"^[-*]\s+(.+)$", line)
                if list_match:
                    # If we have accumulated text, add it first
                    if current_text:
                        elements.append({"type": "paragraph", "content": current_text})
                        current_text = ""
                    
                    content = list_match.group(1).strip()
                    elements.append({
                        "type": "list_item",
                        "content": content
                    })
                    continue
                    
                # Check for tables (markdown tables)
                # Table headers: | Column1 | Column2 |
                table_header_match = re.match(r"^\|(.+)\|$", line)
                if table_header_match and not in_table:
                    # This might be a table header
                    # If the next line contains only |---|---|, it's a table
                    if current_text:
                        elements.append({"type": "paragraph", "content": current_text})
                        current_text = ""
                    
                    # Extract headers
                    header_cells = [cell.strip() for cell in table_header_match.group(1).split("|")]
                    table_headers = header_cells
                    in_table = True
                    continue
                
                # Table rows
                if in_table and re.match(r"^\|(.+)\|$", line):
                    cells = [cell.strip() for cell in line[1:-1].split("|")]
                    if all(cell == "" or re.match(r"^[-:]+$", cell) for cell in cells):
                        # This is the separator row in markdown tables
                        continue
                    
                    table_rows.append(cells)
                    continue
                elif in_table:
                    # End of table
                    elements.append({
                        "type": "table",
                        "headers": table_headers,
                        "rows": table_rows
                    })
                    table_headers = []
                    table_rows = []
                    in_table = False
                
                # Check for image references ![alt](url)
                image_match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
                if image_match:
                    if current_text:
                        elements.append({"type": "paragraph", "content": current_text})
                        current_text = ""
                        
                    caption = image_match.group(1)
                    image_url = image_match.group(2)
                    image_id = re.sub(r"^.*/", "", image_url.split(".")[0])
                    
                    elements.append({
                        "type": "image",
                        "id": image_id,
                        "caption": caption
                    })
                    continue
                
                # Regular text, append to current paragraph
                if current_text:
                    current_text += " " + line
                else:
                    current_text = line
            
            # Add any remaining text
            if current_text:
                elements.append({"type": "paragraph", "content": current_text})
            
            # Make sure we ended any open tables
            if in_table and table_headers and table_rows:
                elements.append({
                    "type": "table",
                    "headers": table_headers,
                    "rows": table_rows
                })
            
            if elements:
                self.logger.debug(f"Successfully extracted {len(elements)} elements from text")
                return elements
            else:
                self.logger.warning("No elements could be extracted from text")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting elements from text: {str(e)}")
            return None
            

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
