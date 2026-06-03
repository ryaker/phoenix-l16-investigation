# Lane B2 addendum — cross-unit calibration value diff (full precision)

**Status:** `NEEDS_CODEX_VALIDATION`. Deterministic LRI-parse; byte-reproduced. Compares camera-0's K
matrix + distortion between the two units' 28mm same-name twins.

## Result (28mm, camera 0)

| quantity | Unit-1 (`722a6e72`, 2018-07-23) | Unit-2 (`223961c6`, 2018-07-04) | identical? |
|---|---|---|---|
| K fx=fy | 3375.884 | 3372.512 | no (Δ≈3.4) |
| K cx | 2084.516 | 2088.966 | no (Δ≈4.5) |
| K cy | 1541.342 | 1551.830 | no (Δ≈10.5) |
| distortion | [0.03264, 0.15008, 0, 0, −0.57745] | [0.03309, 0.14954, 0, 0, −0.56928] | no |

## OBSERVED

1. **Full-precision per-camera calibration differs between the two units** — both the intrinsics K and
   the distortion coefficients differ (not just the focal-tier fx). This confirms the unit-hash
   divergence (two-unit proof) is a genuine **physical-body lens-calibration difference** at the
   per-camera level.
2. **The calibration SCHEMA is identical across units** — same K layout `[fx 0 cx; 0 fy cy; 0 0 1]`,
   same 5-coefficient distortion vector with positions 3,4 = 0 (tangential off; CANDIDATE Brown-Conrady
   `[k1,k2,0,0,k3]`). Only the VALUES are per-body.

## Clean-room relevance
The distortion model FORM is fixed (a published radial model); only the coefficients are per-body and
LRI-resident. So clean-room Phoenix reimplements one fixed undistort formula and parses each LRI's
per-camera coeffs — no embedded libcp bytes, and it generalizes across bodies by construction.

## Non-claims
- 28mm camera-0 only; not exhaustively across all 16 cams or all 4 zooms (the per-body-constant property
  is from `four_zoom_two_unit.md`).
- "Brown-Conrady" naming is CANDIDATE (form-supported: tangential terms zero); not confirmed vs the
  libcp consumer.
- LRI-input side only; binary consumer untouched (Codex's `0x23faf0` thread).
