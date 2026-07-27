"""The `bench` CLI.

Phase 0 wires the command surface and the two guards that already have
real implementations (`corpus verify`, `corpus freeze`). Commands scheduled
for later phases are registered but exit with a clear "not implemented in
this phase" message rather than pretending to work.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from harness import __version__
from harness.manifest import CorpusMismatch, build, verify

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOTS = [REPO_ROOT / "corpora" / "docs", REPO_ROOT / "corpora" / "code"]
MANIFEST_PATH = REPO_ROOT / "corpora" / "MANIFEST.json"

_NOT_YET = {
    "run": "Phase 2 (harness, run manifests, cost/latency capture)",
    "eval": "Phase 4 (question sets, judges, metrics)",
    "report": "Phase 5 (results table and written analysis)",
}


def _cmd_corpus_verify(_args: argparse.Namespace) -> int:
    if not MANIFEST_PATH.exists():
        print(f"no manifest at {MANIFEST_PATH}; run `bench corpus freeze` first", file=sys.stderr)
        return 1
    try:
        verify(MANIFEST_PATH, REPO_ROOT, CORPUS_ROOTS)
    except CorpusMismatch as exc:
        print(str(exc), file=sys.stderr)
        return 3
    print("corpus matches MANIFEST.json")
    return 0


def _cmd_corpus_freeze(args: argparse.Namespace) -> int:
    if MANIFEST_PATH.exists() and not args.force:
        print(
            f"{MANIFEST_PATH} already exists. Refusing to regenerate silently: "
            "this invalidates every prior run. Pass --force if that is intended.",
            file=sys.stderr,
        )
        return 1
    manifest = build(CORPUS_ROOTS, REPO_ROOT, created=args.created or date.today().isoformat())
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({len(manifest['files'])} files)")
    return 0


def _cmd_not_yet(name: str) -> int:
    print(
        f"`bench {name}` is not implemented yet: scheduled for {_NOT_YET[name]}.",
        file=sys.stderr,
    )
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bench",
        description="llm-wiki-bench: compare agent-maintained knowledge-layer "
        "strategies over one frozen corpus.",
    )
    p.add_argument("--version", action="version", version=f"llm-wiki-bench {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    p_corpus = sub.add_parser("corpus", help="freeze and verify the corpora")
    corpus_sub = p_corpus.add_subparsers(dest="corpus_command", required=True)

    p_verify = corpus_sub.add_parser(
        "verify", help="fail unless corpora match MANIFEST.json (the run guard)"
    )
    p_verify.set_defaults(func=_cmd_corpus_verify)

    p_freeze = corpus_sub.add_parser("freeze", help="compute MANIFEST.json from disk")
    p_freeze.add_argument("--force", action="store_true", help="overwrite an existing manifest")
    p_freeze.add_argument("--created", help="ISO date to record (defaults to today)")
    p_freeze.set_defaults(func=_cmd_corpus_freeze)

    for name, phase in _NOT_YET.items():
        sp = sub.add_parser(name, help=f"[not yet] {phase}")
        sp.set_defaults(func=lambda _a, _n=name: _cmd_not_yet(_n))

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
