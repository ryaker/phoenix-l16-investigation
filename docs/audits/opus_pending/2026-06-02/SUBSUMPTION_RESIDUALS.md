<!-- provenance: confirm-subsumed read-only parent-coverage pass (a96cb1be9d86e3c58) + orchestrator, 2026-06-04. Captures the sub-mechanism residuals + flags that survive when 14 staging docs subsume into graduated parents — so nothing is silently dropped (Rich's rule). -->
**Status:** RESIDUAL REGISTER — **NOW DECODED (2026-06-04).** These were initially parked as LEADs; that was
a deferral. Every one has since been decoded byte-exact in
`../opus_findings_for_codex/parked_residuals_decoded_FOURZOOM.md`, and the full 19-row validate/invalidate
audit is in `../opus_findings_for_codex/RESIDUAL_VALIDATION_LEDGER.md`. Decoding caught two further wrong
claims (`0x1f0a00` "RB-tree" → intrusive list; `0x22f3fd` dispatcher conflation) and closed the merge
SELECTION prong (`0x36930f`). The text below is the original parking note, kept for provenance.

# Residuals surviving subsumption (14 docs → graduated parents)

## Tracked residual sub-mechanisms (covered parent + extra detail kept here)
- **row1 `BLIND_SPOTS_discovered_stages`** → denoise/sharpen/depth parents. Residual: **§3 BilateralUpsample
  LEAD** — `0x29ed90` guided depth-upsampler tied to RTTI `lt::BilateralUpsample<f,h>` /
  `BilateralUpsampleFromCollapse`. Depth parent names `0x29ed90` exists but not the RTTI tie. NLM/PatchNLM
  body still a GAP in both (consistent, not lost).
- **row5 `accumulate_search_216f60`** → `geometry_builder_216f60_FOURZOOM` (REFUTED-prediction covered:
  0x216f60/0x218390/0x1f0a00 are geometry/compose, NOT the accumulator). Residual: **`0x1f0a00` = RB-tree map
  walk + per-record constructor** (`operator new(0xe8)`/`(0x220)` + cvtps2pd) — sub-mechanism detail.
- **row7 `geom_record_consumer_static`** → `geometry_builder_216f60_FOURZOOM` (unwind-vtable barrier covered).
  Residual: **caller census** (exactly 2 direct callers: `0x22acf5` in `0x22aaf0`, `0x22d74c` in `0x22d250`) +
  **State-machine dispatcher** (`0x22f0f0`/`0x22f3fd`, vtable +0x30, returns next-State enum to `(%r12)`) —
  co-credited by lane-D `accept_consumer_calibstage` (row64).
- **row20 `laneA3/CORRECTION`** → `lane3_blend_FOURZOOM` + `terminal_merge_3661b0_FOURZOOM` (Hann overlap-add
  placement + accumulate-store covered). Residual: **`0x80000000` per-(contributor,position) coverage-sentinel
  gate at `0x36930f`** (tile-level acceptance) — co-credited by step0 docs.
- **row23 `laneA3/step0_reconciliation`** → `terminal_merge` + `lane3_blend`. Residual: **per-contributor
  `(flow_x, flow_y, score)` tuple store** at `0x369e7e/0x369e8b/0x369e91` — points to Codex's committed
  `iramp_*` lane; confirm that lane covers it before dropping.
- **row64 `accept_consumer_calibstage`** → `accept_reject_gate_FOURZOOM` (ACCEPT path → `0xf33d0` covered).
  Residual (downstream-confirming expansion): **`0xf33d0` CalibStage bank layout** (State `+0x12c..` current /
  `+0x180..` factory; r8d=0 factory / r8d=1 current; "wrong CalibStage" throw) + the `0x22f3ff` dispatcher →
  group-runner reconciliation (also covers row7's residual).
- **row66 `acceptance_gate_location`** → `accept_reject_gate_FOURZOOM` (parent FOUND the gate the staging doc
  failed to locate: `0x216f60` block `0x217ab9`, 0.25 ceiling). Residual: the staging's verified **array-filler
  call-site map** (`0x218f7c callq 0x218b30` inside `0x218e20`; outputs → `rbx+0x18`/`rbx+0x38`) **with the
  verifier correction `r14 = -0x220` not `-0xd0`** — the `-0x220` correction must travel with this map.

## Clean subsume, no material residual
rows **10, 11, 21, 22, 27, 28** — load-bearing claim fully quoted-covered by parent (see confirm-subsumed
table). row22's "sum-vs-select hinge" is correctly DISSOLVED by its own `step0_reconciliation` retraction
(`-0x4240` is a compared patch, not an accumulator) — not lost, dead.

## ⚠ FLAGS — do NOT graduate as asserted (Codex eyeball before ledger truth)
- **row16 `score_q1q2_lineage` — RETRACTED-on-subsumption (CONTRADICTION).** Its central claim ("the two
  final multiplicands at `0x36e511` are BOTH wavelet horizontal-minima, NOT one SSIM + one wavelet") is
  **refuted** by its graduated parent `static_submechanisms_verified_FOURZOOM`, which byte-re-extracts
  score = √(**q1 = cs-SSIM term `0x36cea6`** · **q2 = wavelet statistic `0x371730`**). The parent is the
  deterministic re-extraction ⇒ it wins; row16's refutation is wrong. **Surviving novel bit (PRESERVED):**
  "K added RAW, no `(K·L)²` square" — independently confirmed by the parent. The q1=SSIM interpretation of the
  verified bytes still wants a Codex confirm (it is an interpretation of re-extracted instructions/constants,
  which strongly match the SSIM contrast-structure form `2σ_AB+C / σ²+σ²+C`).
- **row40 `block6_color_candidate` — dead LEAD.** Block-6 STRUCTURE (42 records, two 3×3 CCMs, row-sums
  0.9642/1.0/0.8252) is graduated by `lri_calibration_parser_FOURZOOM` Claim 4. But its LEAD "Block-6 may be
  the source of the A5 post-merge `__bss` 3×3" is **dead** — `colormatrix_runtime_const_RESOLVED` proves the
  A5 matrix is the fixed I1I2I3 constant, NOT LRI-derived. Subsume the structure; do NOT promote the dead link.
