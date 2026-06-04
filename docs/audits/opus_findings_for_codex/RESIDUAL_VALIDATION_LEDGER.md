<!-- The 19 non-graduated-but-resolved ledger rows, each brought to validate/invalidate rigor. 2026-06-04. Answers Rich: "validate or invalidate those 19 to the level codex validates; if invalidate, is there a new alternative to investigate." Every row gets a verdict + (if invalidated) the alternative investigated + (if validated-with-residual) the residual decoded — none parked. -->
**Status:** NEEDS_CODEX_VALIDATION. **"VALIDATED"/"INVALIDATED" below are the ORCHESTRATOR's investigation
verdicts — candidates for Codex, NOT final truth. I am not the verdict on truth; Codex is.** (My two decode
passes already disagreed on the State-machine structure — see `parked_residuals_decoded_FOURZOOM` — which is
exactly why none of this is closed.) Companion to `../opus_pending/2026-06-02/REMEDIATION_LEDGER.md`. The 61
graduated rows are the four-zoom findings; these **19** were resolved as subsumed/superseded/retracted. Per
Rich, each is here brought to the same bar: **VALIDATED** (subsumption proven, parent coverage cited; any
shed sub-mechanism DECODED) or **INVALIDATED** (claim shown wrong → the correct ALTERNATIVE investigated, not
parked). Static decodes are byte-exact from `libcp b38dc4b3` (orchestrator + `decode-residuals` agent,
spot-verified). Genuinely runtime-only remainders are named per row.

# Validate / Invalidate ledger — the 19 non-graduated rows

## INVALIDATED — claim shown wrong; alternative investigated
| row | doc | claim REFUTED | how proven wrong | ALTERNATIVE (investigated) |
|---|---|---|---|---|
| 29 | post_blend_color_matrix | "matrix is runtime/per-LRI" | `__bss`≠per-render; write-wp 0 hits; values = recognizable I1I2I3 | fixed I1I2I3 const, static-init `0x374505` → GRADUATED (row25, `merge_magnitudes`§3) |
| 16 | score_q1q2_lineage | "both `0x36e511` factors are wavelet hmin" | byte re-extract: q1=`0x36cea6` cs-SSIM form, q2=`0x371730` wavelet | score=√(q1=SSIM · q2=wavelet) → GRADUATED (`static_submechanisms`); surviving "K raw not (K·L)²" preserved |
| 22 | step0_inner_body | "`-0x4240` = pixel accumulator" | self-retracted; `-0x4240` is read as input to score kernel | `-0x4240` = a compared patch into `0x36cde0` → GRADUATED (`merge_magnitudes`§1) |
| 74 | output_producer_static | "level/priority-keyed RB-tree container" | libc++ symbol scan: `__tree`/map/set/list all 0 binary-wide | intrusive 0x80-byte-node list, drained by `0x3bfe60` → GRADUATED (`final_compositing_consumer`) |
| 78 | MERGE_MECHANISM_SYNTHESIS | (synthesis carried) "runtime-populated color matrix" | same as row29 | I1I2I3 const; synthesis re-derived from graduated children |
| 79 | MERGE_PIPELINE | (table carried) "runtime/per-LRI color-correction" | same as row29 | I1I2I3 const (stage-10 row corrected) |
| 40 | block6_color_candidate | LEAD "Block-6 → the A5 `__bss` matrix" | A5 matrix proven = I1I2I3 const, not LRI-derived | dead lead; Block-6 STRUCTURE itself GRADUATED (`lri_calibration_parser` Claim4) |

## VALIDATED — subsumption correct; any shed sub-mechanism DECODED (not parked)
| row | doc | parent coverage (validated) | shed residual → DECODED |
|---|---|---|---|
| 1 | BLIND_SPOTS_discovered_stages | denoise/sharpen/depth parents (CNR/bilateral/sharpen/tone/depth) | `0x29ed90` = `lt::BilateralUpsample<f,h>` guided depth upsampler (range `0.5/σ²`, `{1,1/3}` tent) → DECODED `parked_residuals`§5 |
| 5 | accumulate_search_216f60 | geometry_builder (0x216f60/0x218390 NOT the accumulator — REFUTED-prediction covered) | `0x1f0a00` = intrusive walk + 0xe8/0x220 record ctors (NOT "RB-tree" — corrected) → DECODED §4 |
| 7 | geom_record_consumer_static | geometry_builder (unwind-vtable barrier) | State-machine dispatcher `0x22f0f0`/`0x22f3fd` (next-state = node+0x50 functor) → DECODED §2 |
| 10 | matrix_36acf0_bss_storage | colormatrix_runtime_const (self forward-ptr; I1I2I3 const) | none |
| 11 | matrix_36acf0_decode | merge_magnitudes§3 + colormatrix + lane3_blend (lane3=1.0) | none (orthonormal I1I2I3 values confirmed) |
| 20 | laneA3/CORRECTION | lane3_blend + terminal_merge (Hann overlap-add + accumulate-store) | coverage-sentinel `0x36930f` = the merge SELECTION prong → DECODED §1 |
| 21 | laneA3/LEDGER_RECONCILIATION | terminal_merge (pure reconciliation; makes NO standalone claim) | none by construction |
| 23 | laneA3/step0_reconciliation | terminal_merge + lane3_blend (N→1 score-weighted reduction) | `{flow_x,flow_y,score}` 12-byte tuple store `0x369e7e` → DECODED §6 |
| 27 | kernel_identity | resample_kernels (B-spline 0x2b2be0 / Catmull-Rom 0x36f800 byte-identical) | none |
| 28 | matrix_36acf0_bss_storage (laneA5) | DUPLICATE of row10 → colormatrix const | none (duplicate) |
| 64 | accept_consumer_calibstage | accept_reject_gate (ACCEPT path → 0xf33d0) | `0xf33d0` CalibStage current/factory bank store (r8d 1=cur/0=fac, byte-exact offsets) → DECODED §3 |
| 66 | acceptance_gate_location | accept_reject_gate (parent FOUND the gate `0x217ab9` the staging doc said was elsewhere) | array-filler call-site `0x218f7c callq 0x218b30` (graduated stats-reducer), outputs → rbx+0x18/+0x30/+0x38 → DECODED (this pass) |

## Net
**19/19 at the bar:** 7 INVALIDATED (each with the correct alternative investigated + graduated), 12 VALIDATED
(parent coverage cited; all 6 shed sub-mechanisms DECODED byte-exact). The decode caught **two further wrong
claims** (#4 `0x1f0a00` "RB-tree"; #2 `0x22f3fd` conflation). The merge SELECTION prong (#1 `0x36930f`) was
decoded statically. The remainders (state-enum values + which functor location is right; bilateral per-tile
kernel — decoded statically as Gaussian exp; flow-map producer — decoded as Cramer's-rule registration; the
flow-map's downstream reader; the `0xf33d0` bank census) are **still-to-do, and being done now** (a live
trace + remaining static decode are in flight) — not deferred.
