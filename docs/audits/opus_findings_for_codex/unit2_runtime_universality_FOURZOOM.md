<!-- GRADUATED finding. provenance: u2-render batch (abd0602fce0f53a51) + orchestrator deterministic re-check, 2026-06-04. Closes the standing "every four-zoom runtime claim was on ONE body" open. -->
**Status:** NEEDS_CODEX_VALIDATION — **two-body OBSERVED** (Tier 1 candidate). First runtime confirmation that
the pipeline mechanisms hold on the **second physical L16 body** (Unit-2, intrinsics sig `223961c6…`), not just
Unit-1 (`722a6e72…`): merge/score/CCM/I1I2I3 with magnitudes (below), AND stereo/denoise/resample/gates/lane-E
topology by fire+entry-structure (see "Other stages on Unit-2"). The probe validated against Unit-1 28mm known values first
(CCM, I1I2I3 bits, 1/Σ, √(a·b) all reproduced exactly) before the U2 runs. All values orchestrator-re-checked.

# Unit-2 runtime universality — structure universal, values per-body

## Method note
U2 seeds carry same-named `.lris` sidecars (`lri_process` auto-loads them); to keep U2 comparable to the
sidecar-free U1 method, every U2 render used `--no-lris`. U2 has focals **28/70/150 only** — there is NO
clean U2 35mm in the corpus (see corpus correction), so U2 was tested at three tiers.

## Result (single mid-render sample per mechanism per tier — scope-bound)
| U2 tier | score `0x36cde0` a·b → √ | merge `0x36a938` pre→post | CCM `0xa9f20` row-sums | I1I2I3 `0xbfa20` |
|---|---|---|---|---|
| 28mm | 0.9019·0.9969 → **0.9482** ✓ | 0.2000 → **5.0** (1/Σ) ✓ | [0.9642, 1.0, 0.8252] | bits identical to U1 |
| 70mm | 0.1152·0.1645 → **0.1377** ✓ | 0.2000 → **5.0** ✓ | [0.9643, 1.0, 0.8251] | identical |
| 150mm | 0.7891·0.9676 → **0.8738** ✓ | 0.2000 → **5.0** ✓ | [0.9643, 1.0, 0.8252] | identical |

## Verdict
- **STRUCTURE is universal across both bodies.** Score kernel = √(factorA·factorB) non-degenerate [0,1] on
  all U2 tiers; merge `0x36a938` = 1/Σscore reciprocal normalizer on all; CCM `0xa9f20` row-sums =
  [0.9642,1.0,0.8252] (Block-6 D65 structural invariant) hold on U2 AND U1; I1I2I3 `0xbfa20` is bit-identical
  to U1 (a true static const, body-independent by construction).
- **VALUES are per-body.** Every U2 CCM matrix differs element-wise from U1 (max Δ ≈ 0.096 ≈ 10% at U2-28mm
  vs U1-28mm) while preserving the row-sum constraint. U2 28mm CCM = `[0.7739,0.1884,0.0019; 0.2142,1.0999,
  −0.3142; −0.1568,−0.5847,1.5667]` vs U1 28mm `[0.8246,0.1700,−0.0304; 0.2542,1.0919,−0.3461; −0.1128,
  −0.5331,1.4710]`. (U2 70mm/150mm CCMs likewise per-body — see batch report.)

⇒ This closes the long-standing **"every four-zoom claim was tested on ONE body"** gap for the merge/score/
CCM/I1I2I3 mechanisms: the algorithm is body-invariant; only the LRI-resident calibration values differ.
Consistent with the calibration-side cross-unit result (`lri_calibration_parser_FOURZOOM`: structure
cross-unit, values per-body).

## Other stages on Unit-2 (2026-06-04) — fire + entry-structure, all match Unit-1
Extends the above beyond merge/score/CCM. Module-relative BPs (bound `nlocs=1` every tier), one-shot
fire-confirmation + first-hit struct (auto-continue drain was non-terminating for per-pixel stages). U2 at
28/70/150mm; every stage that fires on U1 also fires on U2 with byte-identical entry/struct signatures:
- **Stereo:** runPass `0x276790`, caller `0x276860` (**rdx=N=4 source cams**, config `+0x14=4,+0x18=2.0,
  +0x2c=24.0,+0x40=2.0,+0x44=0.5` byte-identical U2-28/70/150 AND U1), cost `0x2732f0` (`+0x20/+0x24=16.0f`,
  `+0x40=0x00060602`).
- **Denoise:** CNR `0x34b3f0` FIRE; NLM `0x3070e0` FIRE; bilateral `0x2f78e0` **no-fire (= same as U1; a
  profile/config gate, NOT a U2 divergence)**.
- **Resample:** B-spline `0x2b2be0` + Catmull-Rom `0x36f800` FIRE.
- **Accept gates:** gate1 `0x217ab9` / gate2 `0x217acf` / gate3 `0x217ae3` all FIRE (rdi=0x100 signature).
- **Lane-E topology:** L0 `0x3ec770` / L1 `0x3ebb80` / L2-4 `0x3d0650` + collector `0x3bf820` all FIRE.
⇒ structural universality across both bodies now covers the WHOLE pipeline, not just merge/score/CCM.
Scope: fire + entry-signature/first-hit-struct equivalence — NOT exact hit counts and NOT full-body N→1
proof per stage (auto-continue drain abandoned as non-terminating). bilateral no-fire cross-checked vs U1-28
only. No clean U2 35mm (three U2 tiers).

## Scope / residuals
Single mid-render sample per mechanism per tier (one camera-pair / one merge tile / one CCM apply) — confirms
mechanism identity + row-sum invariance, NOT a full per-pixel census. U2 = 28/70/150 only (no clean U2 35mm).
U2 ran `--no-lris`; whether the sidecar would alter these specific reads not separately measured. Other
runtime stages (depth, denoise, resample, gates, topology) were NOT re-run on U2 — only merge/score/CCM/I1I2I3.
