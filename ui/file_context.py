"""
file_context.py
---------------
Utilities for drag-and-drop file support.

When a user drags files onto a terminal, the terminal pastes the absolute
path(s) as plain text.  This module:

  1. Extracts valid file/dir paths from raw input text.
  2. Reads file content with a size cap (text) or metadata (binary).
  3. Builds an augmented task string that injects file contents for the LLM.

Handles macOS-specific quirks:
  - Backslash-escaped spaces:  /Users/me/My\ Documents/file.txt
  - Single-quoted paths:       '/Users/me/My Documents/file.txt'
  - file:// URIs from Finder:  file:///Users/me/file.txt
  - Multiple paths on one line
"""

from __future__ import annotations

import mimetypes
import os
import re
from pathlib import Path
from typing import List, Tuple
from urllib.parse import unquote as url_unquote

# ── Configuration ─────────────────────────────────────────────────────
MAX_FILE_BYTES = 50_000          # Truncate text files after this

# Binary MIME prefixes that we show as metadata-only
_BINARY_PREFIXES = (
    "image/", "audio/", "video/", "application/pdf",
    "application/zip", "application/x-tar", "application/gzip",
    "application/octet-stream", "application/vnd.ms-",
    "application/vnd.openxmlformats",
)


def _is_binary_mime(mime: str) -> bool:
    """Return True when the MIME type indicates binary content."""
    if not mime:
        return False
    return any(mime.startswith(p) for p in _BINARY_PREFIXES)


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _resolve_and_validate(raw: str) -> str | None:
    """Resolve a raw path string to an absolute path that exists on disk.
    Returns None if the path doesn't exist or is outside allowed roots."""
    if not raw or len(raw) < 2:
        return None

    # Unescape macOS backslash-escaped spaces:  /path/My\ Folder → /path/My Folder
    cleaned = raw.replace("\\ ", " ").strip().rstrip("/")

    try:
        p = str(Path(os.path.expandvars(os.path.expanduser(cleaned))).resolve())
    except (OSError, ValueError):
        return None

    if not (os.path.isfile(p) or os.path.isdir(p)):
        return None

    # Safety: only allow paths under user home or cwd
    home = str(Path.home().resolve())
    cwd = str(Path.cwd().resolve())
    if not (p.startswith(home) or p.startswith(cwd)):
        return None

    return p


# ── Path extraction ──────────────────────────────────────────────────

def extract_paths(text: str) -> List[str]:
    """
    Parse absolute file/directory paths from user input.

    Handles all common macOS terminal drag-and-drop formats:
      - Bare paths:              /Users/keshav/file.txt
      - Tilde paths:             ~/Desktop/notes.md
      - Backslash-escaped:       /Users/keshav/My\\ Documents/file.txt
      - Single-quoted:           '/Users/keshav/My Documents/file.txt'
      - Double-quoted:           "/Users/keshav/My Documents/file.txt"
      - file:// URIs:            file:///Users/keshav/report.csv
      - Multiple paths

    Returns a deduplicated list of resolved absolute paths that exist on disk.
    """
    if not text or not text.strip():
        return []

    raw_candidates: list[str] = []

    # 1. file:// URIs  (Finder drag or apps that produce URIs)
    for m in re.finditer(r"file://(/[^\s'\"]+)", text):
        raw_candidates.append(url_unquote(m.group(1)))

    # 2. Single-quoted paths:  '/path/with spaces/file.txt'
    for m in re.finditer(r"'((?:/|~)[^']+)'", text):
        raw_candidates.append(m.group(1))

    # 3. Double-quoted paths:  "/path/with spaces/file.txt"
    for m in re.finditer(r'"((?:/|~)[^"]+)"', text):
        raw_candidates.append(m.group(1))

    # 4. Backslash-escaped paths:  /path/My\ Documents/file.txt
    #    These contain `\ ` for spaces. We greedily match them.
    for m in re.finditer(r'((?:/|~/)(?:[^\s]|\\ )+)', text):
        candidate = m.group(1)
        if "\\ " in candidate:
            raw_candidates.append(candidate)

    # 5. Bare absolute or tilde paths — split on unescaped whitespace
    #    Remove already-matched regions to avoid duplicates
    remaining = text
    remaining = re.sub(r"file://\S+", " ", remaining)
    remaining = re.sub(r"'[^']*'", " ", remaining)
    remaining = re.sub(r'"[^"]*"', " ", remaining)

    for token in re.split(r"(?<![\\])\s+", remaining):
        token = token.strip("'\",()")
        if not token:
            continue
        if token.startswith("/") or token.startswith("~/"):
            raw_candidates.append(token)

    # Resolve, dedupe, validate
    seen: set[str] = set()
    result: list[str] = []

    for raw in raw_candidates:
        resolved = _resolve_and_validate(raw)
        if resolved and resolved not in seen:
            seen.add(resolved)
            result.append(resolved)

    return result


