# 99-stub

A contract-conformance reference, **not a benchmark competitor**. It must
never appear in a results table.

It exists so the harness can exercise the four-command contract before any
real variant is written, and so a new variant author has a minimal working
example to copy. Every number it produces is trivially correct and trivially
useless: `query` always abstains, `lint` always reports an empty graph.
