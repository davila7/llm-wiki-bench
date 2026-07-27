# Design

## What this repo is for

Three knowledge-layer approaches landed in 2026 — Karpathy's `llm-wiki.md`
pattern, Google Cloud's Open Knowledge Format, and LangChain's OpenWiki — and
nobody has measured them against each other. This repo implements each over
one shared frozen corpus and runs a reproducible evaluation to answer which
produces the most effective knowledge layer, and why.

The output that matters is a **defensible comparison**, not a wiki. A wiki
that is beautiful and loses to `grep` on every metric is a finding, and we
publish it.

### The question, operationalized

"Effective" is not a vibe. It decomposes into nine measured quantities (§
Metrics). The headline claim of this benchmark will be of the form:

> Variant *V* answers *X%* of multi-hop questions correctly at *$Y* per query
> and *Z* ms latency, versus *X'* / *$Y'* / *Z'* for raw grep, and its
> advantage comes specifically from *metric M*.

Any "why" that cannot be pinned to a specific metric does not go in the
report.

## The falsifiability spine: baselines

`00-baseline-grep` and `01-baseline-rag` are load-bearing, not filler.
Without them the benchmark is unfalsifiable — "the wiki answered well" is
meaningless if raw grep answers just as well for a fraction of the cost.

- **00-baseline-grep** — no persistent artifact at all. An agent with
  Glob/Grep/Read over the raw corpus. This is the honest floor: it is what a
  competent engineer does with no infrastructure.
- **01-baseline-rag** — chunk, embed, top-k retrieve. No persistent
  human-readable artifact, no maintenance loop. This isolates *retrieval*
  from *curation*: if the wiki variants only match RAG, then the wiki is
  buying nothing that an index doesn't already buy.

The interesting result is not "wikis win". It is *where* the curated layer
beats retrieval and where it does not. Multi-hop and contradiction detection
are where a curated layer should pay off, because they require knowledge that
exists in no single chunk. Single-hop is where it should not.

**If the wiki variants do not beat both baselines on any metric, that is the
result and we report it.**

## Variants

| ID | Approach | Persistent artifact | Notes |
|---|---|---|---|
| `00-baseline-grep` | raw sources + agent | none | the floor |
| `01-baseline-rag` | chunk + embed + top-k | index only | isolates retrieval from curation |
| `02-karpathy-pure` | the pattern, by hand | markdown wiki | schema file + agent, `index.md` + `log.md` |
| `03-openwiki-code` | OpenWiki code mode | `openwiki/` dir | maintains AGENTS.md / CLAUDE.md marker blocks |
| `04-openwiki-personal` | OpenWiki personal mode | `~/.openwiki/wiki` | **git-repo connector only** |
| `05-okf-native` | our own OKF producer | OKF bundle | emits v0.2 at the pinned SHA |
| `06-okf-hybrid` | 05 + hybrid search | OKF bundle + index | SQLite FTS5 + local embeddings, RRF |

`99-stub` is a contract-conformance reference. It is not a competitor and
must never appear in a results table.

### On 02: there is no official Karpathy prompt

The gist is an idea file, not code — three layers (immutable raw sources, an
LLM-maintained markdown wiki, a schema file such as CLAUDE.md/AGENTS.md) and
three operations (ingest, query, lint), with `index.md` and `log.md`
reserved. No prompt ships with it.

This means **variant 02 is our interpretation**, and its result is partly a
measurement of our prompt-writing. That is a real threat to validity and it
gets stated in the report rather than hidden. Mitigation: the 02 prompt is
written once, before any results are seen, is checked into
`variants/02-karpathy-pure/`, and is not tuned in response to scores. If we
ever do tune it, that becomes a separate variant (`02b`) and both are
reported.

## The variant contract

Every variant is a subprocess exposing four commands:

```
variant init   --corpus <path> --out <path>
variant ingest --source <path>
variant query  --question <text> --out <json>
variant lint   --out <json>
```

Subprocess-level, not Python-level, so implementation language is free —
OpenWiki is a Node CLI. The Python base class in `harness/contract.py` is a
convenience for variants we write ourselves, plus the definition of the JSON
that *every* variant, in any language, must emit.

### One documented addition: `--artifact`

The contract as briefed is underspecified: `init --out` establishes the
artifact directory, but `ingest`, `query` and `lint` have no way to be told
which artifact directory to operate on. Rather than invent hidden global
state, all three accept an additive `--artifact <path>`, defaulting to
`$BENCH_ARTIFACT_DIR`. The four mandated flags are unchanged and still work.
This is the only deviation from the briefed contract.

### Adapters must confess

