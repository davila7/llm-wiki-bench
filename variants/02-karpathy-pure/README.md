# 02-karpathy-pure

Karpathy's `llm-wiki.md` pattern implemented by hand: three layers
(immutable raw sources, an LLM-maintained markdown wiki, a schema file), three
operations (ingest, query, lint), with `index.md` and `log.md` reserved.

## Threat to validity — read this before reading any result

**There is no official prompt from Karpathy.** The gist is an idea file, not
code. So this variant is *our interpretation*, and its score is partly a
measurement of our prompt-writing rather than of the pattern.

Mitigations, all binding:

- The prompt is written once, before any results are seen, and checked in here.
- It is **not** tuned in response to scores. If it is ever tuned, that becomes
  variant `02b` and both are reported.
- The report states this limitation wherever 02's numbers appear.

## Status

Not implemented. Phase 3.
