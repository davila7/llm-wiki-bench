# 05-okf-native

Our own implementation, emitting OKF bundles at the exact spec version read:
**v0.2, commit `3fcbb9f828c2f23d109c855ee403c3a4c81f3a96`**. See
`docs/OKF-NOTES.md`.

## What conformance does and does not prove

OKF v0.2 conformance is three permissive clauses, substantively identical to
v0.1: parseable frontmatter, a non-empty `type`, and well-formed `index.md` /
`log.md`. A bundle emitting nothing but `type:` is fully conformant.

So this variant is scored on **two separate things**:

1. **Conformance** — binary, near-free, validated by upstream's
   `OKFDocument.validate()` at the pinned SHA, cross-checked against our own
   independent checker.
2. **Field utilization** — which optional v0.2 families it actually populates
   (`sources`, `generated`, `verified`, `status`, `stale_after`, and the
   `Attested Computation` keys). This is **not** a conformance measure and the
   report says so.

Note that upstream's validator covers clauses 1–2 only; reserved-file
structure (clause 3) needs our own checker either way.

## Home-team advantage

We author this variant, which is a real bias. Mitigation: 05 gets no prompt
tuning that 02 does not get, and 06 exists partly to separate how much of
05's result comes from the *format* versus from a *search index*.

## Status

Not implemented. Phase 3.
