# tests/test_diff_patch.py
import pytest
from pathlib import Path
from app.config import SecurityError, validate_safe_path
from app.schemas.patch import PatchProposal
from app.synthesis.synthesis_service import SynthesisService


def test_validate_safe_path(tmp_path: Path):
    base_dir = tmp_path / "kb"
    base_dir.mkdir()

    # Valid relative paths
    p1 = validate_safe_path("kubernetes/cgroups.md", base_dir)
    assert p1 == (base_dir / "kubernetes/cgroups.md").resolve()

    # Path traversal attack
    with pytest.raises(SecurityError, match="escapes base directory"):
        validate_safe_path("../../outside.md", base_dir)

    # Absolute path escaping base_dir
    with pytest.raises(SecurityError, match="escapes base directory"):
        validate_safe_path("/etc/passwd", base_dir)

    # Restricted directory inside base_dir
    with pytest.raises(SecurityError, match="Access to restricted directory/file"):
        validate_safe_path(".git/config", base_dir)

    with pytest.raises(SecurityError, match="Access to restricted directory/file"):
        validate_safe_path(".obsidian/app.json", base_dir)


def test_compute_modified_content_new_file(tmp_path: Path):
    service = SynthesisService(kb_path=tmp_path)
    content = service.compute_modified_content(
        original_content="",
        is_new_file=True,
        target_heading="# Docker Storage",
        original_snippet="",
        proposed_snippet="Volume drivers manage persistent storage."
    )
    assert "# Docker Storage" in content
    assert "Volume drivers manage persistent storage." in content


def test_compute_modified_content_heading_insertion(tmp_path: Path):
    service = SynthesisService(kb_path=tmp_path)
    original = """# Kubernetes

## Pods
Basic pod info.

## Services
Service info.
"""
    result = service.compute_modified_content(
        original_content=original,
        is_new_file=False,
        target_heading="## Pods",
        original_snippet="",
        proposed_snippet="### Static Pods\nManaged by kubelet node daemon."
    )

    assert "### Static Pods" in result
    # Verify Static Pods is placed before ## Services
    pos_static = result.find("### Static Pods")
    pos_services = result.find("## Services")
    assert pos_static < pos_services


def test_compute_modified_content_snippet_replacement(tmp_path: Path):
    service = SynthesisService(kb_path=tmp_path)
    original = """# System Architecture

## Cache Layer
Redis is currently used for caching.

## Database Layer
PostgreSQL is used as the primary database.
"""
    result = service.compute_modified_content(
        original_content=original,
        is_new_file=False,
        target_heading="## Cache Layer",
        original_snippet="Redis is currently used for caching.",
        proposed_snippet="Redis Cluster v7 with sentinel failover is used for caching."
    )

    assert "Redis Cluster v7 with sentinel failover is used for caching." in result
    assert "Redis is currently used for caching." not in result
    assert "PostgreSQL is used as the primary database." in result


def test_generate_unified_diff(tmp_path: Path):
    service = SynthesisService(kb_path=tmp_path)
    original = "# Title\nLine 1\nLine 2"
    modified = "# Title\nLine 1\nLine 2 (Updated)\nLine 3"

    diff = service.generate_unified_diff(
        rel_path="notes/demo.md",
        original_content=original,
        modified_content=modified,
        is_new_file=False
    )

    assert "--- a/notes/demo.md" in diff
    assert "+++ b/notes/demo.md" in diff
    assert "+Line 2 (Updated)" in diff
    assert "+Line 3" in diff


def test_apply_patch_atomic(tmp_path: Path):
    service = SynthesisService(kb_path=tmp_path)
    proposal = PatchProposal(
        is_new_file=True,
        target_file_path="networks/ebpf.md",
        target_heading="# eBPF Architecture",
        original_snippet="",
        proposed_snippet="eBPF programs run in kernel space with safety verification.",
        unified_diff="--- /dev/null\n+++ b/networks/ebpf.md\n@@ ...",
        reason="eBPF represents Linux kernel networking."
    )

    written_path = service.apply_patch(proposal)

    assert written_path.exists()
    assert written_path.is_file()
    content = written_path.read_text(encoding="utf-8")
    assert "# eBPF Architecture" in content
    assert "kernel space with safety verification" in content