# ── File reading ─────────────────────────────────────────────────────

def read_file_preview(path: str, max_bytes: int = MAX_FILE_BYTES) -> str:
    """
    Read a file's content for LLM context injection.

    - Text files: returns up to *max_bytes* characters with a truncation note.
    - Binary files: returns a metadata line (name, size, MIME type).
    - Directories: returns a listing of top-level entries.
    """
    p = Path(path)

    if p.is_dir():
        try:
            entries = sorted(os.listdir(path))[:50]
            listing = "\n".join(f"  {e}" for e in entries)
            return f"[Directory: {path} — {len(entries)} entries]\n{listing}"
        except OSError as exc:
            return f"[Directory: {path} — cannot list: {exc}]"

    try:
        size = p.stat().st_size
    except OSError:
        return f"[Cannot access file: {path}]"

    mime, _ = mimetypes.guess_type(path)

    if _is_binary_mime(mime or ""):
        return f"[Binary file: {_human_size(size)} {mime or 'unknown type'}]"

    # Attempt text read
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes + 1)
    except (OSError, UnicodeDecodeError) as exc:
        return f"[Cannot read file: {exc}]"

    if len(content) > max_bytes:
        content = content[:max_bytes]
        total = _human_size(size)
        content += f"\n\n... (truncated — {total} total)"

    return content


# ── Task augmentation ────────────────────────────────────────────────

def build_augmented_task(
    raw_input: str,
    paths: List[str],
) -> Tuple[str, str]:
    """
    Build the augmented task string with file contents for the LLM,
    plus a clean display string for the UI.

    Returns:
        (augmented_task, display_task)
    """
    if not paths:
        return raw_input.strip(), raw_input.strip()

    # Strip the raw paths from the display text so the user sees a clean task
    display = raw_input
    for p in paths:
        # Remove the resolved absolute path
        display = display.replace(p, "")
        # Also try removing backslash-escaped version
        escaped = p.replace(" ", "\\ ")
        display = display.replace(escaped, "")
        # Also remove the original tilde form
        try:
            home = str(Path.home())
            if p.startswith(home):
                tilde_form = "~" + p[len(home):]
                display = display.replace(tilde_form, "")
        except Exception:
            pass

    # Also strip file:// URIs
    display = re.sub(r"file://\S+", "", display)
    # Clean up leftover quotes and whitespace
    display = re.sub(r"['\"](?:\s*['\"])*", " ", display)
    display = re.sub(r"\s{2,}", " ", display).strip()

    if not display:
        basenames = ", ".join(Path(p).name for p in paths)
        display = f"Work on: {basenames}"

    # Build the LLM block
    blocks: list[str] = []
    for p in paths:
        content = read_file_preview(p)
        blocks.append(
            f"[File: {p}]\n"
            f"<content>\n{content}\n</content>"
        )

    file_section = "<attached_files>\n" + "\n\n".join(blocks) + "\n</attached_files>"
    augmented = f"{file_section}\n\nUser task: {display}"

    return augmented, display
