# IRAMP merge → output pipeline — synthesis (navigation, not new truth)

**Status:** `NEEDS_CODEX_VALIDATION`. This is a **navigational synthesis** of the Opus quarantine
packets in this campaign — it introduces **no new claims**; every stage links to its packet and carries
that packet's confidence. The ledger/`CLM-*` references cite existing canonical status. Binary
`libcp.dylib` sha256 `b38dc4b3…`, VA == file offset. Codex validates each packet independently.

## End-to-end dataflow (per four-zoom bridge HDR render)

| # | Stage | VA(s) | What | Source / confidence |
|---|---|---|---|---|
| 1 | Entry | `0x365960` | receives `src1, src2, srcs[5], warps[5], scale, ROI`; 5 contributors | Codex `lldb_iramp_entry_signature_four_zoom.md` (four-zoom) |
| 2 | Per-tile loops | `0x369140` (X) / `0x369160` (Y) in `0x3661b0` | iterate output tiles | A3 (machine-verified branch targets) |
| 3 | Contributor loop + coverage gate | `0x3692f0..0x369f24`; sentinel `0x36930f cmpl $0x80000000` | per tile, iterate contributors; skip those not covering the tile (hard pre-gate) | A3 (machine-verified) |
| 4 | Per-contributor align | `0x3694b1..0x369643` (`mpsadbw`×16 + `phminposuw`) | SAD block-match motion alignment | A3 (deterministic opcodes) |
| 5 | Per-contributor score | `0x36cde0` → `(flow_x,flow_y,score)` tuple | **CDF 9/7 wavelet-domain SSIM-class structural-similarity** match metric, `sqrt(q1·q2)` | A6 (constants byte-verified; metric-family LEAD) + Codex `bundle_lldb_iramp_36cde0_scalar.md` |
| 6 | Reduction (acceptance) | `0x36a7d8..0x36a93c` | **soft** similarity-weighted normalized blend: `weight=(score+2·max(score−0.5,0),score,score,score)`, `Σw·src / Σw` (`rcpss`); **no hard reject** | A7 (instructions/const OBSERVED; ghost-suppression LEAD) + Codex `iramp_tuple_*` |
| 7 | Weighted accumulator | `0x369fa1..0x369fa8` (Hann 16×16 separable, weights `rbp-0xa0`) | weighted accumulate into shared output base `-0x1710` | **ledger `CLM-MERGE-002` PROVEN/SPEC_READY** (Hann-weight ID is A3/Lane-B LEAD) |
| 8 | Finalization — edge-pad | `0x3750a0` (×2, extend=2) | border replication of the merged views | A5 (assert-string anchored) |
| 9 | Finalization — resample | `0x2b2be0` (cubic **B-spline**) / `0x36f800` (**Catmull-Rom**); Q16.16, 64-phase, separable 4-tap; driver `0x5440` | resample merged result to output | A5 `kernel_identity.md` / `apply_structure.md` (byte-verified kernels) |
| 10 | Post-merge color | `0x36acf0` per-pixel 3×3 matrix `out.rgb=M·in.rgb` | M from `__bss` (`0x671980..`) = **runtime/per-LRI color-correction**, not a constant | A5 `post_blend_color_matrix.md` (section-map deterministic; values runtime/deferred) |

## How this answers the parity blockers (scope-bound)

- **Blocker 1 / `CLM-PREFUSION-002`** (src1/src2 merge math): the *mechanism* is now a per-tile,
  block-match-aligned, SSIM-weighted normalized blend (stages 3–7). Still OPEN per ledger: the **semantic
  contents** of `src1`/`src2` (what the contributor frames actually carry) — stages above describe HOW
  they combine, not WHAT they are.
- **Blocker 3** (full merge topology): stages 1–10 give the topology around the proven accumulator.
- **Blocker 5** (acceptance / ghost suppression): A7 shows it is **soft** (similarity-weighting +
  >0.5 boost), not a hard reject in the merge body — a candidate answer to "why no visible trails."

## What this synthesis does NOT do

- It does not promote any LEAD to fact, does not touch the ledger/TRUTH, and does not assert the
  end-to-end chain is runtime-verified as a whole (each stage's confidence is per its packet).
- Cross-stage runtime continuity (that the same buffer flows 7→8→9→10 in one render) is **inferred from
  static placement**, not proven by a single runtime trace.
- Open per-stage items remain in each packet's `non_claims.md` (e.g. `src1`/`src2` semantic contents,
  A6 closed form, A7 lane semantics, the runtime color-matrix values).
