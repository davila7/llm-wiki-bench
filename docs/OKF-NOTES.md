# OKF Notes

Everything here was read from the spec source, not from secondary summaries.
Where the project briefing and the spec disagree, the spec wins and the
disagreement is called out explicitly.

## 1. What was read, exactly

| Item | Value |
|---|---|
| Repository | `https://github.com/GoogleCloudPlatform/knowledge-catalog` |
| Spec path | `okf/SPEC.md` |
| Commit read | `3fcbb9f828c2f23d109c855ee403c3a4c81f3a96` |
| Commit date | 2026-07-24 |
| Commit subject | `Update SPEC.md` |
| Version declared in the document | **0.2** (§12, and the `**Version 0.2**` line at the top) |
| License | Apache 2.0 |
| Read on | 2026-07-27 |

### Version history of `okf/SPEC.md`

Three commits have touched the spec. The version string at each:

| Commit | Date | Version line | Note |
|---|---|---|---|
| `ee67a5c` | 2026-06-11 | `**Version 0.1 — Draft**` | initial import |
| `780fe9d` | 2026-07-24 | `**Version 0.2 (Draft)**` | "migrate format and tooling to OKF v0.2 (#227)" |
| `3fcbb9f` | 2026-07-24 | `**Version 0.2**` | drops "(Draft)" — **current HEAD** |

**Correction to the briefing.** The briefing states "v0.1 is the published
draft; v0.2 exists". As of the commit read, that is no longer accurate: v0.2
is the spec at HEAD, and it is no longer marked draft — the `(Draft)`
qualifier was removed three days ago in `3fcbb9f`. v0.1 is superseded (§13:
"v0.2 supersedes OKF v0.1"). There is no separate v0.1 branch or tag; v0.1
exists only as commit `ee67a5c` in history, from which the v0.1 comparisons
below were reconstructed.

**We build against v0.2 at `3fcbb9f`.** That exact SHA goes in every run
manifest, because the spec changed twice in one day and could change again.

## 2. Frontmatter fields, as actually specified

### Required

| Field | Rule |
|---|---|
| `type` | The **only** always-required key. A short, free-form string. §4.1: "a concept carrying just `type` is fully conformant". Not centrally registered; consumers MUST tolerate unknown values. |

### Recommended (all optional)

| Field | Meaning |
|---|---|
| `title` | Display name. Consumers MAY derive one from the filename if absent. |
| `description` | One-sentence summary; used by index generators and search snippets. |
| `resource` | Canonical URI of the underlying asset. Absent for abstract concepts. |
| `tags` | YAML list of short strings. |

### Provenance family (§5.1)

| Field | Rule |
|---|---|
| `sources` | List of materials the concept derives from. |
| `sources[].resource` | **REQUIRED within an entry.** Either a followable artifact (URL, bundle-relative path, `references/` path) **or a scope descriptor that is not a path at all** (e.g. `all queries in BigQuery project X`). |
| `sources[].id` | Optional, but SHOULD be present when the body cites the source — it is the footnote join key. |
| `sources[].title` | Optional human label. |
| `sources[].author` | Optional credibility signal, in the actor convention (§7). |
| `sources[].usage_count` | Optional adoption/liveness signal, framed by `usage_window`. |
| `sources[].last_modified` | Optional recency signal, `YYYY-MM-DD`. Distinct from `generated.at`. |
| `usage_window` | Sibling of `sources` (not inside it), `{ from, to }`. A single entry MAY override it locally. |

Two things worth flagging because they trip up implementations:

- OKF deliberately stores **signals, not a credibility score** (§5.1). Do not
  compute and persist a trust number into frontmatter; it is inferred at
  consumption time.
- **Per-claim attribution is a markdown footnote whose label equals a
  `sources[].id`** — `[^rev-policy]` — not a positional index. The spec is
  explicit that positional refs (`sources[0]`) misattribute silently when an
  agent reorders the list.
- **Lineage is expressed through links, not a field.** There is no
  `derived_from`. Explicit external lineage is out of scope for v0.2.

### Trust family (§5.2, §5.3)

