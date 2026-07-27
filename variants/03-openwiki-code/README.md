# 03-openwiki-code

LangChain OpenWiki in **code mode**: writes an `openwiki/` directory for the
target repo and maintains marker blocks in `AGENTS.md` and `CLAUDE.md`.

## Pinning

`npm view openwiki` on 2026-07-27 reports **latest = 0.2.3** (not 0.2.0 as in
the project briefing). An exact version is pinned at implementation time and
recorded in every run manifest.

## Operational constraints

- Telemetry is ON by default upstream. Every invocation goes through
  `harness.env.variant_env()`, which sets `OPENWIKI_TELEMETRY_DISABLED=1` and
  `DO_NOT_TRACK=1`, asserted before the subprocess starts.
- OpenWiki maintains marker blocks in `AGENTS.md`/`CLAUDE.md`. It must operate
  on a **scratch copy** of the corpus, never on this repo's own instruction
  files.

## Adapter disclosure — to be completed at implementation

Open risk as of Phase 0: whether OpenWiki exposes a per-question query mode
that returns citations in a form compatible with the contract is
**unverified**. If it does not, the adapter and exactly what it substitutes
gets documented here before any number is reported.

## Status

Not implemented. Phase 3.
