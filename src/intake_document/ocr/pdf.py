"""PDF text extraction utilities."""

import logging
from typing import Optional

from intake_document.utils.exceptions import OCRTextExtractionError


class PDFTextExtractor:
    """Extracts text directly from PDF files."""

    def __init__(self) -> None:
        """Initialize the PDF text extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Optional[str]:
        """Extract text directly from a PDF file.
        
        Args:
            pdf_content: The binary content of the PDF file
            
        Returns:
            Optional[str]: The extracted text, or None if extraction failed
            
        Raises:
            OCRTextExtractionError: If a critical extraction error occurs
        """
        try:
            # Import here to avoid dependencies for those who don't need PDF extraction
            from io import BytesIO
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
            import io
            
            # Create file-like objects for input and output
            pdf_file = BytesIO(pdf_content)
            output_string = io.StringIO()
            
            # Extract text
            extract_text_to_fp(pdf_file, output_string, laparams=LAParams(), 
                               output_type='text', codec='utf-8')
            
            # Get the extracted text
            text = output_string.getvalue()
            
            return text if text.strip() else None
        except ImportError as e:
            self.logger.warning(f"PDF text extraction module not available: {str(e)}")
            self.logger.info("Install pdfminer.six for PDF text extraction support")
            return None
        except Exception as e:
            self.logger.warning(f"PDF text extraction failed: {str(e)}")
            # We return None instead of raising because this is a fallback mechanism
            # and we don't want it to block the main OCR path
            return None