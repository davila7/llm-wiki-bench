# AGENTS.md

Instructions for agents working in this repository.

## What this repo is

A benchmark comparing agent-maintained knowledge-layer strategies over one
frozen corpus. **The deliverable is a defensible comparison, not a wiki.**
Read `docs/DESIGN.md` before changing anything structural.

## Rules that override normal helpfulness

These exist because the failure mode of this repo is producing numbers that
look credible and mean nothing.

### 1. Never invent a number

No value reaches `reports/` unless it traces to a run ID in `runs/`. Do not
estimate, interpolate, extrapolate, or fill a gap with a plausible figure. If
a run failed, the report says it failed. If a variant does not support a
command, the report says *not applicable* — never zero. A zero is a
measurement; an absence is not.

### 2. Never silently regenerate `corpora/MANIFEST.json`

The manifest freezes the corpus. Regenerating it invalidates every prior run.
`bench corpus freeze` refuses to overwrite without `--force`, and that is
deliberate. If corpus content must change, that is a conversation, not a fix.

Likewise, do not "fix" a failing `bench corpus verify` by re-freezing. A
mismatch means either the corpus was edited (find out why) or a file was
added (find out by whom). Both invalidate results.

### 3. Never fake a variant capability

If a variant cannot support a contract command, implement the thinnest
possible adapter and document in that variant's README **exactly** what the
adapter does. An adapter that quietly substitutes different behavior turns
the whole comparison into fiction. Use exit code `2` (unsupported) rather
than returning an empty-but-successful result.

### 4. Do not tune a variant in response to its score

Prompts and configuration are written once, before results are seen. If a
variant is tuned after seeing scores, it becomes a **new variant** with a new
ID, and both are reported. Otherwise we are measuring our own tuning effort.

### 5. Do not author or modify question sets after seeing a generated wiki

Question sets are written before and independently of variant construction.
Writing questions after seeing a wiki tests that wiki's vocabulary, not its
knowledge.

### 6. Corrections go in the docs

If a claim in `docs/` turns out to be wrong against a source you actually
read, fix the doc and record the correction. `docs/OKF-NOTES.md` §1 and
`docs/DESIGN.md` § "Corrections to the briefing" already carry several.

## Operational constraints

- **Telemetry**: build subprocess environments with
  `harness.env.variant_env()`, which sets `OPENWIKI_TELEMETRY_DISABLED=1` and
  `DO_NOT_TRACK=1`. Assert with `assert_telemetry_disabled()`. Never
  construct a variant env by hand.
- **Connectors**: variant 04 uses the **git-repo connector only**. Gmail,
  Notion, X, Web Search and Hacker News are banned — non-reproducible and
  they pull private data. The allow-list is default-deny.
- **Secrets**: `.env.local`, gitignored. OpenWiki keeps provider credentials
  in plaintext at `~/.openwiki/.env`, **including an OAuth refresh token**.
  Never copy that file into this repo, never read it into context, never
  paste its contents anywhere.
- **No network calls at import time.** Enforced by `tests/test_cli.py`.

## Conventions

- Python 3.12, managed with `uv`. `uv run pytest`, `uv run ruff check .`.
- Line length 100.
- Variant directories are `NN-name`; the `Variant.name` attribute must match
  the directory name.
- `harness/contract.py` owns the JSON schemas. Bump the schema integer when a
  shape changes — the harness refuses to aggregate records whose schema tag
  it does not recognize, so an unversioned change would corrupt `runs/`.
- Lint finding kinds are a fixed vocabulary (`LINT_KINDS`). An unknown kind
  raises. Do not widen it casually: metric 4 is only comparable across
  variants if the vocabulary is shared.

## Pinned external facts

Recorded so nobody re-derives them from memory. See `docs/OKF-NOTES.md`.

| Thing | Value |
|---|---|
| OKF spec version | 0.2 (no longer draft) |
| OKF spec commit | `3fcbb9f828c2f23d109c855ee403c3a4c81f3a96`, 2026-07-24 |
| OKF conformance | 3 permissive clauses; v0.1 and v0.2 substantively identical |
| OpenWiki npm latest | 0.2.3 as of 2026-07-27 (not 0.2.0) |

## Current phase

**Phase 0 — scaffold, awaiting review.** Do not start Phase 1 without
explicit confirmation. Phase order is in `docs/DESIGN.md`; baselines 00 and
01 are built before the wiki variants, deliberately.
