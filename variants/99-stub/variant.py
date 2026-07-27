#!/usr/bin/env python3
"""99-stub: a contract-conformance reference variant.

This is NOT a benchmark competitor and must never appear in a results table.
It exists so the harness has something to exercise the four-command contract
against before any real variant is written, and so a new variant author has
a minimal working example to copy.

What it does: `ingest` records the source paths it was handed; `query`
returns a fixed abstention citing nothing; `lint` reports a clean, empty
graph. Every number it produces is trivially correct and trivially useless.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.contract import (  # noqa: E402
    GraphStats,
    LintResult,
    QueryResult,
    Usage,
    Variant,
)

STATE_FILE = "state.json"


class StubVariant(Variant):
    name = "99-stub"

    def init(self, corpus: Path, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        (out / STATE_FILE).write_text(
            json.dumps({"corpus": str(corpus), "ingested": []}, indent=2) + "\n",
            encoding="utf-8",
        )

    def ingest(self, source: Path, artifact: Path) -> None:
        state_path = artifact / STATE_FILE
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["ingested"].append(str(source))
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    def query(self, question: str, artifact: Path) -> QueryResult:
        return QueryResult(
            question=question,
            answer="",
            citations=[],
            abstained=True,
            usage=Usage(model="none", measured=True),
        )

    def lint(self, artifact: Path) -> LintResult:
        return LintResult(findings=[], graph=GraphStats(applicable=False))


if __name__ == "__main__":
    raise SystemExit(StubVariant().main())
