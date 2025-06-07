"""File utility functions for document processing."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple

from intake_document.utils.exceptions import FileError


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
        raise FileError(f"Failed to calculate checksum for {file_path}", detail=str(e))


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
        raise FileError(f"Failed to get metadata for {file_path}", detail=str(e))