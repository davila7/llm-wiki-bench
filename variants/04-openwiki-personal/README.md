# 04-openwiki-personal

LangChain OpenWiki in **personal mode**, building a wiki in `~/.openwiki/wiki`.

## Connector policy — git-repo only

**Gmail, Notion, X, Web Search and Hacker News connectors are banned in every
benchmark run.** They are non-reproducible and pull private data. Only the
**git-repo** connector is permitted.

Enforced by `harness.env.assert_connectors_allowed()`, which is default-deny:
an unrecognized connector is rejected, not ignored, so a newly added upstream
connector cannot slip in.

## Credential safety

OpenWiki stores provider credentials in plaintext at `~/.openwiki/.env`,
**including an OAuth refresh token**. That file is never copied into this
repo, never read into agent context, and `.gitignore` carries defensive
patterns so an accidental copy cannot be committed.

## Adapter disclosure — to be completed at implementation

Personal mode writes to a fixed home-directory path, which conflicts with the
contract's `--out` artifact directory and with running variants in parallel.
The isolation approach (HOME override or equivalent) gets documented here.

## Status

Not implemented. Phase 3.
