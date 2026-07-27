"""Corpus freezing and the hash-check guard.

Any change to a corpus invalidates every prior run. The guard is not advice:
`verify()` raises, and the runner calls it before any variant is invoked.

MANIFEST.json shape::

    {
      "schema": "bench.manifest/1",
      "created": "2026-07-27",
      "files": {
        "corpora/docs/0001-foo.md": {
          "sha256": "…",
          "bytes": 1234,
          "provenance": {"url": "…", "license": "CC-BY-4.0", "retrieved": "2026-07-27"}
        }
      }
    }

Paths are repo-root-relative and POSIX-separated so the manifest is
byte-identical across platforms.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_SCHEMA = "bench.manifest/1"


class CorpusMismatch(RuntimeError):
    """Raised when on-disk corpus content does not match MANIFEST.json."""


@dataclass(frozen=True)
class Mismatch:
    path: str
    reason: str  # "missing" | "changed" | "untracked"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_corpus_files(corpus_root: Path) -> list[Path]:
    """Every regular file under `corpus_root`, sorted, excluding VCS noise.

    MANIFEST.json itself lives beside the corpora directories, not inside
    them, so it never hashes itself.
    """
    skip_dirs = {".git", "__pycache__", ".DS_Store"}
    out = [
        p
        for p in sorted(corpus_root.rglob("*"))
        if p.is_file()
        and not any(part in skip_dirs for part in p.parts)
        and p.name != ".DS_Store"
    ]
    return out


def build(corpus_roots: list[Path], repo_root: Path, created: str) -> dict:
    """Compute a manifest. Provenance is left empty for the author to fill;
    it is deliberately not inferred.
    """
    files: dict[str, dict] = {}
    for root in corpus_roots:
        for p in iter_corpus_files(root):
            rel = p.relative_to(repo_root).as_posix()
            files[rel] = {
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
                "provenance": {},
            }
    return {"schema": MANIFEST_SCHEMA, "created": created, "files": dict(sorted(files.items()))}


def load(manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = data.get("schema")
    if schema != MANIFEST_SCHEMA:
        raise CorpusMismatch(f"unknown manifest schema {schema!r}, expected {MANIFEST_SCHEMA!r}")
    return data


def check(manifest: dict, repo_root: Path, corpus_roots: list[Path]) -> list[Mismatch]:
    """Return every discrepancy between `manifest` and disk.

    Detects three kinds, all of which invalidate runs: a manifested file that
    is gone, one whose bytes changed, and a file on disk that the manifest
    does not track (which would otherwise let someone slip a document into
    the corpus unnoticed).
    """
    recorded: dict[str, dict] = manifest.get("files", {})
    problems: list[Mismatch] = []

    on_disk: set[str] = set()
    for root in corpus_roots:
        if not root.exists():
            continue
        for p in iter_corpus_files(root):
            on_disk.add(p.relative_to(repo_root).as_posix())

    for rel, meta in sorted(recorded.items()):
        abs_path = repo_root / rel
        if not abs_path.is_file():
            problems.append(Mismatch(rel, "missing"))
            continue
        if sha256_file(abs_path) != meta.get("sha256"):
            problems.append(Mismatch(rel, "changed"))

    for rel in sorted(on_disk - set(recorded)):
        problems.append(Mismatch(rel, "untracked"))

    return problems


def verify(manifest_path: Path, repo_root: Path, corpus_roots: list[Path]) -> None:
    """Raise `CorpusMismatch` unless disk matches the manifest exactly."""
    problems = check(load(manifest_path), repo_root, corpus_roots)
    if problems:
        lines = "\n".join(f"  {m.reason:9} {m.path}" for m in problems)
        raise CorpusMismatch(
            f"corpus does not match {manifest_path}:\n{lines}\n"
            "Prior runs are invalid against this corpus state. "
            "Regenerating the manifest is an explicit, deliberate act."
        )
