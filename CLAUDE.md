See [AGENTS.md](AGENTS.md) for the full working instructions for this repository.

The short version, because these are the rules that matter most here:

1. **Never invent a number.** Nothing reaches `reports/` unless it traces to a run ID in `runs/`. A variant that cannot do something is *not applicable*, never zero.
2. **Never silently regenerate `corpora/MANIFEST.json`.** It freezes the corpus; regenerating invalidates every prior run.
3. **Never fake a variant capability.** Thin adapter + document exactly what it does, or exit code 2 (unsupported).
4. **Do not tune a variant after seeing its score.** Tuning creates a new variant ID; both get reported.
5. **Do not author question sets after seeing a generated wiki.**

Build subprocess environments with `harness.env.variant_env()` so OpenWiki telemetry is disabled. Never read or copy `~/.openwiki/.env` — it holds plaintext credentials including an OAuth refresh token.

Current phase: **Phase 0, awaiting review.** Do not start Phase 1 without confirmation.
