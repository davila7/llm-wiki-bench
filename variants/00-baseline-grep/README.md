# 00-baseline-grep

**Mandatory baseline. Not filler.** No persistent artifact: an agent with
Glob/Grep/Read over the raw corpus. This is the honest floor — what a
competent engineer does with no infrastructure.

Without this variant the benchmark is unfalsifiable: "the wiki answered well"
is meaningless if raw grep answers just as well for a fraction of the cost.

## Adapter disclosure

- `init` — creates an artifact dir holding only the corpus path and run
  config. No index is built.
- `ingest` — **no-op by design**, recorded as such. There is nothing to
  ingest into; the corpus is read directly at query time. This is not a
  missing feature, it is the point of the variant.
- `lint` — **not applicable.** There is no artifact to lint. Reports
  `graph.applicable = false`. The report must render this as *not
  applicable*, never as a score of zero.

## Status

Not implemented. Phase 3.
