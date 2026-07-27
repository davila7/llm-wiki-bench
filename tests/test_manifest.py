"""The corpus guard is the foundation of every claim in reports/.

If these tests are weak, a silently-edited corpus produces numbers that
look fine and mean nothing. Each of the three mismatch kinds is tested.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.manifest import CorpusMismatch, build, check, verify


@pytest.fixture
def corpus(tmp_path: Path) -> tuple[Path, Path, Path]:
    """(repo_root, corpus_root, manifest_path) with two frozen files."""
    root = tmp_path / "corpora" / "docs"
    root.mkdir(parents=True)
    (root / "a.md").write_text("alpha\n", encoding="utf-8")
    (root / "b.md").write_text("beta\n", encoding="utf-8")

    manifest = build([root], tmp_path, created="2026-07-27")
    manifest_path = tmp_path / "corpora" / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return tmp_path, root, manifest_path


def test_clean_corpus_verifies(corpus) -> None:
    repo_root, root, manifest_path = corpus
    verify(manifest_path, repo_root, [root])  # must not raise


def test_manifest_paths_are_posix_relative(corpus) -> None:
    _, _, manifest_path = corpus
    files = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    assert set(files) == {"corpora/docs/a.md", "corpora/docs/b.md"}


def test_changed_file_is_caught(corpus) -> None:
    repo_root, root, manifest_path = corpus
    (root / "a.md").write_text("alpha edited\n", encoding="utf-8")
    problems = check(json.loads(manifest_path.read_text()), repo_root, [root])
    assert [(m.path, m.reason) for m in problems] == [("corpora/docs/a.md", "changed")]
    with pytest.raises(CorpusMismatch):
        verify(manifest_path, repo_root, [root])


def test_missing_file_is_caught(corpus) -> None:
    repo_root, root, manifest_path = corpus
    (root / "b.md").unlink()
    problems = check(json.loads(manifest_path.read_text()), repo_root, [root])
    assert [(m.path, m.reason) for m in problems] == [("corpora/docs/b.md", "missing")]


def test_untracked_file_is_caught(corpus) -> None:
    """Smuggling an extra document into the corpus must invalidate runs,
    even though every manifested file still hashes correctly."""
    repo_root, root, manifest_path = corpus
    (root / "c.md").write_text("gamma\n", encoding="utf-8")
    problems = check(json.loads(manifest_path.read_text()), repo_root, [root])
    assert [(m.path, m.reason) for m in problems] == [("corpora/docs/c.md", "untracked")]


def test_unknown_schema_is_rejected(tmp_path: Path) -> None:
    p = tmp_path / "MANIFEST.json"
    p.write_text(json.dumps({"schema": "bench.manifest/99", "files": {}}), encoding="utf-8")
    with pytest.raises(CorpusMismatch, match="unknown manifest schema"):
        verify(p, tmp_path, [])
