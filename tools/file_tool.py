"""
file_tool.py
------------
Universal file operations toolkit capable of creating, reading, modifying,
and managing files across multiple formats including:
* Text files (.txt, .md)
* Data files (.csv, .json, .xml)
* Excel files (.xlsx)
* PowerPoint presentations (.pptx)
* Word documents (.docx)
* Code files (.py, .js, .cpp, etc.)

All write operations are sandboxed to the output/ directory defined in config.OUTPUT_FOLDER.
"""

import os
import csv
import json
import logging
from typing import Optional, List, Dict, Any
from smolagents import tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("file_tool")


def _get_safe_path(filename: str) -> str:
    full_path = os.path.abspath(filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    return full_path

def _log_action(action: str, details: str):
    logger.info(f"{action} | {details}")


@tool
def read_file(path: str) -> str:
    """
    Read and return the contents of a file (Text, Code, etc).

    Args:
        path: Absolute or relative path to the file.

    Returns:
        Full text content of the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@tool
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file inside the output/ directory.
    Use this for Text or Code files, adding comments/formatting where necessary.

    Args:
        filename: Name of the file to create or overwrite (no path prefix).
        content: Text content to write.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    _log_action("Write file", f"Written to {full_path}")
    return full_path

@tool
def append_file(filename: str, content: str) -> str:
    """
    Append content to an existing file in the output/ directory.

    Args:
        filename: Target filename inside output/.
        content: Text to append.

    Returns:
        Absolute path to the modified file.
    """
    full_path = _get_safe_path(filename)
    with open(full_path, "a", encoding="utf-8") as f:
        f.write(content)
    _log_action("Append file", f"Appended to {full_path}")
    return full_path

@tool
def list_files(directory: str) -> list:
    """
    List all files in the specified directory.

    Args:
        directory: Path to the directory to list.

    Returns:
        Filenames found in the directory.
    """
    return os.listdir(directory)

@tool
def delete_file(path: str) -> bool:
    """
    Delete a file at the given path (restricted to output/ directory).

    Args:
        path: Path to the file to delete.

    Returns:
        True if deletion succeeded.
    """
    if not os.path.isabs(path):
        path = _get_safe_path(path)
    try:
        if os.path.exists(path):
            os.remove(path)
            _log_action("Delete file", f"Deleted {path}")
        return True
    except Exception:
        return False

@tool
def read_json_file(path: str) -> dict:
    """
    Reads a JSON file safely, maintaining valid schema structure.

    Args:
        path: Path to the target JSON file.

    Returns:
        The dictionary representation of the JSON data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@tool
def write_json_file(filename: str, data: dict) -> str:
    """
    Writes valid JSON content to a file inside the output/ directory.
    Maintains clean key-value structure formatting.

    Args:
        filename: Name of the file to create or overwrite (e.g., 'data.json').
        data: Dictionary object to save as JSON.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    _log_action("Write JSON", f"Written to {full_path}")
    return full_path

@tool
def write_csv_file(filename: str, headers: list, rows: list) -> str:
    """
    Creates a CSV file inside the output/ directory ensuring consistent column counts.

    Args:
        filename: Name of the CSV file (e.g., 'data.csv').
        headers: List of column names.
        rows: List of rows, where each row is a list of values.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    with open(full_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)
    _log_action("Write CSV", f"Written to {full_path}")
    return full_path

@tool
def create_excel_file(filename: str, headers: list, rows: list) -> str:
    """
    Creates an Excel (.xlsx) file in the output/ directory maintaining tabular structure.
    Always creates at least one sheet and avoids empty rows.

    Args:
        filename: Name of the standard Excel file (e.g., 'report.xlsx').
        headers: Row headers representing the schema.
        rows: Grid data matching header columns.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    try:
        import xlsxwriter
        workbook = xlsxwriter.Workbook(full_path)
        worksheet = workbook.add_worksheet()
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)
        for row_num, row_data in enumerate(rows):
            for col_num, cell_data in enumerate(row_data):
                worksheet.write(row_num + 1, col_num, cell_data)
        workbook.close()
        _log_action("Create Excel", f"Written to {full_path}")
    except ImportError:
        raise ImportError("xlsxwriter is required for Excel creation. Install with: pip install XlsxWriter")
    return full_path

@tool
def create_word_document(filename: str, title: str, paragraphs: list) -> str:
    """
    Generates a structured Word (.docx) document inside the output/ directory.

    Args:
        filename: Name of the Word document (e.g., 'document.docx').
        title: Bolded heading 1 title.
        paragraphs: List of string paragraphs to insert sequentially.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    try:
        import docx
        doc = docx.Document()
        if title:
            doc.add_heading(title, 0)
        for p in paragraphs:
            doc.add_paragraph(p)
        doc.save(full_path)
        _log_action("Create Word", f"Written to {full_path}")
    except ImportError:
        raise ImportError("python-docx is required. Install with: pip install python-docx")
    return full_path

@tool
def create_ppt_presentation(filename: str, slide_title: str, bullet_points: list) -> str:
    """
    Generates a structured PowerPoint (.pptx) presentation inside the output/ directory.
    Creates a title slide and a content slide (ensuring clear bullet organization).

    Args:
        filename: Name of the presentation file (e.g., 'deck.pptx').
        slide_title: Header title for the presentation layout.
        bullet_points: Maximum list of 5 concise text bullet points.

    Returns:
        Absolute path to the written file.
    """
    full_path = _get_safe_path(filename)
    try:
        from pptx import Presentation
        prs = Presentation()
        
        # Title slide
        title_slide_layout = prs.slide_layouts[0]
        slide1 = prs.slides.add_slide(title_slide_layout)
        title = slide1.shapes.title
        subtitle = slide1.placeholders[1]
        title.text = slide_title
        subtitle.text = "Generated by Synergy Agent"

        # Content slide with bullets
        bullet_slide_layout = prs.slide_layouts[1]
        slide2 = prs.slides.add_slide(bullet_slide_layout)
        shapes = slide2.shapes
        title_shape = shapes.title
        body_shape = shapes.placeholders[1]

        title_shape.text = slide_title
        tf = body_shape.text_frame
        for point in bullet_points:
            p = tf.add_paragraph()
            p.text = point

        prs.save(full_path)
        _log_action("Create PPT", f"Written to {full_path}")
    except ImportError:
        raise ImportError("python-pptx is required. Install with: pip install python-pptx")
    return full_path

ALL_TOOLS = [
    read_file,
    write_file,
    append_file,
    list_files,
    delete_file,
    read_json_file,
    write_json_file,
    write_csv_file,
    create_excel_file,
    create_word_document,
    create_ppt_presentation
]
