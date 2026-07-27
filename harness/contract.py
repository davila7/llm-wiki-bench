"""The variant CLI contract.

Every variant is a subprocess exposing four commands:

    variant init   --corpus <path> --out <path>
    variant ingest --source <path>  [--artifact <path>]
    variant query  --question <text> --out <json> [--artifact <path>]
    variant lint   --out <json>     [--artifact <path>]

The four flags named in the project brief are mandatory and unchanged. The
`--artifact` flag is an *additive* extension: `init --out` establishes the
artifact directory, and the later three commands need to be told which
artifact directory to operate on. Rather than invent hidden state, the
harness passes `--artifact` explicitly. It defaults to the
`BENCH_ARTIFACT_DIR` environment variable so a variant can also be driven
by hand. See docs/DESIGN.md for the rationale.

Variants may be written in any language; this module is the Python base
class plus the JSON schemas that every variant, in any language, must emit.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Schema identifiers. Bump the integer when the shape changes; the harness
# refuses to aggregate records whose schema tag it does not recognize, so a
# format change can never silently corrupt an existing runs/ directory.
QUERY_SCHEMA = "bench.query/1"
LINT_SCHEMA = "bench.lint/1"

# Exit codes. A variant MUST use these; the harness distinguishes "this
# variant genuinely cannot do this" from "this variant crashed", and the two
# must never be conflated in a report.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_UNSUPPORTED = 2  # command not supported natively and not adapted
EXIT_CORPUS_MISMATCH = 3  # corpus hashes do not match MANIFEST.json

#: Finding kinds a `lint` result may report. Fixed vocabulary so that graph
#: health is comparable across variants (metric 4).
LINT_KINDS = (
    "contradiction",
    "orphan",
    "stale",
    "broken_link",
    "duplicate_entity",
)


@dataclass
class Usage:
    """Token and cost accounting for a single variant invocation.

    All fields default to zero rather than None: a variant that genuinely
    spends nothing (grep) reports zeros, and the harness can distinguish
    that from a variant that failed to report, which reports `measured=False`.
    """

    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    measured: bool = True


@dataclass
class QueryResult:
    """The answer to one question, plus everything needed to grade it.

    `citations` are paths relative to the repository root (e.g.
    ``corpora/docs/0007-foo.md``), never absolute and never artifact-internal
    wiki pages. Grounding (metric 2) is checked against the *corpus*, so a
    variant that cites its own generated wiki page must resolve that page
    back to the corpus documents it derives from.
    """

    question: str
    answer: str
    citations: list[str] = field(default_factory=list)
    abstained: bool = False
    variant: str = ""
    artifact_dir: str = ""
    latency_ms: int = 0
    usage: Usage = field(default_factory=Usage)
    schema: str = QUERY_SCHEMA

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = self.schema
        return d


@dataclass
class LintFinding:
    kind: str
    detail: str
    path: str = ""
    severity: str = "warn"

    def __post_init__(self) -> None:
        if self.kind not in LINT_KINDS:
            raise ValueError(f"unknown lint kind {self.kind!r}; expected one of {LINT_KINDS}")


@dataclass
class GraphStats:
    """Metric 4 inputs. A variant with no persistent artifact (00, 01)
    reports zeros and sets `applicable=False` so the report can say
    "not applicable" instead of "scored zero"."""

    pages: int = 0
    internal_links: int = 0
    orphans: int = 0
    broken_links: int = 0
    duplicate_entities: int = 0
    applicable: bool = True

    @property
    def xref_density(self) -> float:
        return (self.internal_links / self.pages) if self.pages else 0.0


@dataclass
class LintResult:
    variant: str = ""
    artifact_dir: str = ""
    findings: list[LintFinding] = field(default_factory=list)
    graph: GraphStats = field(default_factory=GraphStats)
    latency_ms: int = 0
    schema: str = LINT_SCHEMA

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema"] = self.schema
        d["counts"] = {k: sum(1 for f in self.findings if f.kind == k) for k in LINT_KINDS}
        d["graph"]["xref_density"] = self.graph.xref_density
        return d


class Variant(ABC):
    """Base class for variants implemented in Python.

    Subclass, implement the four methods, and call `.main()` from a module
    `__main__`. Variants in other languages (OpenWiki is a Node CLI) are
    wrapped by a thin Python adapter that subclasses this and shells out;
    each such adapter's README must state exactly what the adapter does.
    """

    #: Variant identifier, e.g. "00-baseline-grep". Must match the directory.
    name: str = ""

    # --- the four contract commands -------------------------------------

    @abstractmethod
    def init(self, corpus: Path, out: Path) -> None:
        """Create the artifact directory. Must be idempotent."""

    @abstractmethod
    def ingest(self, source: Path, artifact: Path) -> None:
        """Fold `source` (a file or directory) into the artifact."""

    @abstractmethod
    def query(self, question: str, artifact: Path) -> QueryResult:
        """Answer `question`, citing corpus-relative source paths."""

    @abstractmethod
    def lint(self, artifact: Path) -> LintResult:
        """Report contradictions, orphans, stale claims and broken links."""

    # --- CLI plumbing ----------------------------------------------------

    def build_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog=self.name or "variant")
        sub = p.add_subparsers(dest="command", required=True)

        p_init = sub.add_parser("init", help="create the artifact directory")
        p_init.add_argument("--corpus", required=True, type=Path)
        p_init.add_argument("--out", required=True, type=Path)

        p_ingest = sub.add_parser("ingest", help="fold a source into the artifact")
        p_ingest.add_argument("--source", required=True, type=Path)
        _add_artifact(p_ingest)

        p_query = sub.add_parser("query", help="answer a question")
        p_query.add_argument("--question", required=True)
        p_query.add_argument("--out", required=True, type=Path, help="write QueryResult JSON here")
        _add_artifact(p_query)

        p_lint = sub.add_parser("lint", help="report knowledge-layer defects")
        p_lint.add_argument("--out", required=True, type=Path, help="write LintResult JSON here")
        _add_artifact(p_lint)

        return p

    def main(self, argv: list[str] | None = None) -> int:
        args = self.build_parser().parse_args(argv)
        started = time.perf_counter()

        if args.command == "init":
            self.init(args.corpus, args.out)
            return EXIT_OK

        if args.command == "ingest":
            self.ingest(args.source, _artifact_of(args))
            return EXIT_OK

        if args.command == "query":
            result = self.query(args.question, _artifact_of(args))
            result.variant = result.variant or self.name
            result.artifact_dir = result.artifact_dir or str(_artifact_of(args))
            if not result.latency_ms:
                result.latency_ms = _elapsed_ms(started)
            _write_json(args.out, result.to_json())
            return EXIT_OK

        if args.command == "lint":
            result = self.lint(_artifact_of(args))
            result.variant = result.variant or self.name
            result.artifact_dir = result.artifact_dir or str(_artifact_of(args))
            if not result.latency_ms:
                result.latency_ms = _elapsed_ms(started)
            _write_json(args.out, result.to_json())
            return EXIT_OK

        raise AssertionError(f"unhandled command {args.command!r}")


class UnsupportedCommand(RuntimeError):
    """Raised by a variant that cannot support a command, even via adapter.

    The harness records this as `unsupported`, not as a failure and never as
    a zero score. Reports must render it as such.
    """


def _add_artifact(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--artifact",
        type=Path,
        default=None,
        help="artifact directory created by `init --out` "
        "(defaults to $BENCH_ARTIFACT_DIR)",
    )


def _artifact_of(args: argparse.Namespace) -> Path:
    if args.artifact is not None:
        return args.artifact
    env = os.environ.get("BENCH_ARTIFACT_DIR")
    if env:
        return Path(env)
    raise SystemExit("no artifact directory: pass --artifact or set BENCH_ARTIFACT_DIR")


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
