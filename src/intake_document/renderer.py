"""Markdown rendering for document elements."""

import logging

from src.intake_document.models.document import (
    Document,
    ImageElement,
    TableElement,
    TextElement,
)


class MarkdownRenderer:
    """Renderer for converting document elements to markdown."""

    def __init__(self) -> None:
        """Initialize the markdown renderer."""
        self.logger = logging.getLogger(__name__)

    def render_markdown(self, document: Document) -> Document:
        """Render a document's elements as markdown.

        Args:
            document: The document to render

        Returns:
            Document: The document with added markdown content
        """
        self.logger.debug(f"Rendering markdown for document: {document.path}")

        # Start with an empty string
        markdown = ""

        # Process each element in the document
        for element in document.elements:
            # Add spacing between elements
            if markdown:
                markdown += "\n\n"

            # Render the element based on its type
            if isinstance(element, TextElement):
                markdown += self._render_text_element(element)
            elif isinstance(element, TableElement):
                markdown += self._render_table_element(element)
            elif isinstance(element, ImageElement):
                markdown += self._render_image_element(element)

        # Store the markdown in the document
        document.markdown = markdown

        return document

    def _render_text_element(self, element: TextElement) -> str:
        """Render a text element as markdown.

        Args:
            element: The text element to render

        Returns:
            str: The markdown representation
        """
        # If it's a heading, add the appropriate number of # symbols
        if element.level is not None and 1 <= element.level <= 6:
            return f"{'#' * element.level} {element.content}"

        # If it's a list item, prefix with - or *
        if element.is_list_item:
            return f"- {element.content}"

        # Otherwise it's a regular paragraph
        return element.content

    def _render_table_element(self, element: TableElement) -> str:
        """Render a table element as markdown.

        Args:
            element: The table element to render

        Returns:
            str: The markdown representation
        """
        # Create header row
        md_table = "| " + " | ".join(element.headers) + " |\n"

        # Create separator row
        md_table += "| " + " | ".join(["---"] * len(element.headers)) + " |\n"

        # Create data rows
        for row in element.rows:
            md_table += "| " + " | ".join(row) + " |\n"

        return md_table.rstrip()  # Remove trailing newline

    def _render_image_element(self, element: ImageElement) -> str:
        """Render an image element as markdown.

        Args:
            element: The image element to render

        Returns:
            str: The markdown representation
        """
        # Use standard markdown image syntax
        alt_text = element.caption if element.caption else "Image"
        return f"![{alt_text}](images/{element.image_id}.png)"