Where a variant cannot support a command natively, we implement the thinnest
possible adapter and record in that variant's README exactly what the adapter
does. Nothing is silently faked. Concretely we already expect:

- `lint` is not native to 00, 01, 03 or 04. For 00/01 there is no artifact to
  lint, so `lint` reports `graph.applicable = false` — which the report
  renders as **not applicable**, never as a score of zero. Scoring an absent
  artifact as zero would be a fabricated number.
- Whether OpenWiki exposes a per-question query mode compatible with our
  citation requirement is unverified as of Phase 0 and is an open risk.

### Exit codes

`0` ok, `1` error, `2` unsupported, `3` corpus hash mismatch. The harness
must never conflate "cannot" with "crashed" — they mean different things in
a results table.

### Citations are corpus paths

`query` returns an answer plus cited source paths **relative to the repo
root, pointing into `corpora/`**. Grounding is checked against the corpus,
not against a variant's own generated pages. A variant that cites its own
wiki page must resolve that page back to the corpus documents behind it.
Otherwise a wiki could "cite" itself and score perfectly on grounding while
being entirely hallucinated.

## Corpora

Two corpora, because the ingest loop differs meaningfully between prose and
code.

**`corpora/docs/`** — 40–60 real documents on one coherent topic, from public
material with permissive terms, provenance recorded per file in
`MANIFEST.json`. Deliberately seeded with:

- **≥ 5 genuine contradiction/supersession pairs.** These are the entire
  basis of the contradiction-detection question category. They must be real
  disagreements or real over-time supersessions, not manufactured ones, or
  the category measures nothing.
- **≥ 8 facts that only emerge by combining 2–3 documents.** These are the
  basis of the multi-hop category, and the place a curated layer should earn
  its keep. If a fact is answerable from one document, it is single-hop no
  matter how hard it looks.

**`corpora/code/`** — one mid-sized OSS repo vendored at a pinned SHA, plus a
**second, later SHA reserved for the drift test** and not touched during the
initial build.

### Freezing is enforced, not requested

`corpora/MANIFEST.json` records sha256 + byte count + provenance per file.
`harness/manifest.py` detects three failure kinds, all of which invalidate
prior runs:

| Kind | Why it matters |
|---|---|
| `changed` | content edited under a stable path |
| `missing` | a manifested file deleted |
| `untracked` | a file added to the corpus that the manifest doesn't know about |

The third is the one people forget: every manifested file can hash correctly
while someone has quietly dropped an extra document into the corpus. The
runner calls `verify()` before invoking any variant and refuses to run on
mismatch. `bench corpus freeze` refuses to overwrite an existing manifest
without `--force`, because regenerating it is a deliberate act that throws
away every prior run.

## Metrics

Every number traces to a run ID in `runs/`. Nothing is estimated,
interpolated, or gap-filled.

**1. Answer quality.** Held-out question set, four categories:
single-hop, multi-hop (2–3 sources), contradiction detection, and
**out-of-corpus abstention**. The last is not decoration: a variant that
answers everything confidently will beat a careful one on the first three
categories while being strictly worse in practice. Graded by LLM judge
against a written rubric, plus a **human spot-check of ≥ 20%**, with
**judge–human agreement reported**. An unreported agreement figure makes
every quality number unverifiable.

**2. Citation grounding.** Fraction of answers whose cited paths actually
contain the claim. Confident answers with no valid citation are penalized —
this is the check that catches a fluent hallucinator.

**3. Drift resistance.** After the initial build, ingest the later corpus
state (new and contradicting sources, second code SHA). Measure: affected
pages updated, stale claims surviving, cross-references gone dead. This is
the metric that separates a knowledge layer from a one-shot summary, and it
is where we expect the sharpest differences.

**4. Graph health.** Orphan pages, broken internal links, duplicate entities
(same concept, two pages), cross-reference density. Fixed finding vocabulary
across variants so the numbers are comparable; an unknown lint kind is a hard
error, not a silently dropped count.

**5. Format conformance — reported as two separate things.** See
`docs/OKF-NOTES.md` §4. OKF's conformance rules are three permissive clauses,
substantively identical between v0.1 and v0.2, and they certify *parse-level
interoperability only*. A bundle emitting nothing but `type:` is fully
conformant. So conformance is reported as a near-free binary, and separately
we report **field utilization** — which optional v0.2 families a variant
actually populates. Only the latter discriminates, and it is explicitly
labelled as *not* a conformance measure. External oracle: upstream's
`OKFDocument.validate()` at the pinned SHA, cross-checked against our own
independent checker; disagreement between them is itself reportable.

**6. Cost.** Input/output tokens and USD, per source ingested, per query, and
per update run. Amortization matters: a variant with an expensive build and a
cheap query is a different product than the reverse, and a single blended
number hides that.

