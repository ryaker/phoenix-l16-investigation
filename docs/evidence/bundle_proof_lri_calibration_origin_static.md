# Evidence: LRI Calibration Origin (Static, Machine-Verified)

**Date:** 2026-05-30
**Status:** VERIFIED (three machine-checked facts) + scoped observations + leads.
**Scope:** The four canonical LRIs (28mm L16_02130, 35mm L16_03041, 70mm L16_03434, 150mm L16_02285)
and this `libcp.dylib`. Static only — no render, no lldb.
**Bearing:** Lane B / WSJF #2 (pair-grid producer calibration / LRI origins). Supports the standalone
distribution model (Phoenix must parse calibration from each LRI; see project distribution decision).

## Verification Method

Findings produced by a static agent (Lane B), then **independently re-verified by the parent** with a
standalone script (`runs/lri_calibration_origin/verify_laneB_independent.py`) that re-hashes raw block
payloads via the repo parser `tools/lri_field_inspect.py` and re-walks proto fields — a different code
path from the agent's. Only facts that reproduced under that independent re-run are stated as FACT below.

## FACT 1 — Calibration payloads are byte-identical across the four canonical LRIs

The three calibration-bearing block payloads have identical SHA-256 across all four LRIs
(re-computed independently; both passes agree):

| Block | payload size | SHA-256 (first 16) | 28mm | 35mm | 70mm | 150mm |
|---|---|---|---|---|---|---|
| intrinsics (blk3 wide / blk4 tele) | 32832 | `722a6e721636c9c4` | ✓ | ✓ | ✓ | ✓ |
| distortion (blk4 wide / blk5 tele) | 262968 | `f0c34433f9cf9b07` | ✓ | ✓ | ✓ | ✓ |
| depthcfg (blk6 wide / blk7 tele) | 35266 | `6a0d52b6a4d1b4de` | ✓ | ✓ | ✓ | ✓ |

Distinct hashes among the four LRIs = **1** for each block → byte-identical.

## FACT 2 — Calibration is genuinely per-camera (16 pairwise-distinct records)

Within one LRI, the intrinsics block field-13 holds **16 records** keyed `camera_id` 0..15, and all 16
are **pairwise distinct** (16 distinct SHA-256). This proves the calibration is real measured
per-camera data, not a shared constant table.

## FACT 3 — Full sensor ROI 4160×3120 is LRI-stored; pyramid dims are not

A recursive proto-field value walk over all metadata blocks shows:
- `4160` and `3120` ARE real proto field values: `LightHeader.CameraModule[i].f9.f2.f1 = 4160`,
  `.f2.f2 = 3120` (per camera, all four tiers). This is the per-camera full sensor ROI.
- `2080, 1560, 10432, 7824, 8896, 6672, 4096, 1040, 520, 390` do **NOT** appear as any proto field
  value in any LRI (the earlier byte-substring "hits" were coincidental bytes inside float payloads).

Therefore the `UpsampleLayer+0x90` depth descriptor (4160×3120, proven in
`lldb_upsample_layer_depth_path.md`) equals the LRI-stored sensor ROI, and the half-res 2080×1560 plus
the `PipelineCache` level-vector dims are libcp-computed pyramid halvings — not LRI-stored.

## Parity-Critical Consequence (supports the standalone distribution model)

- **Phoenix MUST parse per-capture from each LRI:** the 16 per-camera intrinsics records, the per-camera
  distortion records, the DepthConfig, and the per-camera 4160×3120 sensor ROI. The 16-distinct-record
  fact makes hardcoding these unsafe — the LRI is the only carrier, and a different physical body would
  legitimately carry different per-camera bytes.
- **Pyramid/level dimensions need not be stored** — they are deterministic halvings of 4160×3120.

## Scoped Observation (NOT a doctrine change — flagged for human review)

All four canonical LRIs carry **byte-identical** calibration, and `body_serial` / `module_serial`
fields are zeroed/redacted in all four. The most likely reading is that all four captures came from one
physical L16 body — which would mean the repo's "Unit A / Unit B" labeling is not exercised by this
corpus (it tests one calibration set four times, distinguishing only focal tier, not physical unit).
**This is an inference, not proof:** identical bytes are also consistent with a shared factory/batch
calibration, and the serials are redacted, so "same body" cannot be established from bytes alone.
Settling it needs LRIs from a second physical body. **The `CLAUDE.md` Unit A/B doctrine is left
unchanged pending that** — recorded here, not silently rewritten.

## FACT 4 — libcp `__const` hardcode-vs-compute (independently re-verified)

Parent re-ran the byte-search this session (`runs/lri_calibration_origin/verify_libcp_const.py`),
clean result:

| value | float32 occurrences in libcp | verdict |
|---|---|---|
| `1.0` (sanity — proves the search works) | 5627 | — |
| `0.5` (sanity) | 258 | — |
| coeff `1/3` (0.33333334) | 14 | UNIVERSAL `__const` (safe to hardcode) |
| scale `1/288` (0.00347222) | 0 | NOT stored — computed at runtime |

So the `0x29ed90` upsample coefficient `1/3` is a build-universal constant Phoenix may hardcode, while
the `1/288` scale must be reproduced from the runtime computation, not copied.

## Leads (NOT fact — see docs/hypotheses/)

The per-camera K-matrix decode for cams 1..15, the row-composition matrix source link to the `0x25e0c0`
producer, and the CalibStage-bank mapping are tracked in `docs/hypotheses/HYP-LANEB-calibration-decode.md`.

## Artifacts

- Independent re-verification: `runs/lri_calibration_origin/verify_laneB_independent.py` (rerunnable)
- Lane B full writeup + raw dumps: `/Volumes/Dev/lumen-phoenix-scratch/laneB_lri_origin_findings.md`
  and `laneB_*.txt` (scratch corpus; cited, not repo-owned)
