"""Custom exceptions for the application."""

from typing import Optional
from enum import Enum


class ErrorCode(Enum):
    """Error codes for application exceptions."""
    # General errors
    UNKNOWN_ERROR = 1000
    
    # Configuration errors
    CONFIG_NOT_FOUND = 2000
    CONFIG_INVALID = 2001
    CONFIG_PERMISSION_DENIED = 2002
    
    # XDG errors
    XDG_PATH_NOT_FOUND = 3000
    XDG_PERMISSION_DENIED = 3001
    
    # File errors
    FILE_NOT_FOUND = 4000
    FILE_PERMISSION_DENIED = 4001
    FILE_TYPE_UNSUPPORTED = 4002
    FILE_TOO_LARGE = 4003
    FILE_CORRUPT = 4004
    
    # Document processing errors
    DOCUMENT_PARSE_ERROR = 5000
    DOCUMENT_ELEMENT_ERROR = 5001
    DOCUMENT_STRUCTURE_ERROR = 5002
    
    # OCR errors
    OCR_EXTRACTION_ERROR = 6000
    OCR_TEXT_EXTRACTION_ERROR = 6001
    OCR_TABLE_EXTRACTION_ERROR = 6002
    OCR_IMAGE_EXTRACTION_ERROR = 6003
    
    # API errors
    API_CONNECTION_ERROR = 7000
    API_AUTHENTICATION_ERROR = 7001
    API_QUOTA_ERROR = 7002
    API_TIMEOUT_ERROR = 7003
    API_RESPONSE_ERROR = 7004
    
    # Rendering errors
    RENDER_MARKDOWN_ERROR = 8000
    RENDER_TABLE_ERROR = 8001
    RENDER_IMAGE_ERROR = 8002


class IntakeDocumentError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self, 
        message: str = "An error occurred", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR
    ):
        """Initialize the exception.

        Args:
            message: The error message
            detail: Additional detail about the error
            error_code: Specific error code
        """
        self.message = message
        self.detail = detail
        self.error_code = error_code
        super().__init__(f"{message}{f': {detail}' if detail else ''}")


class ConfigError(IntakeDocumentError):
    """Raised when there's an issue with configuration."""
    
    def __init__(
        self, 
        message: str = "Configuration error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.CONFIG_NOT_FOUND
    ):
        super().__init__(message, detail, error_code)


class ConfigNotFoundError(ConfigError):
    """Raised when a configuration file is not found."""
    
    def __init__(self, message: str = "Configuration file not found", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.CONFIG_NOT_FOUND)


class ConfigInvalidError(ConfigError):
    """Raised when a configuration file has invalid syntax or values."""
    
    def __init__(self, message: str = "Invalid configuration", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.CONFIG_INVALID)


class XDGError(IntakeDocumentError):
    """Raised when there's an issue with XDG paths."""
    
    def __init__(
        self, 
        message: str = "XDG error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.XDG_PATH_NOT_FOUND
    ):
        super().__init__(message, detail, error_code)


class XDGPathNotFoundError(XDGError):
    """Raised when an XDG path cannot be found or created."""
    
    def __init__(self, message: str = "XDG path not found", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.XDG_PATH_NOT_FOUND)


class OCRError(IntakeDocumentError):
    """Base class for OCR processing errors."""
    
    def __init__(
        self, 
        message: str = "OCR processing error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.OCR_EXTRACTION_ERROR
    ):
        super().__init__(message, detail, error_code)


class OCRTextExtractionError(OCRError):
    """Raised when text extraction fails during OCR processing."""
    
    def __init__(self, message: str = "Text extraction failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.OCR_TEXT_EXTRACTION_ERROR)


class OCRTableExtractionError(OCRError):
    """Raised when table extraction fails during OCR processing."""
    
    def __init__(self, message: str = "Table extraction failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.OCR_TABLE_EXTRACTION_ERROR)


class OCRImageExtractionError(OCRError):
    """Raised when image extraction fails during OCR processing."""
    
    def __init__(self, message: str = "Image extraction failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.OCR_IMAGE_EXTRACTION_ERROR)


class DocumentError(IntakeDocumentError):
    """Base class for document processing errors."""
    
    def __init__(
        self, 
        message: str = "Document processing error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.DOCUMENT_PARSE_ERROR
    ):
        super().__init__(message, detail, error_code)


class DocumentStructureError(DocumentError):
    """Raised when the document has an invalid structure."""
    
    def __init__(self, message: str = "Invalid document structure", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.DOCUMENT_STRUCTURE_ERROR)


class DocumentElementError(DocumentError):
    """Raised when a document element cannot be processed."""
    
    def __init__(self, message: str = "Document element error", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.DOCUMENT_ELEMENT_ERROR)


class RenderError(IntakeDocumentError):
    """Base class for rendering errors."""
    
    def __init__(
        self, 
        message: str = "Rendering error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.RENDER_MARKDOWN_ERROR
    ):
        super().__init__(message, detail, error_code)


class RenderTableError(RenderError):
    """Raised when a table cannot be rendered."""
    
    def __init__(self, message: str = "Table rendering failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.RENDER_TABLE_ERROR)


class RenderImageError(RenderError):
    """Raised when an image cannot be rendered."""
    
    def __init__(self, message: str = "Image rendering failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.RENDER_IMAGE_ERROR)


class FileError(IntakeDocumentError):
    """Base class for file-related errors."""
    
    def __init__(
        self, 
        message: str = "File error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.FILE_NOT_FOUND
    ):
        super().__init__(message, detail, error_code)


class FileNotFoundError(FileError):
    """Raised when a file cannot be found."""
    
    def __init__(self, message: str = "File not found", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.FILE_NOT_FOUND)


class FilePermissionError(FileError):
    """Raised when file permissions prevent an operation."""
    
    def __init__(self, message: str = "File permission denied", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.FILE_PERMISSION_DENIED)


class FileTypeError(FileError):
    """Raised when a file has an unsupported type."""
    
    def __init__(self, message: str = "Unsupported file type", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.FILE_TYPE_UNSUPPORTED)


class FileSizeError(FileError):
    """Raised when a file is too large to process."""
    
    def __init__(self, message: str = "File is too large", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.FILE_TOO_LARGE)


class FileCorruptError(FileError):
    """Raised when a file is corrupt and cannot be processed."""
    
    def __init__(self, message: str = "File is corrupt", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.FILE_CORRUPT)


class APIError(IntakeDocumentError):
    """Base class for API communication errors."""
    
    def __init__(
        self, 
        message: str = "API error", 
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.API_CONNECTION_ERROR
    ):
        super().__init__(message, detail, error_code)


class APIConnectionError(APIError):
    """Raised when connection to the API fails."""
    
    def __init__(self, message: str = "API connection failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.API_CONNECTION_ERROR)


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "API authentication failed", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.API_AUTHENTICATION_ERROR)


class APIQuotaError(APIError):
    """Raised when API quota is exceeded."""
    
    def __init__(self, message: str = "API quota exceeded", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.API_QUOTA_ERROR)


class APITimeoutError(APIError):
    """Raised when API request times out."""
    
    def __init__(self, message: str = "API request timed out", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.API_TIMEOUT_ERROR)


class APIResponseError(APIError):
    """Raised when API returns an error response."""
    
    def __init__(self, message: str = "API returned an error", detail: Optional[str] = None):
        super().__init__(message, detail, ErrorCode.API_RESPONSE_ERROR)