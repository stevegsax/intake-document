"""Custom exceptions for the application."""

from typing import Optional


class IntakeDocumentError(Exception):
    """Base exception for all application-specific errors."""

    def __init__(
        self, message: str = "An error occurred", detail: Optional[str] = None
    ):
        """Initialize the exception.

        Args:
            message: The error message
            detail: Additional detail about the error
        """
        self.message = message
        self.detail = detail
        super().__init__(f"{message}{f': {detail}' if detail else ''}")


class ConfigError(IntakeDocumentError):
    """Raised when there's an issue with configuration."""


class XDGError(IntakeDocumentError):
    """Raised when there's an issue with XDG paths."""


class OCRError(IntakeDocumentError):
    """Raised when there's an issue with OCR processing."""


class DocumentError(IntakeDocumentError):
    """Raised when there's an issue with document processing."""


class RenderError(IntakeDocumentError):
    """Raised when there's an issue with rendering a document."""


class FileTypeError(DocumentError):
    """Raised when a file has an unsupported type."""


class APIError(IntakeDocumentError):
    """Raised when there's an issue with API communication."""
