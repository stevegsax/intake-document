"""Custom exceptions for the application."""

from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    """Error codes for application exceptions."""

    # General errors
    UNKNOWN_ERROR = 1000

    # Configuration errors
    CONFIG_ERROR = 2000

    # File errors
    FILE_ERROR = 3000

    # OCR processing errors
    OCR_ERROR = 4000

    # API errors
    API_ERROR = 5000

    # Rendering errors
    RENDER_ERROR = 6000


class IntakeDocumentError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        detail: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
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
    ):
        super().__init__(message, detail, ErrorCode.CONFIG_ERROR)


class FileError(IntakeDocumentError):
    """Base class for file-related errors."""

    def __init__(
        self, message: str = "File error", detail: Optional[str] = None
    ):
        super().__init__(message, detail, ErrorCode.FILE_ERROR)


class FileTypeError(FileError):
    """Raised when a file has an unsupported type."""

    pass


class OCRError(IntakeDocumentError):
    """Base class for OCR processing errors."""

    def __init__(
        self,
        message: str = "OCR processing error",
        detail: Optional[str] = None,
    ):
        super().__init__(message, detail, ErrorCode.OCR_ERROR)


class DocumentError(IntakeDocumentError):
    """Base class for document processing errors."""

    def __init__(
        self,
        message: str = "Document processing error",
        detail: Optional[str] = None,
    ):
        super().__init__(message, detail, ErrorCode.FILE_ERROR)


class APIError(IntakeDocumentError):
    """Base class for API communication errors."""

    def __init__(
        self, message: str = "API error", detail: Optional[str] = None
    ):
        super().__init__(message, detail, ErrorCode.API_ERROR)


class RenderError(IntakeDocumentError):
    """Base class for rendering errors."""

    def __init__(
        self, message: str = "Rendering error", detail: Optional[str] = None
    ):
        super().__init__(message, detail, ErrorCode.RENDER_ERROR)
