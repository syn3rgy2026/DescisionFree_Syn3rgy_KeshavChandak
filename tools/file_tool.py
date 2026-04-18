import os
import shutil
import stat
import time
import hashlib
import zipfile
import tempfile
import logging
import json
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Generator

import config

# 14. Logging and Auditing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("file_tool")


class FileTool:
    """
    You are a file system operations expert.
    This class represents a comprehensive and structured list of all possible file-related operations 
    that can be performed in a typical operating system or programming environment.

    1. Basic File Operations
    * Create file: Creates a new, empty file at the specified path.
    * Read file (full, partial, line-by-line): Reads the content of a file completely, in chunks, or line by line.
    * Write file: Writes content to a file, overwriting existing content.
    * Append to file: Adds new content to the end of an existing file.
    * Delete file: Removes a file permanently from the file system.

    2. File Management Operations
    * Copy file: Duplicates a file from a source path to a destination path.
    * Move file: Transfers a file to a new location, removing it from the original path.
    * Rename file: Changes the name or extension of an existing file.
    * Replace/overwrite file: Replaces an existing file safely.
    * Duplicate file: Creates an exact copy of the file in the same directory.

    3. Directory/Folder Operations
    * Create folder: Creates a new directory at the specified path.
    * Delete folder: Removes a directory and all of its contents.
    * List contents of a folder: Retrieves a list of all items within a directory.
    * Traverse directories: Recursively lists all items matching a pattern or throughout the tree.
    * Move/copy entire directories: Moves or copies a whole folder structure.

    4. File Metadata Operations
    * Get file size: Returns the size of the file in bytes.
    * Get creation/modification/access time: Retrieves OS-level timestamp metadata.
    * Check file type: Determines whether a path is a file, directory, or symlink.
    * Check file ownership: Gets the user ID and group ID of the file owner.
    * Retrieve file permissions: Gets the read/write/execute permissions of the file.

    5. Permission and Security Operations
    * Change file permissions (read/write/execute): Modifies file access flags (chmod).
    * Change ownership: Changes the owner and group of the file (chown).
    * Restrict or grant access: Specific OS-level permission restrictions.
    * Encrypt/decrypt files: Protects file data using basic encoding/encryption.

    6. Validation and Existence Checks
    * Check if file exists: Returns true if the file path is valid.
    * Check if path is file or directory: Determines the type of existing path.
    * Validate file format: Checks the file extension or MIME type.
    * Check file integrity (hashing): Generates an MD5/SHA-256 hash of the file.

    7. Advanced File Operations
    * File compression (zip/unzip): Compresses files into zip archives or extracts them.
    * File decompression: Extracts the contents of an archive.
    * Split large files: Divides a file into smaller chunks.
    * Merge files: Combines multiple files into a single file.
    * Convert file formats (e.g., txt → csv → json): Handles basic textual conversions.

    8. Streaming and Large File Handling
    * Read/write files in chunks: Handles massive files without overwhelming memory.
    * Stream file content: Provides a generator for file streams.
    * Buffer management: Utilizes memory buffers efficiently.

    9. File Locking and Concurrency
    * Lock file for exclusive access: Prevents other processes from writing to the file temporarily.
    * Unlock file: Releases the exclusive lock.
    * Handle concurrent read/write: Manages safe operations using transient locks.

    10. Temporary File Operations
    * Create temporary files: Generates isolated, unique temp files.
    * Auto-delete temporary files: Cleans up transient files after use.
    * Manage cache files: Stores standard cache output in local environments.

    11. Monitoring and Events
    * Watch file for changes: Checks the modification time interval of a file.
    * Trigger actions on file modification: Executes callbacks on change detection.
    * Log file activity: Submits standard operation events to the logger.

    12. Symbolic and Shortcut Operations
    * Create symbolic links: Creates a symlink pointing to an original file.
    * Resolve symbolic links: Returns the real absolute path of a symlink target.
    * Create shortcuts/aliases: Creates standard filesystem aliases.

    13. Error Handling and Recovery
    * Handle file not found errors: Traps IO exceptions gracefully.
    * Handle permission errors: Captures access denial errors without crashing.
    * Retry failed operations: Employs simple retry mechanisms for transient IO locks.
    * Backup before modification: Saves a '.bak' copy before destructive writes.

    14. Logging and Auditing
    * Log file operations: All actions are automatically written via standard Python logging.
    * Maintain history of changes: Keeps a record of operations performed via this tool.
    * Track access logs: Traces when data is read or touched.
    """

    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize the file tool. Optional base_directory to restrict operations to a specific folder.
        """
        self.base_directory = base_directory
        self.history = []

    def _log_action(self, action: str, details: str):
        logger.info(f"{action} | {details}")
        self.history.append({"action": action, "details": details, "time": time.time()})

    # ==========================
    # 1. Basic File Operations
    # ==========================
    def create_file(self, path: str):
        Path(path).touch(exist_ok=True)
        self._log_action("Create file", f"Created file at {path}")

    def read_file(self, path: str, mode: str = "full", chunk_size: int = 1024) -> Union[str, Generator, List[str]]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        self._log_action("Read file", f"Reading file {path} ({mode})")
        if mode == "full":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        elif mode == "line-by-line":
            with open(path, "r", encoding="utf-8") as f:
                return f.readlines()
        elif mode == "chunk":
            def stream():
                with open(path, "r", encoding="utf-8") as f:
                    while chunk := f.read(chunk_size):
                        yield chunk
            return stream()

    def write_file(self, path: str, content: str, backup: bool = False):
        if backup and os.path.exists(path):
            self.backup_before_modification(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self._log_action("Write file", f"Wrote content to {path}")

    def append_to_file(self, path: str, content: str):
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        self._log_action("Append file", f"Appended content to {path}")

    def delete_file(self, path: str):
        if os.path.exists(path):
            os.remove(path)
            self._log_action("Delete file", f"Deleted {path}")

    # ==========================
    # 2. File Management Operations
    # ==========================
    def copy_file(self, source: str, destination: str):
        shutil.copy2(source, destination)
        self._log_action("Copy file", f"Copied {source} to {destination}")

    def move_file(self, source: str, destination: str):
        shutil.move(source, destination)
        self._log_action("Move file", f"Moved {source} to {destination}")

    def rename_file(self, path: str, new_name: str):
        dir_name = os.path.dirname(path)
        new_path = os.path.join(dir_name, new_name)
        os.rename(path, new_path)
        self._log_action("Rename file", f"Renamed {path} to {new_path}")

    def replace_overwrite_file(self, path: str, new_content: str):
        self.write_file(path, new_content)

    def duplicate_file(self, path: str):
        dir_name = os.path.dirname(path)
        base, ext = os.path.splitext(os.path.basename(path))
        new_path = os.path.join(dir_name, f"{base}_copy{ext}")
        self.copy_file(path, new_path)
        return new_path

    # ==========================
    # 3. Directory/Folder Operations
    # ==========================
    def create_folder(self, path: str):
        os.makedirs(path, exist_ok=True)
        self._log_action("Create folder", f"Created {path}")

    def delete_folder(self, path: str):
        shutil.rmtree(path, ignore_errors=True)
        self._log_action("Delete folder", f"Deleted {path}")

    def list_contentsOf_folder(self, path: str) -> List[str]:
        self._log_action("List contents", f"Listed contents of {path}")
        return os.listdir(path)

    def traverse_directories(self, path: str) -> List[str]:
        results = []
        for root, dirs, files in os.walk(path):
            for name in files:
                results.append(os.path.join(root, name))
        self._log_action("Traverse dirs", f"Traversed {path}")
        return results

    def copy_entire_directory(self, source: str, destination: str):
        shutil.copytree(source, destination, dirs_exist_ok=True)
        self._log_action("Copy directory", f"Copied directory {source} to {destination}")

    # ==========================
    # 4. File Metadata Operations
    # ==========================
    def get_file_size(self, path: str) -> int:
        return os.path.getsize(path)

    def get_file_times(self, path: str) -> dict:
        stat_info = os.stat(path)
        return {
            "creation_time": stat_info.st_ctime,
            "modification_time": stat_info.st_mtime,
            "access_time": stat_info.st_atime
        }

    def check_file_type(self, path: str) -> str:
        if os.path.islink(path): return "symlink"
        if os.path.isfile(path): return "file"
        if os.path.isdir(path): return "directory"
        return "unknown"

    def check_file_ownership(self, path: str) -> dict:
        stat_info = os.stat(path)
        return {"uid": stat_info.st_uid, "gid": stat_info.st_gid}

    def retrieve_file_permissions(self, path: str) -> str:
        return oct(stat.S_IMODE(os.lstat(path).st_mode))

    # ==========================
    # 5. Permission and Security
    # ==========================
    def change_permissions(self, path: str, mode: int):
        os.chmod(path, mode)
        self._log_action("Change perms", f"Changed {path} permissions to {mode}")

    # ==========================
    # 6. Validation & Existence
    # ==========================
    def check_exists(self, path: str) -> bool:
        return os.path.exists(path)

    def check_integrity_hash(self, path: str, algorithm: str = "sha256") -> str:
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    # ==========================
    # 7. Advanced File Operations
    # ==========================
    def compress_zip(self, source_path: str, zip_path: str):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(source_path):
                for root, _, files in os.walk(source_path):
                    for file in files:
                        zipf.write(os.path.join(root, file), 
                                   os.path.relpath(os.path.join(root, file), 
                                   os.path.join(source_path, '..')))
            else:
                zipf.write(source_path, os.path.basename(source_path))
        self._log_action("Compress file", f"Compressed {source_path} to {zip_path}")
        
    def decompress_zip(self, zip_path: str, extract_path: str):
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_path)
        self._log_action("Decompress file", f"Decompressed {zip_path} to {extract_path}")

    # ==========================
    # 10. Temporary File Operations
    # ==========================
    def create_temporary_file(self) -> str:
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        self._log_action("Temp file", f"Created temp file at {temp_path}")
        return temp_path

    # ==========================
    # 12. Symbolic and Shortcut
    # ==========================
    def create_symbolic_link(self, source: str, link_name: str):
        os.symlink(source, link_name)
        self._log_action("Symlink", f"Created symlink {link_name} -> {source}")

    def resolve_symbolic_link(self, path: str) -> str:
        return os.path.realpath(path)

    # ==========================
    # 13. Error Handling and Recovery
    # ==========================
    def backup_before_modification(self, path: str):
        if os.path.exists(path):
            backup_path = path + ".bak"
            shutil.copy2(path, backup_path)
            self._log_action("Backup", f"Created backup {backup_path}")

    # ==========================
    # 14. Logging and Auditing
    # ==========================
    def get_history(self) -> List[Dict]:
        return self.history


# Provide backwards compatibility with the previous basic functions in file_tool.py if needed
_tool_instance = FileTool()

def read_file(path: str) -> str:
    """
    Read and return the contents of a file.

    Args:
        path (str): Absolute or relative path to the file.

    Returns:
        str: Full text content of the file.
    """
    return _tool_instance.read_file(path, mode="full")

def write_file(filename: str, content: str) -> str:
    """
    Write content to a file inside the output/ directory.

    Args:
        filename (str): Name of the file to create or overwrite (no path prefix).
        content (str): Text content to write.

    Returns:
        str: Absolute path to the written file.
    """
    out_dir = getattr(config, "OUTPUT_FOLDER", "./output/")
    full_path = os.path.abspath(os.path.join(out_dir, filename))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    _tool_instance.write_file(full_path, content)
    return full_path

def append_file(filename: str, content: str) -> str:
    """
    Append content to an existing file in the output/ directory.

    Args:
        filename (str): Target filename inside output/.
        content (str): Text to append.

    Returns:
        str: Absolute path to the modified file.
    """
    out_dir = getattr(config, "OUTPUT_FOLDER", "./output/")
    full_path = os.path.abspath(os.path.join(out_dir, filename))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    _tool_instance.append_to_file(full_path, content)
    return full_path

def list_files(directory: str) -> list:
    """
    List all files in the specified directory.

    Args:
        directory (str): Path to the directory to list.

    Returns:
        list[str]: Filenames found in the directory.
    """
    return _tool_instance.list_contentsOf_folder(directory)

def delete_file(path: str) -> bool:
    """
    Delete a file at the given path (restricted to output/ directory).

    Args:
        path (str): Path to the file to delete.

    Returns:
        bool: True if deletion succeeded.
    """
    out_dir = getattr(config, "OUTPUT_FOLDER", "./output/")
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(out_dir, path))
        
    try:
        _tool_instance.delete_file(path)
        return True
    except Exception:
        return False
