# Lane A1 — Post-node consumers (STATIC) — research packet

**One-line summary:** Static disasm of libcp.dylib shows the node produced by `0x23faf0`
lands in caller `0x23c5f0` stack slots `-0x1f8(%rbp)` (site `0x23c6da`) and `-0x378(%rbp)`
(site `0x23cbbc`); the CANDIDATE downstream consumer of that node's `+0x28..+0x50` fields is
an inline `cvtps2pd` widening block at `0x23c917..0x23c98a` that writes float→double-widened
values into a freshly-allocated `0xa8`-byte red-black-tree record (base `r14`), which is then
inserted via the RB-tree fixup routine `0xdb240`.

**Status:** NEEDS_CODEX_VALIDATION

This packet makes NO claim that any consumer is "the reducer", "the merge", or has image
effect. STATIC bytes only — no runtime. See `non_claims.md`.

anchorPassed = true (triplet `mulps`/`maxps`/`sqrtps` confirmed at `0x3ecfe4..0x3ecfea`).
