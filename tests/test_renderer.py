"""Tests for the markdown renderer."""

from datetime import datetime

from intake_document.models.document import (
    Document,
    ElementType,
    ImageElement,
    TableElement,
    TextElement,
)
from intake_document.renderer import MarkdownRenderer


def test_render_heading():
    """Test rendering a heading element."""
    renderer = MarkdownRenderer()
    element = TextElement(
        element_type=ElementType.TEXT,
        element_index=0,
        content="Test Heading",
        level=2,
    )
    result = renderer._render_text_element(element)

    assert result == "## Test Heading"


def test_render_paragraph():
    """Test rendering a paragraph element."""
    renderer = MarkdownRenderer()
    element = TextElement(
        element_type=ElementType.TEXT,
        element_index=0,
        content="Test paragraph content.",
    )
    result = renderer._render_text_element(element)

    assert result == "Test paragraph content."


def test_render_list_item():
    """Test rendering a list item element."""
    renderer = MarkdownRenderer()
    element = TextElement(
        element_type=ElementType.TEXT,
        element_index=0,
        content="List item",
        is_list_item=True,
    )
    result = renderer._render_text_element(element)

    assert result == "- List item"


def test_render_table():
    """Test rendering a table element."""
    renderer = MarkdownRenderer()
    element = TableElement(
        element_type=ElementType.TABLE,
        element_index=0,
        headers=["Name", "Age", "Location"],
        rows=[
            ["Alice", "30", "New York"],
            ["Bob", "25", "San Francisco"],
        ],
    )
    result = renderer._render_table_element(element)

    expected = "| Name | Age | Location |\n| --- | --- | --- |\n| Alice | 30 | New York |\n| Bob | 25 | San Francisco |"
    assert result == expected


def test_render_image():
    """Test rendering an image element."""
    renderer = MarkdownRenderer()
    element = ImageElement(
        element_type=ElementType.IMAGE,
        element_index=0,
        image_id="img123",
        caption="Test Image",
    )
    result = renderer._render_image_element(element)

    assert result == "![Test Image](images/img123.png)"


def test_render_complete_document():
    """Test rendering a complete document with multiple elements."""
    renderer = MarkdownRenderer()

    # Create a test document with various elements
    document = Document(
        checksum="abc123def456",
        processed_at=datetime.now(),
        elements=[
            TextElement(
                element_type=ElementType.TEXT,
                element_index=0,
                content="Sample Document",
                level=1,
            ),
            TextElement(
                element_type=ElementType.TEXT,
                element_index=1,
                content="This is a sample paragraph.",
            ),
            TextElement(
                element_type=ElementType.TEXT,
                element_index=2,
                content="First item",
                is_list_item=True,
            ),
            TextElement(
                element_type=ElementType.TEXT,
                element_index=3,
                content="Second item",
                is_list_item=True,
            ),
            TableElement(
                element_type=ElementType.TABLE,
                element_index=4,
                headers=["Column 1", "Column 2"],
                rows=[["Data 1", "Data 2"], ["Data 3", "Data 4"]],
            ),
            ImageElement(
                element_type=ElementType.IMAGE,
                element_index=5,
                image_id="img001",
                caption="A sample image",
            ),
        ],
    )

    # Render the document
    result_doc = renderer.render_markdown(document)

    # Check that markdown was generated and stored in the document
    assert result_doc.markdown is not None

    # Verify content
    expected_markdown = (
        "# Sample Document\n\n"
        "This is a sample paragraph.\n\n"
        "- First item\n\n"
        "- Second item\n\n"
        "| Column 1 | Column 2 |\n"
        "| --- | --- |\n"
        "| Data 1 | Data 2 |\n"
        "| Data 3 | Data 4 |\n\n"
        "![A sample image](images/img001.png)"
    )

    assert result_doc.markdown == expected_markdown
