"""File utility functions for document processing."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple

from intake_document.models.document import DocumentType
from intake_document.utils.exceptions import FileError, FileTypeError


def calculate_sha512(file_path: Path) -> str:
    """Calculate SHA-512 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        str: Hexadecimal SHA-512 checksum

    Raises:
        FileError: If file cannot be read
    """
    try:
        sha512_hash = hashlib.sha512()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(65536), b""):
                sha512_hash.update(chunk)
        return sha512_hash.hexdigest()
    except OSError as e:
        raise FileError(
            f"Failed to calculate checksum for {file_path}", detail=str(e)
        )


def get_file_metadata(file_path: Path) -> Tuple[int, datetime]:
    """Get file size and modification time.

    Args:
        file_path: Path to the file

    Returns:
        Tuple[int, datetime]: File size in bytes and modification time

    Raises:
        FileError: If file metadata cannot be read
    """
    try:
        stat = file_path.stat()
        file_size = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        return file_size, last_modified
    except OSError as e:
        raise FileError(
            f"Failed to get metadata for {file_path}", detail=str(e)
        )


def validate_file(file_path: Path) -> DocumentType:
    """Validate file exists, is readable, and determine document type.

    Args:
        file_path: Path to the file to validate

    Returns:
        DocumentType: The detected document type

    Raises:
        FileError: If file doesn't exist, isn't readable, or is too large
        FileTypeError: If file type is not supported
    """
    # Check if file exists
    if not file_path.exists():
        raise FileError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileError(f"Not a file: {file_path}")

    # Check file size (warn if > 10MB)
    try:
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            # Just log warning, don't raise error
            pass
    except OSError as e:
        raise FileError(f"Cannot access file: {file_path}", detail=str(e))

    # Determine document type
    return get_document_type(file_path)


def get_document_type(file_path: Path) -> DocumentType:
    """Determine the document type from a file path.

    Args:
        file_path: Path to the document file

    Returns:
        DocumentType: The document type

    Raises:
        FileTypeError: If file type is not supported
    """
    SUPPORTED_TYPES = {
        ".pdf": DocumentType.PDF,
        ".png": DocumentType.PNG,
        ".jpg": DocumentType.JPG,
        ".jpeg": DocumentType.JPEG,
        ".tiff": DocumentType.TIFF,
        ".docx": DocumentType.DOCX,
    }

    ext = file_path.suffix.lower()
    doc_type = SUPPORTED_TYPES.get(ext)

    if doc_type is None:
        raise FileTypeError(f"Unsupported file type: {ext}")

    return doc_type