**7. Latency.** Wall clock for init, ingest, query, update. Plus **agent-side
file search latency as the artifact grows** — total repo size affects
Glob/Grep even on untouched files, so a large wiki imposes a tax on
everything else in the repo.

**8. Scaling.** Each variant at 10, 25, and full corpus size. The specific
question: **where does a flat `index.md` stop working?** We expect a knee,
and finding it is one of the more useful things this benchmark can produce.

**9. Variance.** N=3 runs per variant per configuration on identical inputs;
mean and spread reported. Agent output is non-deterministic and a single run
proves nothing. If the spread swamps the between-variant difference, the
honest conclusion is "no measurable difference", and we draw it.

## Methodology rules

- Same model, same temperature, same corpus across all variants. Only the
  wiki strategy varies. Exact model IDs pinned and recorded in every run
  manifest.
- **The judge model must be from a different family than the generator.** If
  that is impossible, run both and report both. A model judging its own
  family's output is not an independent measurement.
- **Question sets are authored before, and independently of, looking at any
  generated wiki.** Writing questions after seeing a wiki tests the wiki's
  vocabulary rather than its knowledge. Question sets are committed before
  variant construction begins, and the commit order is the evidence.
- Never write a number into `reports/` that is not traceable to a run ID in
  `runs/`. If a run failed, the report says it failed.
- Any "why" claim points at a specific metric.

### Known threats to validity, recorded up front

1. **We author variant 02's prompt** (see above). Partly measures us.
2. **We author variant 05 outright.** Home-team advantage is real. Mitigation:
   05 and 06 get no prompt tuning that 02 doesn't get, and 06 exists partly to
   show how much of 05's result is the *format* versus the *search index*.
3. **Judge agreement may be low** on contradiction detection, which is the
   most subjective category. Reported, not smoothed.
4. **OpenWiki is a moving target.** Pin the exact version.

## Operational constraints

- **Telemetry off in every invocation.** `OPENWIKI_TELEMETRY_DISABLED=1` and
  `DO_NOT_TRACK=1` are set by `harness/env.variant_env()` and asserted by
  `assert_telemetry_disabled()`. This is enforced by code because relying on
  a developer to remember it is how it ends up on.
- **Connector allow-list.** Variant 04 uses the **git-repo connector only**.
  Gmail, Notion, X, Web Search and Hacker News are banned: non-reproducible
  and they pull private data. `assert_connectors_allowed()` rejects both
  banned and unknown connectors — default-deny, so a new connector cannot
  slip in by being unrecognized.
- **Secrets** live in `.env.local`, gitignored. OpenWiki stores provider
  credentials in plaintext in `~/.openwiki/.env` **including an OAuth refresh
  token**; that file is never copied into the repo, and `.gitignore` carries
  defensive patterns so an accidental copy cannot be committed.
- No network calls at import time; enforced by a test.

## Corrections to the briefing

Recorded because the benchmark's credibility depends on building against what
is actually true, not what was assumed:

1. **OKF v0.2 is no longer a draft, and is the spec at HEAD.** The briefing
   describes v0.1 as the published draft with v0.2 as something that "exists".
   As of commit `3fcbb9f` (2026-07-24) the `(Draft)` marker is gone and v0.2
   supersedes v0.1. Details in `docs/OKF-NOTES.md`.
2. **v0.2 adds an entire family the briefing does not mention**: the
   `Attested Computation` concept type with `runtime`, `parameters`,
   `computation`, `executor` and `attester` (§10). This is the largest
   addition in v0.2 and it expands what variant 05 must be able to emit.
3. **OpenWiki's latest npm version is 0.2.3, not 0.2.0.** `npm view openwiki`
   on 2026-07-27 reports `0.2.3` as `latest`, created 2026-06-26. We pin an
   exact version in Phase 3 and record it in every run manifest.
4. **OKF conformance barely discriminates.** The v0.1 and v0.2 conformance
   clauses are substantively identical, so "validates as OKF" is close to a
   free pass — hence the split of metric 5 above.

## Phases

| Phase | Content | State |
|---|---|---|
| 0 | scaffold, contract, stub variant, this doc, OKF notes | **awaiting review** |
| 1 | corpora + frozen manifest + hash guard | manifest code exists; corpora not authored |
| 2 | harness, run manifests, cost/latency capture, duckdb aggregation | not started |
| 3 | baselines 00 and 01 **first**, then 02–06 | not started |
| 4 | eval: question sets, judges, metrics | not started |
| 5 | reports: results table + written analysis | not started |

Baselines are built before the wiki variants deliberately: it fixes the bar
before there is any temptation to move it.
