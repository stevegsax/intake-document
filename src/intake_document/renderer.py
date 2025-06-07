"""Markdown rendering for document elements."""

import logging

# Local application imports
from intake_document.models.document import (
    Document,
    DocumentElement,
    ImageElement,
    TableElement,
    TextElement,
)
from intake_document.utils.exceptions import RenderError


class MarkdownRenderer:
    """Renderer for converting document elements to markdown."""

    def __init__(self) -> None:
        """Initialize the markdown renderer."""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MarkdownRenderer initialized")

    def render_markdown(self, document: Document) -> Document:
        """Render a document's elements as markdown.

        Args:
            document: The document to render

        Returns:
            Document: The document with added markdown content

        Raises:
            RenderError: If rendering fails
        """

        try:
            # Start with an empty string
            markdown = ""

            # Check if we have elements to render
            if not document.elements:
                self.logger.warning("No elements to render in document")

            # Process each element in the document
            for i, element in enumerate(document.elements):
                # Add spacing between elements
                if markdown:
                    markdown += "\n\n"

                try:
                    # Render the element based on its type
                    self.logger.debug(
                        f"Rendering element {i + 1}/{len(document.elements)}: {element.element_type}"
                    )

                    if isinstance(element, TextElement):
                        markdown += self._render_text_element(element)
                    elif isinstance(element, TableElement):
                        markdown += self._render_table_element(element)
                    elif isinstance(element, ImageElement):
                        markdown += self._render_image_element(element)
                    else:
                        self.logger.warning(
                            f"Unknown element type: {type(element)}"
                        )
                        markdown += f"<!-- Unsupported element type: {type(element).__name__} -->"

                except Exception as e:
                    # Log the error but continue with other elements
                    error_msg = f"Failed to render element {i + 1}"
                    self.logger.error(f"{error_msg}: {str(e)}")

                    # Add a comment in the markdown noting the error
                    markdown += (
                        f"\n\n<!-- Error rendering element: {str(e)} -->\n\n"
                    )

            # Store the markdown in the document
            document.markdown = markdown

            return document

        except Exception as e:
            error_msg = (
                f"Failed to render markdown for document: {document.checksum[:16]}..."
            )
            self.logger.error(f"{error_msg}: {str(e)}")
            raise RenderError(error_msg, detail=str(e))

    def _render_text_element(self, element: TextElement) -> str:
        """Render a text element as markdown.

        Args:
            element: The text element to render

        Returns:
            str: The markdown representation

        Raises:
            RenderError: If the element has invalid properties
        """
        self.logger.debug(f"Rendering text element: {element.content[:20]}...")

        # Validate content
        if not element.content:
            self.logger.warning("Empty content in text element")
            return ""

        # If it's a heading, add the appropriate number of # symbols
        if element.level is not None:
            if 1 <= element.level <= 6:
                self.logger.debug(
                    f"Rendering as level {element.level} heading"
                )
                return f"{'#' * element.level} {element.content}"
            else:
                self.logger.warning(
                    f"Invalid heading level: {element.level}, treating as paragraph"
                )
                return element.content

        # If it's a list item, prefix with - or *
        if element.is_list_item:
            self.logger.debug("Rendering as list item")
            return f"- {element.content}"

        # Otherwise it's a regular paragraph
        self.logger.debug("Rendering as paragraph")
        return element.content

    def _render_table_element(self, element: TableElement) -> str:
        """Render a table element as markdown.

        Args:
            element: The table element to render

        Returns:
            str: The markdown representation

        Raises:
            RenderError: If the table structure is invalid
        """
        self.logger.debug(
            f"Rendering table with {len(element.headers)} columns, {len(element.rows)} rows"
        )

        # Validate table structure
        if not element.headers:
            error_msg = "Table has no headers"
            self.logger.error(error_msg)
            raise RenderError(error_msg)

        # Make sure all rows have the same number of columns as headers
        for i, row in enumerate(element.rows):
            if len(row) != len(element.headers):
                self.logger.warning(
                    f"Row {i + 1} has {len(row)} columns, but table has {len(element.headers)} headers. "
                    "Adjusting row to match."
                )
                # Pad or truncate row to match header count
                if len(row) < len(element.headers):
                    row.extend([""] * (len(element.headers) - len(row)))
                else:
                    row = row[: len(element.headers)]

        try:
            # Create header row
            md_table = "| " + " | ".join(element.headers) + " |\n"

            # Create separator row
            md_table += (
                "| " + " | ".join(["---"] * len(element.headers)) + " |\n"
            )

            # Create data rows
            for row in element.rows:
                # Escape pipe characters in cell content to avoid breaking the table
                escaped_row = [cell.replace("|", "\\|") for cell in row]
                md_table += "| " + " | ".join(escaped_row) + " |\n"

            return md_table.rstrip()  # Remove trailing newline

        except Exception as e:
            error_msg = "Failed to render table element"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise RenderError(error_msg, detail=str(e))

    def _render_image_element(self, element: ImageElement) -> str:
        """Render an image element as markdown.

        Args:
            element: The image element to render

        Returns:
            str: The markdown representation

        Raises:
            RenderError: If the image element has invalid properties
        """
        self.logger.debug(f"Rendering image element: {element.image_id}")

        # Validate image ID
        if not element.image_id:
            error_msg = "Image element missing image_id"
            self.logger.error(error_msg)
            raise RenderError(error_msg)

        try:
            # Use standard markdown image syntax
            alt_text = element.caption if element.caption else "Image"
            self.logger.debug(f"Using alt text: {alt_text}")

            return f"![{alt_text}](images/{element.image_id}.png)"

        except Exception as e:
            error_msg = "Failed to render image element"
            self.logger.error(f"{error_msg}: {str(e)}")
            raise RenderError(error_msg, detail=str(e))

    def get_element_type_name(self, element: DocumentElement) -> str:
        """Get a human-readable name for an element type.

        Args:
            element: The document element

        Returns:
            str: Human-readable element type name
        """
        if isinstance(element, TextElement):
            if element.level is not None and 1 <= element.level <= 6:
                return f"Heading (Level {element.level})"
            elif element.is_list_item:
                return "List Item"
            else:
                return "Paragraph"
        elif isinstance(element, TableElement):
            return f"Table ({len(element.headers)} columns, {len(element.rows)} rows)"
        elif isinstance(element, ImageElement):
            return f"Image: {element.caption or element.image_id}"
        else:
            return element.element_type
