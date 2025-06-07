"""Document processing functionality."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Local application imports
from intake_document.config import config
from intake_document.models.document import Document, DocumentInstance, DocumentType
from intake_document.ocr import MistralOCR
from intake_document.renderer import MarkdownRenderer
from intake_document.utils.exceptions import DocumentError, FileTypeError
from intake_document.utils.file_utils import calculate_sha512, get_file_metadata


class DocumentProcessor:
    """Handles processing of documents through OCR and conversion."""

    def __init__(self) -> None:
        """Initialize the document processor.

        Raises:
            DocumentError: If the output directory cannot be created
        """
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing DocumentProcessor")

        self.ocr = MistralOCR()
        self.renderer = MarkdownRenderer()
        
        # Cache for processed documents to avoid reprocessing
        self._processed_documents: Dict[str, Document] = {}

        # Ensure output directory exists
        try:
            output_dir = Path(config.settings.app.output_dir)
            self.logger.debug(
                f"Creating output directory if needed: {output_dir}"
            )
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            error_msg = f"Failed to create output directory: {output_dir}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise DocumentError(error_msg, detail=str(e))

        self.logger.info(
            f"DocumentProcessor initialized with output directory: {output_dir}"
        )

    def _get_document_type(self, file_path: Path) -> Optional[DocumentType]:
        """Determine the document type from a file path.

        Args:
            file_path: Path to the document file

        Returns:
            Optional[DocumentType]: The document type or None if unsupported
        """
        # Get the file extension (lowercase)
        ext = file_path.suffix.lower().lstrip(".")
        self.logger.debug(f"Determining document type for extension: {ext}")

        # Try to map to a DocumentType
        try:
            doc_type = DocumentType(ext)
            self.logger.debug(f"Mapped to document type: {doc_type}")
            return doc_type
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
            DocumentError: If the document processing fails
            FileTypeError: If the file type is not supported
            FileNotFoundError: If the file doesn't exist
        """
        self.logger.info(f"Processing file: {file_path}")

        # Check if file exists
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Check file size
        try:
            file_size = file_path.stat().st_size
            self.logger.debug(f"File size: {file_size / 1024:.2f} KB")

            # Warn if file is very large (e.g., > 10MB)
            if file_size > 10 * 1024 * 1024:
                self.logger.warning(
                    f"Large file detected ({file_size / 1024 / 1024:.2f} MB), processing may take longer"
                )
        except OSError as e:
            self.logger.warning(f"Could not determine file size: {str(e)}")

        # Get document type
        doc_type = self._get_document_type(file_path)
        if doc_type is None:
            error_msg = f"Unsupported file type: {file_path.suffix}"
            self.logger.error(error_msg)
            raise FileTypeError(error_msg)

        try:
            # Create document instance
            self.logger.debug(f"Creating document instance for: {file_path}")
            checksum = calculate_sha512(file_path)
            file_size, last_modified = get_file_metadata(file_path)
            
            document_instance = DocumentInstance(
                path=file_path,
                file_type=doc_type,
                checksum=checksum,
                file_size=file_size,
                last_modified=last_modified
            )
            self.logger.debug(f"Document checksum: {checksum}")
            
            # Check if we already have processed this document
            if checksum in self._processed_documents:
                self.logger.info(f"Document already processed, using cached result: {checksum[:16]}...")
                document = self._processed_documents[checksum]
                document_instance.processed_at = document.processed_at
            else:
                # Process with OCR
                self.logger.debug(f"Sending to OCR: {file_path}")
                document = self.ocr.process_document(document_instance)
                self.logger.info(
                    f"OCR processing complete: {len(document.elements)} elements extracted"
                )
                
                # Convert to markdown
                self.logger.debug(f"Converting to markdown: {file_path}")
                document = self.renderer.render_markdown(document)
                
                # Cache the processed document
                self._processed_documents[checksum] = document
                document_instance.processed_at = document.processed_at

            if document.markdown:
                self.logger.debug(
                    f"Markdown generated: {len(document.markdown)} characters"
                )
            else:
                self.logger.warning("No markdown content generated")

            # Save to output file
            output_path = self._get_output_path(file_path)
            self._save_markdown(document, output_path)
            self.logger.info(
                f"Document processing complete: {file_path} → {output_path}"
            )

            return output_path

        except Exception as e:
            error_msg = f"Failed to process document: {file_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise DocumentError(error_msg, detail=str(e))

    def process_directory(self, dir_path: Path) -> List[Path]:
        """Process all supported documents in a directory.

        Args:
            dir_path: Path to the directory

        Returns:
            List[Path]: Paths to the output markdown files

        Raises:
            DocumentError: If the directory doesn't exist or cannot be read
        """
        self.logger.info(f"Processing directory: {dir_path}")

        # Check if directory exists
        if not dir_path.exists() or not dir_path.is_dir():
            error_msg = f"Not a valid directory: {dir_path}"
            self.logger.error(error_msg)
            raise DocumentError(error_msg)

        try:
            # List all files in the directory
            file_count = sum(1 for _ in dir_path.iterdir() if _.is_file())
            self.logger.debug(f"Found {file_count} files in directory")

            # Track processing statistics
            stats = {
                "processed": 0,
                "skipped": 0,
                "failed": 0,
                "total": file_count,
            }

            # Process all supported files
            output_paths = []
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    try:
                        # Check if file type is supported
                        if self._get_document_type(file_path) is None:
                            self.logger.debug(
                                f"Skipping unsupported file: {file_path}"
                            )
                            stats["skipped"] += 1
                            continue

                        # Process the file
                        self.logger.debug(
                            f"Processing file {stats['processed'] + stats['skipped'] + stats['failed'] + 1}/{file_count}: {file_path}"
                        )
                        output_path = self.process_file(file_path)
                        output_paths.append(output_path)
                        stats["processed"] += 1

                    except Exception as e:
                        stats["failed"] += 1
                        self.logger.error(
                            f"Error processing {file_path}: {str(e)}"
                        )

            # Log processing summary
            self.logger.info(
                f"Directory processing complete: "
                f"{stats['processed']} processed, {stats['skipped']} skipped, "
                f"{stats['failed']} failed, {stats['total']} total"
            )

            return output_paths

        except OSError as e:
            error_msg = f"Error reading directory: {dir_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise DocumentError(error_msg, detail=str(e))

    def _get_output_path(self, input_path: Path) -> Path:
        """Get the output path for a processed document.

        Args:
            input_path: Path to the input document

        Returns:
            Path: Path where the markdown output will be saved
        """
        output_dir = Path(config.settings.app.output_dir)
        output_path = output_dir / f"{input_path.stem}.md"
        self.logger.debug(f"Output path for {input_path}: {output_path}")
        return output_path

    def _save_markdown(self, document: Document, output_path: Path) -> None:
        """Save the markdown output to a file.

        Args:
            document: The document with markdown content
            output_path: Path where to save the markdown

        Raises:
            DocumentError: If markdown content is missing or file cannot be written
        """
        if document.markdown is None:
            error_msg = "No markdown content to save"
            self.logger.error(error_msg)
            raise DocumentError(error_msg)

        try:
            # Ensure parent directory exists
            self.logger.debug(
                f"Creating output directory if needed: {output_path.parent}"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Calculate estimated size
            estimated_size = len(document.markdown) / 1024
            self.logger.debug(
                f"Writing approximately {estimated_size:.2f} KB to {output_path}"
            )

            # Write markdown to file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(document.markdown)

            # Verify file was written
            if not output_path.exists():
                error_msg = f"File was not written: {output_path}"
                self.logger.error(error_msg)
                raise DocumentError(error_msg)

            # Get actual file size
            actual_size = output_path.stat().st_size / 1024
            self.logger.debug(f"Wrote {actual_size:.2f} KB to {output_path}")

            self.logger.info(f"Saved markdown to: {output_path}")

        except OSError as e:
            error_msg = f"Failed to save markdown to {output_path}"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise DocumentError(error_msg, detail=str(e))
