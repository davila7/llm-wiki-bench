# 01-baseline-rag

**Mandatory baseline. Not filler.** Chunk + embed + top-k retrieval. An index,
but no persistent human-readable artifact and no maintenance loop.

This variant isolates **retrieval** from **curation**. If the wiki variants
only match RAG, the curated layer is buying nothing an index does not already
buy. The interesting comparison is on multi-hop and contradiction detection,
where the answer exists in no single chunk.

## Adapter disclosure

- `lint` — **not applicable.** An embedding index has no pages, links, or
  orphans. Reports `graph.applicable = false`, never zero.
- Chunking strategy, embedding model, `k`, and any reranking are pinned in
  config and recorded in the run manifest. They are chosen once, before
  results are seen, and not tuned in response to scores.

## Status

Not implemented. Phase 3.