| Field | Rule |
|---|---|
| `generated.by` | **REQUIRED within `generated`.** An actor (§7). |
| `generated.at` | ISO 8601 datetime of last meaningful content change. |
| `verified` | List of `{ by, at }` verification events. Independent of `generated`. |

Two consumer obligations that are `MUST`:

- A **bare `verified` mapping** (no list dash) MUST be treated as a
  one-element list.
- A concept with no trust frontmatter MUST NOT be rejected.

Trust tiers are **derived, never stored**: no `verified` ⇒ *unverified*;
`verified` by non-`human:` actors only ⇒ *machine-confirmed*; any
`human:<id>` actor ⇒ *human-reviewed*.

### Lifecycle family (§5.4, §5.5)

| Field | Rule |
|---|---|
| `status` | `draft` \| `stable` \| `deprecated`. **Absent ⇒ `stable`.** |
| `stale_after` | Absolute date `YYYY-MM-DD`. Stale when `today >= stale_after`. Deliberately absolute, not a relative TTL. |

### Computation family (§10) — `type: Attested Computation` only

**The briefing does not mention this family at all.** It is the single
largest addition in v0.2 and it changes what variant 05 must emit.

| Field | Rule |
|---|---|
| `runtime` | **REQUIRED for this type.** e.g. `bigquery`, `dbt`, `python`. Defines what `parameters` mean. |
| `parameters` | List of `{ name, type, required }`. |
| `computation` | Optional path to a computation file; if absent, the body `# Computation` fence *is* the computation. Exactly one of the two. |
| `executor` | `{ resource, receipt }` — how to run it, and the fields a run must return. |
| `attester` | `{ resource }` — deterministic, no-LLM code that checks a receipt and returns a verdict. |

Constraint with teeth: an agent MAY only supply *values* for declared
`parameters`; it **MUST NOT author or edit the computation**. Receipts and
verdicts are runtime artifacts and are **not stored in the bundle**.

### Extensions

Producers MAY add any keys. Consumers SHOULD preserve unknown keys on
round-trip and **MUST NOT** reject documents with unrecognized fields.

## 3. Structure and reserved filenames

Reserved at **any** level of the hierarchy, and MUST NOT be used for concept
documents:

| Filename | Purpose |
|---|---|
| `index.md` | Directory listing (§8) |
| `log.md` | Update history (§9) |

Only these two. There is no reserved tags file — v0.2 §3.1 states OKF does
not specify a tag-aggregation file format; a tag view is synthesized at
consumption time. (I checked v0.1 directly: its reserved table is identical,
so nothing was added or removed here.)

Constraints that are easy to violate accidentally:

- **`index.md` files contain no frontmatter**, with exactly one exception: a
  **bundle-root** `index.md` MAY carry `okf_version` (§8, §12). An `index.md`
  carrying a `type:` block is non-conformant.
- **`log.md` date headings MUST be ISO 8601 `YYYY-MM-DD`.** The leading bold
  word (`**Update**`) is convention, not requirement.
- Links: absolute bundle-relative (`/tables/customers.md`) is the
  **recommended** form. Consumers **MUST tolerate broken links** — a dangling
  link is "not-yet-written knowledge", not an error.

## 4. Conformance rules, verbatim in substance (§11)

A bundle is conformant with v0.2 if:

1. Every non-reserved `.md` file contains a parseable YAML frontmatter block.
2. Every frontmatter block contains a non-empty `type` field.
3. Every reserved filename (`index.md`, `log.md`) follows §8 / §9 when present.

Consumers MUST NOT reject a bundle for: missing optional fields, unknown
`type` values, unknown extra keys, broken cross-links, or missing `index.md`.

### The consequence for metric 5, stated plainly

**The v0.1 and v0.2 conformance rules are substantively identical.** I diffed
them: both are the same three clauses with the same five MUST-NOT-reject
carve-outs. Nothing in the computation, trust, provenance, or lifecycle
families is required for conformance.

Therefore:

- A v0.1 bundle **passes** v0.2 conformance unchanged.
- Conformance **cannot discriminate** between a variant that emits rich v0.2
  frontmatter and one that emits `type: Thing` and nothing else.
