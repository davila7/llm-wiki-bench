# llm-wiki-bench

A reproducible benchmark comparing agent-maintained knowledge-layer
strategies over one shared, frozen corpus.

Three approaches landed in 2026 and nobody has measured them against each
other: Karpathy's `llm-wiki.md` pattern, Google Cloud's [Open Knowledge
Format](https://github.com/GoogleCloudPlatform/knowledge-catalog), and
LangChain's OpenWiki. This repo implements each one, plus two mandatory
baselines, and evaluates them on the same questions to answer which produces
the most effective knowledge layer — and why.

**The output that matters is a defensible comparison, not a wiki.** If the
wiki variants do not beat plain `grep` on some metric, that is a valid and
publishable result.

## Status

**Phase 0 — scaffold.** No variants implemented, no corpora authored, no
results. `docs/DESIGN.md` and `docs/OKF-NOTES.md` are the current
deliverables.

## Quick start

```bash
uv sync --extra dev
```

```bash
uv run bench --help
```

```bash
uv run pytest
```

## Layout

```
corpora/     frozen document + code corpora, sha256 manifest
variants/    one directory per approach, each a CLI implementing the contract
harness/     runner, run manifests, cost and latency capture
eval/        held-out question sets, judges, metrics
runs/        every execution, raw, append-only
reports/     results tables and written analysis
docs/        DESIGN.md (eval design), OKF-NOTES.md (spec, read at a pinned SHA)
```

## The variant contract

Every variant is a subprocess exposing four commands:

```
variant init   --corpus <path> --out <path>
variant ingest --source <path>  [--artifact <path>]
variant query  --question <text> --out <json> [--artifact <path>]
variant lint   --out <json>     [--artifact <path>]
```

Implementation language is free — variants are invoked as subprocesses.
`harness/contract.py` defines the JSON every variant must emit and provides
a Python base class for the ones we write ourselves. See `docs/DESIGN.md`
for the `--artifact` rationale and the adapter-disclosure rule.

## Ground rules

- Same model, same temperature, same corpus across all variants.
- The judge model is from a different family than the generator.
- Question sets are authored before, and independently of, any generated wiki.
- No number reaches `reports/` unless it traces to a run ID in `runs/`.
- The harness refuses to run if the corpus does not match `MANIFEST.json`.

## License

Apache-2.0.
