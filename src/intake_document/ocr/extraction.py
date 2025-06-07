"""Document element extraction from OCR text responses."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from intake_document.models.document import (
    DocumentElement,
    ElementType,
    ImageElement,
    TableElement,
    TextElement,
)
from intake_document.utils.exceptions import (
    OCRTextExtractionError,
    OCRTableExtractionError,
    OCRImageExtractionError
)


class ElementExtractor:
    """Extracts structured document elements from OCR text response."""

    def __init__(self) -> None:
        """Initialize the element extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_elements_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured document elements from text response.

        Args:
            text: The text content to process

        Returns:
            List[Dict[str, Any]]: List of document elements
            
        Raises:
            OCRTextExtractionError: If extraction fails
        """
        self.logger.debug(f"Extracting elements from text of length {len(text)}")

        if not text or len(text) < 10:
            self.logger.warning("Text too short for meaningful extraction")
            raise OCRTextExtractionError("Text too short for meaningful extraction")

        try:
            elements: List[Dict[str, Any]] = []
            lines = text.split("\n")

            # If the text doesn't contain any markdown formatting, treat it as a single paragraph
            if len(lines) == 1 and not re.search(r'[#|\-\*]', text):
                self.logger.debug("Text appears to be a single paragraph with no markdown")
                return [{"type": "paragraph", "content": text.strip()}]
                
            # Check if the text is an error message about not being able to process
            if "unable to" in text.lower() and "process" in text.lower() and "file" in text.lower():
                self.logger.warning("Response indicates inability to process the file")
                return [{"type": "paragraph", "content": "# " + text.strip()}]
            
            # Process lines to extract elements
            self._process_lines(lines, elements)
            
            if elements:
                self.logger.debug(f"Successfully extracted {len(elements)} elements from text")
                return elements
            else:
                self.logger.warning("No elements could be extracted from text")
                # If we couldn't extract elements but have text, create a single paragraph
                if text.strip():
                    return [{"type": "paragraph", "content": text.strip()}]
                raise OCRTextExtractionError("No elements could be extracted")

        except Exception as e:
            self.logger.error(f"Error extracting elements from text: {str(e)}")
            # Return the raw text as a paragraph if extraction fails
            if text.strip():
                return [{"type": "paragraph", "content": text.strip()}]
            raise OCRTextExtractionError("Failed to extract elements", detail=str(e))
    
    def _process_lines(self, lines: List[str], elements: List[Dict[str, Any]]) -> None:
        """Process lines of text to extract document elements.
        
        Args:
            lines: Lines of text to process
            elements: List to store extracted elements
        """
        current_text = ""
        in_table = False
        table_headers: List[str] = []
        table_rows: List[List[str]] = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                if current_text:
                    # Finish current paragraph if we have one
                    elements.append({"type": "paragraph", "content": current_text})
                    current_text = ""
                continue

            # Try to extract elements based on line format
            if self._try_extract_heading(line, elements, current_text):
                current_text = ""
                continue
                
            if self._try_extract_list_item(line, elements, current_text):
                current_text = ""
                continue
                
            # Table processing
            table_result = self._process_table_line(line, in_table, table_headers, table_rows)
            in_table, table_headers, table_rows, table_finished = table_result
            
            if table_finished and current_text:
                elements.append({"type": "paragraph", "content": current_text})
                current_text = ""
                continue
            elif in_table:
                if current_text:
                    elements.append({"type": "paragraph", "content": current_text})
                    current_text = ""
                continue
            elif table_finished:
                # Add the finished table to elements
                elements.append({
                    "type": "table",
                    "headers": table_headers,
                    "rows": table_rows,
                })
                continue

            # Check for image references ![alt](url)
            if self._try_extract_image(line, elements, current_text):
                current_text = ""
                continue

            # Regular text, append to current paragraph
            if current_text:
                current_text += " " + line
            else:
                current_text = line

        # Add any remaining text
        if current_text:
            elements.append({"type": "paragraph", "content": current_text})

        # Make sure we ended any open tables
        if in_table and table_headers and table_rows:
            elements.append({
                "type": "table",
                "headers": table_headers,
                "rows": table_rows,
            })
    
    def _try_extract_heading(self, line: str, elements: List[Dict[str, Any]], current_text: str) -> bool:
        """Try to extract a heading from the line.
        
        Args:
            line: Line to process
            elements: List to add the heading element to
            current_text: Current accumulated paragraph text
            
        Returns:
            bool: True if a heading was extracted, False otherwise
        """
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            # If we have accumulated text, add it first
            if current_text:
                elements.append({"type": "paragraph", "content": current_text})

            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            elements.append({"type": "heading", "level": level, "content": content})
            return True
        return False
    
    def _try_extract_list_item(self, line: str, elements: List[Dict[str, Any]], current_text: str) -> bool:
        """Try to extract a list item from the line.
        
        Args:
            line: Line to process
            elements: List to add the list item element to
            current_text: Current accumulated paragraph text
            
        Returns:
            bool: True if a list item was extracted, False otherwise
        """
        # Check for unordered list items
        list_match = re.match(r"^[-*]\s+(.+)$", line)
        if list_match:
            # If we have accumulated text, add it first
            if current_text:
                elements.append({"type": "paragraph", "content": current_text})

            content = list_match.group(1).strip()
            elements.append({"type": "list_item", "content": content})
            return True
            
        # Check for numbered list items
        numbered_list_match = re.match(r"^(\d+\.)\s+(.+)$", line)
        if numbered_list_match:
            # If we have accumulated text, add it first
            if current_text:
                elements.append({"type": "paragraph", "content": current_text})

            content = numbered_list_match.group(2).strip()
            elements.append({"type": "list_item", "content": content})
            return True
            
        return False
    
    def _process_table_line(self, line: str, in_table: bool, table_headers: List[str], 
                          table_rows: List[List[str]]) -> Tuple[bool, List[str], List[List[str]], bool]:
        """Process a line that might be part of a table.
        
        Args:
            line: Line to process
            in_table: Whether we're currently in a table
            table_headers: Current table headers
            table_rows: Current table rows
            
        Returns:
            Tuple[bool, List[str], List[List[str]], bool]: Updated in_table, headers, rows, and whether table finished
        """
        table_finished = False
        
        # Table headers: | Column1 | Column2 |
        table_header_match = re.match(r"^\|(.+)\|$", line)
        if table_header_match and not in_table:
            # Extract headers
            header_cells = [cell.strip() for cell in table_header_match.group(1).split("|")] 
            return True, header_cells, [], False

        # Table rows
        if in_table and re.match(r"^\|(.+)\|$", line):
            cells = [cell.strip() for cell in line[1:-1].split("|")] 
            # Check if this is the separator row
            if all(cell == "" or re.match(r"^[-:]+$", cell) for cell in cells):
                # This is the separator row in markdown tables
                return in_table, table_headers, table_rows, False

            # Process normal row
            # Ensure the row has the same number of columns as headers
            if len(cells) != len(table_headers):
                if len(cells) < len(table_headers):
                    # Pad with empty cells if needed
                    cells.extend([""] * (len(table_headers) - len(cells)))
                else:
                    # Truncate if too many cells
                    cells = cells[:len(table_headers)]
                
            table_rows.append(cells)
            return in_table, table_headers, table_rows, False
        elif in_table:
            # End of table
            table_finished = True
            in_table = False
            return False, [], [], True
            
        return in_table, table_headers, table_rows, False
    
    def _try_extract_image(self, line: str, elements: List[Dict[str, Any]], current_text: str) -> bool:
        """Try to extract an image reference from the line.
        
        Args:
            line: Line to process
            elements: List to add the image element to
            current_text: Current accumulated paragraph text
            
        Returns:
            bool: True if an image was extracted, False otherwise
        """
        image_match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image_match:
            if current_text:
                elements.append({"type": "paragraph", "content": current_text})

            caption = image_match.group(1)
            image_url = image_match.group(2)
            image_id = re.sub(r"^.*/", "", image_url.split(".")[0])

            elements.append({"type": "image", "id": image_id, "caption": caption})
            return True
        return False
    
    def fix_table_orientation(self, headers: List[str], rows: List[List[str]]) -> Tuple[List[str], List[List[str]]]:
        """Fix table orientation if needed.
        
        Sometimes OCR might interpret columns as rows. This method detects and fixes that.
        
        Args:
            headers: The table headers
            rows: The table rows
            
        Returns:
            Tuple[List[str], List[List[str]]]: Corrected headers and rows
            
        Raises:
            OCRTableExtractionError: If table processing fails
        """
        try:
            # If we have no rows, return as is
            if not rows:
                return headers, rows
                
            # Check if the table might be transposed
            # Heuristic: If we have more columns than rows, and the number of columns is small (< 10)
            # it's more likely to be a normal table. If we have many columns (> 10) and few rows,
            # it might be transposed.
            num_cols = len(headers)
            num_rows = len(rows)
            
            # Don't transpose small tables or tables with more rows than columns
            if num_cols <= 10 or num_rows >= num_cols:
                return headers, rows
                
            self.logger.debug(f"Table might be transposed: {num_cols} columns, {num_rows} rows")
            
            # Transpose the table
            transposed_headers = ["Column " + str(i+1) for i in range(num_rows)]
            transposed_rows = []
            
            # Create the first row from the headers
            first_row = [headers[0]]
            for row in rows:
                if row and len(row) > 0:
                    first_row.append(row[0])
                    
            transposed_rows.append(first_row)
            
            # Create the rest of the rows
            for i in range(1, num_cols):
                if i < len(headers):
                    new_row = [headers[i]]
                    for row in rows:
                        if i < len(row):
                            new_row.append(row[i])
                        else:
                            new_row.append("")
                    transposed_rows.append(new_row)
            
            self.logger.debug(f"Transposed table: {len(transposed_headers)} columns, {len(transposed_rows)} rows")
            return transposed_headers, transposed_rows
            
        except Exception as e:
            self.logger.error(f"Error fixing table orientation: {str(e)}")
            raise OCRTableExtractionError("Failed to fix table orientation", detail=str(e))
    
    def parse_response(self, response: Dict[str, Any]) -> List[DocumentElement]:
        """Parse extracted elements into document elements.

        Args:
            response: The dictionary with extracted elements

        Returns:
            List[DocumentElement]: List of parsed document elements
            
        Raises:
            OCRTextExtractionError: If parsing fails
        """
        self.logger.debug("Parsing elements into document elements")

        elements: List[DocumentElement] = []
        
        try:
            # Parse each element from the response
            for index, elem in enumerate(response.get("elements", [])):
                elem_type = elem.get("type", "")

                if elem_type == "heading":
                    elements.append(
                        TextElement(
                            element_type=ElementType.TEXT,
                            element_index=index,
                            content=elem["content"],
                            level=elem["level"],
                        )
                    )
                elif elem_type == "paragraph":
                    elements.append(
                        TextElement(
                            element_type=ElementType.TEXT,
                            element_index=index,
                            content=elem["content"],
                        )
                    )
                elif elem_type == "list_item":
                    elements.append(
                        TextElement(
                            element_type=ElementType.TEXT,
                            element_index=index,
                            content=elem["content"],
                            is_list_item=True,
                        )
                    )
                elif elem_type == "table":
                    try:
                        # Fix table orientation if needed
                        headers, rows = self.fix_table_orientation(
                            elem["headers"], elem["rows"]
                        )
                        elements.append(
                            TableElement(
                                element_type=ElementType.TABLE,
                                element_index=index,
                                headers=headers,
                                rows=rows,
                            )
                        )
                    except OCRTableExtractionError as e:
                        self.logger.warning(f"Table extraction failed: {str(e)}")
                        # Continue processing other elements
                elif elem_type == "image":
                    try:
                        elements.append(
                            ImageElement(
                                element_type=ElementType.IMAGE,
                                element_index=index,
                                image_id=elem["id"],
                                caption=elem.get("caption"),
                            )
                        )
                    except Exception as e:
                        self.logger.warning(f"Image extraction failed: {str(e)}")
                        # Continue processing other elements
            
            return elements
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            raise OCRTextExtractionError("Failed to parse response", detail=str(e))