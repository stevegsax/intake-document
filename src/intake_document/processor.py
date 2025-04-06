"""Document processing functionality."""

import logging
from pathlib import Path
from typing import List, Optional

from src.intake_document.config import config
from src.intake_document.models.document import Document, DocumentType
from src.intake_document.ocr import MistralOCR
from src.intake_document.renderer import MarkdownRenderer


class DocumentProcessor:
    """Handles processing of documents through OCR and conversion."""

    def __init__(self) -> None:
        """Initialize the document processor."""
        self.logger = logging.getLogger(__name__)
        self.ocr = MistralOCR()
        self.renderer = MarkdownRenderer()

        # Ensure output directory exists
        output_dir = Path(config.settings.app.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    def _get_document_type(self, file_path: Path) -> Optional[DocumentType]:
        """Determine the document type from a file path.

        Args:
            file_path: Path to the document file

        Returns:
            Optional[DocumentType]: The document type or None if unsupported
        """
        # Get the file extension (lowercase)
        ext = file_path.suffix.lower().lstrip(".")

        # Try to map to a DocumentType
        try:
            return DocumentType(ext)
        except ValueError:
            self.logger.warning(f"Unsupported file type: {ext}")
            return None

    def process_file(self, file_path: Path) -> Path:
        """Process a single document file.

        Args:
            file_path: Path to the document file

        Returns:
            Path: Path to the output markdown file

        Raises:
            ValueError: If the file type is not supported
        """
        self.logger.info(f"Processing file: {file_path}")

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get document type
        doc_type = self._get_document_type(file_path)
        if doc_type is None:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Create document model
        document = Document(path=file_path, file_type=doc_type)

        # Process with OCR
        self.logger.debug(f"Sending to OCR: {file_path}")
        document = self.ocr.process_document(document)

        # Convert to markdown
        self.logger.debug(f"Converting to markdown: {file_path}")
        document = self.renderer.render_markdown(document)

        # Save to output file
        output_path = self._get_output_path(file_path)
        self._save_markdown(document, output_path)

        return output_path

    def process_directory(self, dir_path: Path) -> List[Path]:
        """Process all supported documents in a directory.

        Args:
            dir_path: Path to the directory

        Returns:
            List[Path]: Paths to the output markdown files

        Raises:
            ValueError: If the directory doesn't exist
        """
        self.logger.info(f"Processing directory: {dir_path}")

        # Check if directory exists
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Not a valid directory: {dir_path}")

        # Process all supported files
        output_paths = []
        for file_path in dir_path.iterdir():
            if file_path.is_file():
                try:
                    # Skip if not a supported file type
                    if self._get_document_type(file_path) is None:
                        continue

                    # Process the file
                    output_path = self.process_file(file_path)
                    output_paths.append(output_path)
                except Exception as e:
                    self.logger.error(
                        f"Error processing {file_path}: {str(e)}"
                    )

        return output_paths

    def _get_output_path(self, input_path: Path) -> Path:
        """Get the output path for a processed document.

        Args:
            input_path: Path to the input document

        Returns:
            Path: Path where the markdown output will be saved
        """
        output_dir = Path(config.settings.app.output_dir)
        return output_dir / f"{input_path.stem}.md"

    def _save_markdown(self, document: Document, output_path: Path) -> None:
        """Save the markdown output to a file.

        Args:
            document: The document with markdown content
            output_path: Path where to save the markdown

        Raises:
            ValueError: If markdown content is missing
        """
        if document.markdown is None:
            raise ValueError("No markdown content to save")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(document.markdown)

        self.logger.info(f"Saved markdown to: {output_path}")
