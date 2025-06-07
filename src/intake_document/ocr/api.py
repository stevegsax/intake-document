"""API communication with Mistral.ai."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
import base64

from mistralai import Mistral, UserMessage

from intake_document.config import config
from intake_document.utils.exceptions import (
    APIConnectionError,
    APIAuthenticationError,
    APIQuotaError,
    APITimeoutError,
    APIResponseError
)


class MistralAPI:
    """Interface for communicating with Mistral.ai API."""

    def __init__(self) -> None:
        """Initialize the Mistral API client."""
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
        self.max_retries = config.settings.mistral.max_retries
        self.timeout = config.settings.mistral.timeout
    
    def validate_api_key(self) -> bool:
        """Validate that an API key is configured.
        
        Returns:
            bool: True if API key is configured
            
        Raises:
            APIAuthenticationError: If no API key is configured
        """
        if self.client is None:
            error_msg = "Mistral client not initialized"
            self.logger.error(f"{error_msg}. Please provide an API key.")
            raise APIAuthenticationError(
                error_msg,
                detail="Set MISTRAL_API_KEY environment variable or configure it in the config file."
            )
        return True
    
    def send_document_ocr_request(self, file_content: bytes, filename: str, prompt: str) -> Dict[str, Any]:
        """Send a document OCR request to the Mistral API.
        
        Args:
            file_content: Binary content of the file
            filename: Name of the file
            prompt: Instruction prompt for OCR
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            APIConnectionError: If connection to API fails
            APIAuthenticationError: If authentication fails
            APITimeoutError: If request times out
            APIResponseError: If API returns an error response
        """
        self.validate_api_key()
        
        try:
            # Convert file content to base64 for text-based transmission
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Create message content including instructions and file excerpt
            message_content = f"""You are a document OCR system. 

I need you to extract text from a document and format it as markdown. The document is '{filename}' and I'll provide its content.

1. Extract ONLY the actual text content from this document.
2. Preserve the exact structure and formatting of the original document.
3. Maintain all headings, paragraphs, lists, and tables exactly as they appear.
4. Do not generate or invent any content that is not in the original document.
5. Do not explain the document or add commentary.
6. Format the extracted content in clean markdown.
7. Respond ONLY with the markdown content of the document.

Document: '{filename}'

The document content is provided as base64: {file_base64[:100]}... (truncated)

Original instructions: {prompt}"""
            
            # Create proper UserMessage object
            message = UserMessage(content=message_content)
            
            # Call the API
            self.logger.debug("Calling Mistral API for document OCR")
            response = self.client.chat.complete(
                model=self.model,
                messages=[message],  # type: ignore
            )
            
            self.logger.debug("Successfully called Mistral API")
            
            # Extract content from response
            if response.choices and len(response.choices) > 0:
                text_content = response.choices[0].message.content
                return {"content": text_content}
            else:
                self.logger.warning("No content in response from Mistral API")
                raise APIResponseError("Empty response from API")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Classify the error type
            if "connection" in error_msg or "network" in error_msg:
                raise APIConnectionError("Failed to connect to Mistral API", detail=str(e))
            elif "auth" in error_msg or "key" in error_msg or "unauthorized" in error_msg:
                raise APIAuthenticationError("Authentication failed with Mistral API", detail=str(e))
            elif "quota" in error_msg or "limit" in error_msg or "exceeded" in error_msg:
                raise APIQuotaError("Mistral API quota exceeded", detail=str(e))
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise APITimeoutError("Mistral API request timed out", detail=str(e))
            else:
                raise APIResponseError(f"Mistral API request failed", detail=str(e))
    
    def send_text_ocr_request(self, extracted_text: str, filename: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Send a text-based OCR request using pre-extracted text.
        
        Args:
            extracted_text: Text already extracted from document
            filename: Name of the file
            prompt: Instruction prompt for OCR
            
        Returns:
            Optional[Dict[str, Any]]: API response or None if extraction not possible
            
        Raises:
            APIConnectionError: If connection to API fails
            APIAuthenticationError: If authentication fails
            APITimeoutError: If request times out
            APIResponseError: If API returns an error response
        """
        if not extracted_text or len(extracted_text) < 10:
            self.logger.warning("Extracted text too short for meaningful processing")
            return None
            
        self.validate_api_key()
        
        try:
            # Create message with the extracted text
            message_content = f"""You are a document OCR system. 

I need you to format the extracted text from a document as markdown. The document is '{filename}'.

1. Format the provided text as clean markdown.
2. Preserve the structure and formatting from the original document as much as possible.
3. Identify and format headings, paragraphs, lists, and tables correctly.
4. Do not generate or invent any content that is not in the text.
5. Do not explain the document or add commentary.
6. Respond ONLY with the markdown content.

Document: '{filename}'

Extracted text from the document:

```
{extracted_text[:4000]}
```

{("(text truncated due to length)" if len(extracted_text) > 4000 else "")}

Original instructions: {prompt}"""
            
            # Create proper UserMessage object
            message = UserMessage(content=message_content)
            
            # Call the API
            self.logger.debug("Calling Mistral API with extracted text")
            response = self.client.chat.complete(
                model=self.model,
                messages=[message],  # type: ignore
            )
            
            self.logger.debug("Successfully called Mistral API with text")
            
            # Extract content from response
            if response.choices and len(response.choices) > 0:
                text_content = response.choices[0].message.content
                return {"content": text_content}
            else:
                self.logger.warning("No content in response from Mistral API")
                return None
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Classify the error type
            if "connection" in error_msg or "network" in error_msg:
                raise APIConnectionError("Failed to connect to Mistral API", detail=str(e))
            elif "auth" in error_msg or "key" in error_msg or "unauthorized" in error_msg:
                raise APIAuthenticationError("Authentication failed with Mistral API", detail=str(e))
            elif "quota" in error_msg or "limit" in error_msg or "exceeded" in error_msg:
                raise APIQuotaError("Mistral API quota exceeded", detail=str(e))
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise APITimeoutError("Mistral API request timed out", detail=str(e))
            else:
                raise APIResponseError(f"Mistral API request failed", detail=str(e))
    
    def generate_extraction_prompt(self, filename: str) -> str:
        """Generate a prompt for document extraction.

        Args:
            filename: The name of the file being processed

        Returns:
            str: The generated prompt
        """
        return f"""
        Extract the EXACT content from the document '{filename}'.
        
        Your task is to perform OCR on this document and extract its content with perfect accuracy.
        Do not generate or invent content. Only extract what is actually in the document.
        
        Maintain the exact:
        
        1. Headings and subheadings with their appropriate levels
        2. Paragraphs of text with the exact wording
        3. Lists (both ordered and unordered) exactly as they appear
        4. Tables with their exact headers and data
        5. Images (provide image references)
        
        Preserve the exact reading order of the document, including multi-column layouts.
        Do not add any commentary, explanations, or content that is not in the original document.
        """