- Metric 5 ("does the output validate as OKF at the version it claims") is
  close to a free pass and must not be reported as if it were a quality
  score.

Metric 5 is therefore split in the design into **conformance** (binary,
near-free) and **field utilization** (which optional v0.2 families a variant
actually populates), and only the latter is discriminative. Field
utilization is explicitly *not* a conformance measure and the report must
say so.

## 5. v0.1 → v0.2 delta

Reconstructed by diffing `ee67a5c:okf/SPEC.md` against `3fcbb9f:okf/SPEC.md`,
then cross-checking against the spec's own §13 changelog. The two agree.

### Breaking (§13.1) — the two the briefing referred to

1. **`timestamp` is superseded by `generated.at`.** v0.1 had a top-level
   optional `timestamp` field. v0.2 replaces it with `generated: { by, at }`.
   Consumers MAY fall back to a legacy `timestamp` when `generated` is absent.
2. **The body `# Citations` list is superseded by `sources`.** v0.1 §8
   specified a numbered `# Citations` heading at the document bottom.
   Provenance moves into frontmatter. Consumers SHOULD read `sources` and MAY
   still parse a legacy `# Citations` list.

Note the oddity, worth recording because it affects how we pin: §12 defines a
minor bump as backward-compatible, yet §13 calls v0.2 "a minor version bump
… except for two deliberate breaking changes". The spec knowingly ships
breaking changes in a minor bump. Version-string comparison is therefore not
a safe compatibility test; pin the SHA.

### Additive (§13.2)

- Provenance/trust/lifecycle families: `sources` (+ `author`, `usage_count`,
  `last_modified`, `usage_window`), `generated`, `verified`, `status`,
  `stale_after`.
- New concept type `Attested Computation` and its five keys `runtime`,
  `parameters`, `computation`, `executor`, `attester`.
- New conventional body heading `# Computation`.
- The actor convention (`<producer>/<version>`, `human:<id>`, `process:<id>`).

### Carried forward unchanged

Bundle structure, both reserved filenames, the required `type`, the
recommended `title`/`description`/`resource`/`tags`, cross-linking, index
files, log files, and the permissive conformance model.

### One normative strengthening not listed in §13

v0.1 §4.1 said consumers "SHOULD NOT reject" documents with unrecognized
fields. v0.2 §4.1 says "**MUST NOT** reject". The spec's own changelog does
not mention this. Minor, but it is a real tightening and it is the kind of
thing that only shows up by diffing the text rather than reading §13.

## 6. External validator for metric 5

The brief requires an external validator rather than our own checker as the
only oracle. The upstream repo ships one, in the reference agent:

- `okf/src/reference_agent/bundle/document.py` — `OKFDocument.parse()` /
  `.validate()` implements §11 clauses 1–2 (`REQUIRED_FRONTMATTER_KEYS =
  ("type",)`), plus `normalize_verified()` (the bare-mapping MUST),
  `trust_tier()` (§5.3) and `is_stale()` (§5.5).

Plan: use upstream's implementation, vendored at the pinned SHA, as the
**primary** oracle, and our own independent checker as a cross-check.
Disagreement between the two is itself a reportable finding. Note that
upstream's `validate()` covers clauses 1–2 only — it does **not** check
clause 3 (reserved-file structure), so `index.md` / `log.md` structure needs
our own checker either way. That gap is recorded rather than papered over.

Reference bundles for smoke-testing live in `okf/bundles/` (`acme_retail`,
`ga4`, `stackoverflow`, `crypto_bitcoin`).

## 7. `type` is free-form: what conformance does not buy you

§4.1 states type values are not registered centrally and consumers must
tolerate unknown ones. So two bundles can both be fully conformant and still
be **semantically incompatible** — one emitting `type: Metric`, another
`type: metric`, another `type: KPI`, for the same idea.

Conformance certifies **parse-level interoperability only**. It says a
consumer can read the files without crashing. It says nothing about whether
two bundles mean the same thing by the same word. Every reported conformance
number in this benchmark carries that caveat.
