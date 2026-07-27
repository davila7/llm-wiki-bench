"""The variant contract must hold as a subprocess contract, not just an API.

These tests drive the stub variant the same way the harness will: as a real
process, through argv, reading the JSON it writes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from harness.contract import LINT_KINDS, LINT_SCHEMA, QUERY_SCHEMA, LintFinding, LintResult

REPO_ROOT = Path(__file__).resolve().parent.parent
STUB = REPO_ROOT / "variants" / "99-stub" / "variant.py"


def run_stub(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(STUB), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


@pytest.fixture
def artifact(tmp_path: Path) -> Path:
    out = tmp_path / "artifact"
    proc = run_stub("init", "--corpus", str(tmp_path), "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    return out


def test_init_is_idempotent(tmp_path: Path) -> None:
    out = tmp_path / "artifact"
    for _ in range(2):
        assert run_stub("init", "--corpus", str(tmp_path), "--out", str(out)).returncode == 0
    assert (out / "state.json").is_file()


def test_ingest_then_query_writes_conformant_json(artifact: Path, tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    src.write_text("hello\n", encoding="utf-8")
    assert run_stub("ingest", "--source", str(src), "--artifact", str(artifact)).returncode == 0

    out = tmp_path / "q.json"
    proc = run_stub(
        "query", "--question", "what is X?", "--out", str(out), "--artifact", str(artifact)
    )
    assert proc.returncode == 0, proc.stderr

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == QUERY_SCHEMA
    assert payload["question"] == "what is X?"
    assert payload["variant"] == "99-stub"
    assert isinstance(payload["citations"], list)
    assert payload["abstained"] is True
    assert payload["latency_ms"] >= 0
    assert set(payload["usage"]) == {"model", "input_tokens", "output_tokens", "usd", "measured"}


def test_lint_writes_conformant_json(artifact: Path, tmp_path: Path) -> None:
    out = tmp_path / "lint.json"
    proc = run_stub("lint", "--out", str(out), "--artifact", str(artifact))
    assert proc.returncode == 0, proc.stderr

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == LINT_SCHEMA
    assert set(payload["counts"]) == set(LINT_KINDS)
    assert payload["graph"]["applicable"] is False
    assert "xref_density" in payload["graph"]


def test_artifact_dir_falls_back_to_env(artifact: Path, tmp_path: Path) -> None:
    """The harness passes --artifact, but the env fallback must work so a
    variant can be driven by hand during development."""
    out = tmp_path / "q.json"
    proc = subprocess.run(
        [sys.executable, str(STUB), "query", "--question", "q", "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={"PATH": "/usr/bin:/bin", "BENCH_ARTIFACT_DIR": str(artifact)},
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["artifact_dir"] == str(artifact)


def test_missing_artifact_is_an_error(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(STUB), "lint", "--out", str(tmp_path / "l.json")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={"PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode != 0
    assert "artifact" in proc.stderr.lower()


def test_lint_finding_rejects_unknown_kind() -> None:
    """The lint vocabulary is fixed so metric 4 is comparable across
    variants; a typo must fail loudly rather than vanish from the counts."""
    with pytest.raises(ValueError, match="unknown lint kind"):
        LintFinding(kind="whoopsie", detail="x")


def test_xref_density_is_zero_without_pages() -> None:
    assert LintResult().to_json()["graph"]["xref_density"] == 0.0
