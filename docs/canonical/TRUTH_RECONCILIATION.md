# Legacy Root TRUTH Reconciliation

This file records how the superseded root `TRUTH.md` v2.1.6 was reconciled into the current canonical structure.

The current root [TRUTH.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/TRUTH.md) is the rebuilt v3 summary.

This file remains only as an audit artifact.

If this file and `CLAIM_LEDGER.md` disagree, the ledger wins.

## Scope

- Legacy input reviewed: superseded root `docs/TRUTH.md` v2.1.6, preserved in git history
- Goal: preserve proven findings while preventing mixed-trust prose from outranking claim-level evidence
- Standard applied: explicit scope, named evidence, four-zoom status, and implementation consequence

## Promoted In This Pass

These root-TRUTH findings are now admitted into the canonical ledger:

| TRUTH row(s) | Canonical claim ID | Canonical verdict |
|---|---|---|
| `M2` + `M3` | `CLM-MERGE-003` | IRAMP's tested bridge-HDR argument shape is now canonical: `src1`, `src2`, `srcs[5]`, `warps[5]`, `scale`, `roi` |
| `I3` + `R29` | `CLM-DEMOSAIC-001` | `DemosaickLightV1` is active on the tested zoom quartet and the inner kernel is static SSE2, not JIT |
| `K4` + `M4` | `CLM-CCM-001` | Missing-CCM coverage and dispatcher filtering are canonical as a scope-bound negative fact |
| `F1` + `F2` | `CLM-FIRING-001` | Archive-wide firing topology is canonical for the four zoom tiers |
| `Z1` + `Z2` + `Z5` | `CLM-ZOOM-003` | Tiered focal-reference framing is canonical |

## Already Promoted Before This Pass

The following root-TRUTH subject areas were already represented in the seeded canonical zone:

- `M1` maps to `CLM-MERGE-002`
- merge-entry exclusions around `FusionCacheBayer` map to `CLM-MERGE-001`
- the `f_scale` correction maps to `CLM-CERES-001`
- the `0xf540` and dst-pair-grid corrections map to `CLM-WARP-001` and `CLM-WARP-002`
- 35mm bridge crop-plus-upsample behavior maps to `CLM-ZOOM-001`
- stale `150mm = 6C only` is carried as `CLM-ZOOM-002`
- scope-banded depth claims map to `CLM-DEPTH-001` and `CLM-DEPTH-002`
- unresolved anchor pre-fusion / C6 routing remain `CLM-PREFUSION-001`, `CLM-PREFUSION-002`, and `CLM-C6-001`

## Strong In Root TRUTH But Not Yet Admitted

These items look materially important, but they were not promoted in this pass because their proof currently lives in mixed legacy prose or transient `/tmp` artifacts rather than a stable canonical-evidence document:

- `M2.1` WarpField 80-byte runtime layout and apply-site formula details
- `M2.3` aux-image characterization as a shared sensor-native scene-luminance reference image
- `I2` full per-camera ISP stage ordering
- `C1` AWB reciprocal-application direction
- root-TRUTH open items `OPEN-AUX-WRITER`, `OPEN-WARPFIELD-DST-COORD-ARRAY`, and `OPEN-CCM-NORMALIZATION`

These should be lifted into stable proof docs first, then admitted claim-by-claim.

## Keep Quarantined

The following classes of legacy root-TRUTH material must not be used directly as spec input:

- any superseded semantic story around "composite-anchor" behavior unless re-proven at claim level
- any wording that upgrades "not observed in the tested contributor vector" into full routing closure
- any `OPEN-*` row treated as if it were a closed algorithm fact
- any `Phase 2 / Out of Scope` item treated as if it were canonical implementation guidance

## Section-by-Section Read Rule

| superseded v2.1.6 section | How to use it now |
|---|---|
| `§2.1 Cross-camera merge / IRAMP` | Mixed. Read only through admitted claims plus the blocker list. |
| `§2.2 Per-camera ISP` | Partly canonicalized. `DemosaickLightV1` is admitted; full stage order is not yet. |
| `§2.3 Color` | Mixed. Dispatcher / CCM-coverage facts are admitted; AWB and CCM-apply details still need claim-level promotion. |
| `§2.4 Calibration` | Mixed. Use only admitted claim rows and direct evidence files. |
| `§2.5 Firing rules / camera config` | Strong. Archive-scan topology is now canonical. |
| `§2.6 Depth` | Reference-only unless needed for a scoped investigation. Not a canonical driver for base merge spec. |
| `§2.7 Outliers / variant formats` | Reference-only. Do not let outlier formats steer the baseline parity spec. |
| `§2.8 Zoom / crop / canvas` | Strong. Tiered framing and 35mm crop behavior are canonical. |
| `§2.9 Container / library inventory` | Reference-only except where separately admitted. |
| `§3 Refuted Claims` | Safe as negative corrections only. Do not convert them into broader positive conclusions without a separate claim row. |
| `§4 Open Questions` | Not truth. Treat as task list only. |

## Practical Rule

For new spec work, read in this order:

1. `CLAIM_LEDGER.md`
2. `MERGE_CRITICAL_TRUTH.md`
3. `PARITY_BLOCKERS.md`
4. this reconciliation file
5. only then the superseded v2.1.6 root-truth text from git history, row by row, for candidate claim harvesting
