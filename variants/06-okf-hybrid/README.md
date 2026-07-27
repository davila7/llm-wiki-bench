# 06-okf-hybrid

Variant 05 plus a hybrid search index: SQLite FTS5 + local embeddings, fused
with Reciprocal Rank Fusion.

## Why this variant exists

To decompose 05's result. If 06 beats 05, the gain came from **retrieval**,
not from the OKF format — and the honest conclusion is that the format is
doing less work than it appears. If 06 and 05 tie, retrieval is not the
bottleneck. Either way it is a controlled contrast against 05 with exactly one
thing changed.

It is also the direct comparison against `01-baseline-rag`: 06 is RAG *plus* a
curated artifact, 01 is RAG alone.

## Status

Not implemented. Phase 3.
