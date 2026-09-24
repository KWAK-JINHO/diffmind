# app/synthesis/scanner.py
import os
import re
from pathlib import Path
from typing import Optional
from app.config import validate_safe_path

# Standard excluded directories that should never be scanned for knowledge documents
EXCLUDED_DIR_NAMES = {
    ".git",
    ".obsidian",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    ".trash",
}

HEADING_REGEX = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def extract_headings(markdown_text: str) -> list[str]:
    """
    Parses H1~H3 markdown headings (#, ##, ###) from raw text.
    Returns a list of headings formatted with their hashes, e.g.:
    ["# Kubernetes Overview", "## cgroups v2", "### Memory QoS"]
    """
    matches = HEADING_REGEX.findall(markdown_text)
    return [f"{hashes} {title.strip()}" for hashes, title in matches]


def scan_knowledge_base(kb_path: Path) -> dict[str, list[str]]:
    """
    Recursively scans KB_PATH for all markdown files (.md),
    ignoring system/hidden folders (.git, .obsidian, node_modules, etc.).
    Returns a lightweight table-of-contents dictionary:
    { "relative/path/to/file.md": ["# H1", "## H2", ...] }
    """
    resolved_kb = kb_path.resolve()
    if not resolved_kb.exists() or not resolved_kb.is_dir():
        return {}

    toc_map: dict[str, list[str]] = {}

    for root, dirs, files in os.walk(resolved_kb, topdown=True):
        # In-place directory pruning to prevent traversal into excluded folders
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIR_NAMES and not d.startswith(".")
        ]

        for file_name in files:
            if not file_name.lower().endswith(".md"):
                continue

            # Skip hidden markdown files
            if file_name.startswith("."):
                continue

            full_file_path = Path(root) / file_name
            try:
                # Read content safely with UTF-8 encoding
                content = full_file_path.read_text(encoding="utf-8", errors="replace")
                headings = extract_headings(content)
                rel_path = full_file_path.relative_to(resolved_kb).as_posix()
                toc_map[rel_path] = headings
            except (OSError, UnicodeDecodeError):
                continue

    # Return sorted dictionary for deterministic TOC mapping
    return dict(sorted(toc_map.items()))


def get_file_content(kb_path: Path, rel_path: str) -> Optional[str]:
    """
    Safely reads file content within KB_PATH after resolving path security.
    Returns None if file does not exist.
    """
    safe_path = validate_safe_path(rel_path, kb_path)
    if not safe_path.is_file():
        return None
    return safe_path.read_text(encoding="utf-8", errors="replace")
