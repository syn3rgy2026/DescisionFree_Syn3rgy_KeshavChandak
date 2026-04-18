# OWNER: Person 2
"""
file_tool.py
------------
Provides safe file-system operations for the agent. All write operations
are sandboxed to the output/ directory defined in config.OUTPUT_FOLDER.
Supports reading, writing, appending, listing, and deleting files.
"""

import os
import config


def read_file(path: str) -> str:
    """
    Read and return the contents of a file.

    Args:
        path (str): Absolute or relative path to the file.

    Returns:
        str: Full text content of the file.
    """
    raise NotImplementedError("Person 2 will implement this")


def write_file(filename: str, content: str) -> str:
    """
    Write content to a file inside the output/ directory.

    Args:
        filename (str): Name of the file to create or overwrite (no path prefix).
        content (str): Text content to write.

    Returns:
        str: Absolute path to the written file.
    """
    raise NotImplementedError("Person 2 will implement this")


def append_file(filename: str, content: str) -> str:
    """
    Append content to an existing file in the output/ directory.

    Args:
        filename (str): Target filename inside output/.
        content (str): Text to append.

    Returns:
        str: Absolute path to the modified file.
    """
    raise NotImplementedError("Person 2 will implement this")


def list_files(directory: str) -> list:
    """
    List all files in the specified directory.

    Args:
        directory (str): Path to the directory to list.

    Returns:
        list[str]: Filenames found in the directory.
    """
    raise NotImplementedError("Person 2 will implement this")


def delete_file(path: str) -> bool:
    """
    Delete a file at the given path (restricted to output/ directory).

    Args:
        path (str): Path to the file to delete.

    Returns:
        bool: True if deletion succeeded.
    """
    raise NotImplementedError("Person 2 will implement this")
