# Lane A3 — Step 0 reconciliation with Codex's committed IRAMP evidence (RETRACTION + convergence)

**Status:** `NEEDS_CODEX_VALIDATION`. This file **retracts** the "sum-vs-select on `-0x4240`" framing in
`step0_inner_body.md` and `proof_or_disproof_plan.md`, after a pre-task check against Codex's
already-committed `docs/evidence/iramp_*` lane. The retracted framing was based on a misread of
`-0x4240` as a pixel accumulator. It is not.

## What `0x36cde0` actually does (Codex committed evidence, four-zoom)

Per `docs/evidence/bundle_lldb_iramp_36cde0_scalar.md` (Codex, four-zoom): the call
`0x369e3f callq 0x36cde0` with `rdi=-0x4240`, `rsi=-0x11a0` **consumes the two 16×16 vec4 patches and
returns a SCALAR** `sqrt(xmm0*xmm1)` — a per-contributor **match/quality score**, not a pixel write.
`-0x4240` and `-0x11a0` are the **two patches being compared** (reference vs warped contributor), not an
accumulator. So the inner body does NOT sum or select pixels into `-0x4240`.

## What the inner body produces per contributor (machine-verified, this packet)

A 3-float **tuple** written into the contributor-record array (`0x60(%rcx,%rdx)`, indexed by coordinate
`0x58(%rcx,%rdx)`):
```
0x369e7e movss %xmm1,(%rcx,%rax,4)     ; field0 = -0x4310  (flow_x)
0x369e8b movss %xmm1,0x4(%rcx,%rax,4)  ; field1 = -0x4320  (flow_y)
0x369e91 movss %xmm0,0x8(%rcx,%rax,4)  ; field2 = 0x36cde0 return (match score)
```
Combined with the deterministic block-match (`mpsadbw`×16 + `phminposuw` argmin, `0x3694b1..0x369643`),
the contributor loop is a **per-contributor ALIGN (motion search) + SCORE** stage. It emits
`(flow_x, flow_y, score)` per contributor per tile-position. This matches Codex's
`bundle_lldb_iramp_refined_tuple_four_zoom.md`.

## Where the real pixel reduction lives (Codex committed lane — already traced)

The reduction over contributors is **downstream**, consuming these tuples, in Codex's committed evidence:
- `bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md` — **reciprocal-weighted add** (the combine).
- `bundle_lldb_iramp_post_weighted_add_shaping.md`
- `bundle_lldb_iramp_tuple_downstream_consumer.md`
- `bundle_lldb_iramp_partner_record_population.md`, `bundle_proof_iramp_row_composition_matrix_chain.md`

## Converged answer to Lane A3's question

The src1/src2 pre-fusion merge is, per the union of this packet + Codex's committed IRAMP lane, a
**score-weighted (reciprocal-weighted) reduction**: per output tile, each contributor is motion-aligned
(block match) and scored (`0x36cde0`), then contributors are combined by a reciprocal-weighted add — a
true N→1 reduction, but **weighted by per-contributor match quality**, NOT a naive equal-weight sum and
NOT a hard one-winner select. The `0x80000000` coverage sentinel removes non-covering contributors
before scoring (a hard gate), and the weighting handles the rest.

## Retractions

- **RETRACTED:** "sum-vs-select hinge on whether `-0x4240` is accumulated vs overwritten." `-0x4240` is a
  compared patch, not an accumulator. The hinge does not exist as posed.
- **RETRACTED:** runtime task to watchpoint `-0x4240` across the contributor loop (premised on the wrong
  frame). Superseded by: validating the reciprocal-weighted-add reduction against Codex's existing
  `iramp_tuple_post_reciprocal_weighted_add` evidence.

## Standing caveats

- All cross-references to Codex's `iramp_*` docs are pointers; this packet does not re-extract or promote
  them. Codex owns that lane and its validation.
- This packet's own machine-verified items (the nest, the sentinel, the block-match opcodes, the tuple
  store) still need Codex re-extraction before they are fact.
