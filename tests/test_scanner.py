# tests/test_scanner.py
import pytest
from pathlib import Path
from app.synthesis.scanner import scan_knowledge_base, extract_headings, get_file_content


def test_extract_headings():
    markdown = """# Architecture Overview
Some intro text.
## Component 1: Ingestion
Ingestion details.
### Sub-component: Vision
OCR details.
#### Level 4 (Should be ignored)
Not H1~H3.
## Component 2: Synthesis
Diff engine details.
"""
    headings = extract_headings(markdown)
    assert headings == [
        "# Architecture Overview",
        "## Component 1: Ingestion",
        "### Sub-component: Vision",
        "## Component 2: Synthesis",
    ]


def test_scan_knowledge_base_excludes_forbidden_dirs(tmp_path: Path):
    # Set up normal structure
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\n## Getting Started\nText", encoding="utf-8")
    (tmp_path / "root.md").write_text("# Root Document\nText", encoding="utf-8")

    # Set up excluded directories
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "ignored.md").write_text("# Git Internal Doc", encoding="utf-8")

    obsidian_dir = tmp_path / ".obsidian"
    obsidian_dir.mkdir()
    (obsidian_dir / "workspace.json.md").write_text("# Obsidian Note", encoding="utf-8")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.md").write_text("# Package Doc", encoding="utf-8")

    # Non-markdown file
    (docs_dir / "image.png").write_bytes(b"dummy")

    # Scan
    toc = scan_knowledge_base(tmp_path)

    # Assertions
    assert "docs/guide.md" in toc
    assert "root.md" in toc
    assert toc["docs/guide.md"] == ["# Guide", "## Getting Started"]
    assert toc["root.md"] == ["# Root Document"]

    # Excluded directories must NOT appear in TOC
    for key in toc.keys():
        assert ".git" not in key
        assert ".obsidian" not in key
        assert "node_modules" not in key


def test_get_file_content_safe(tmp_path: Path):
    doc_file = tmp_path / "test.md"
    doc_file.write_text("Hello DiffMind World!", encoding="utf-8")

    content = get_file_content(tmp_path, "test.md")
    assert content == "Hello DiffMind World!"

    # Non-existent file
    missing = get_file_content(tmp_path, "does_not_exist.md")
    assert missing is None
