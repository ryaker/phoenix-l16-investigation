# Phoenix Spike v2 — Clean-Room Python Validator

**Date:** 2026-04-20
**Canonical truth:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/TRUTH.md` v2.1.3+
**Purpose:** Validate TRUTH v2.1.3 end-to-end by rendering 4 LRIs (one per focal length) through a clean-room Python reimplementation of the L16 bridge HDR pipeline. If output visually matches expectation at all 4 zoom tiers (proper color, no ghosting, no trailers), TRUTH is confirmed and Phoenix spec writing is unblocked.

## Success criteria (Rich 2026-04-20)

**PASS** per-LRI means:
- Output is a merged 10432×7824 TIFF combining all fired cameras (10 at 28/35mm tier, 11 at 70/150mm tier)
- **Colors in correct channels** — no purple shift, no green cast, no channel inversion (catches AWB direction / CCM space mistakes)
- **No ghosting or trailers** — sub-images properly aligned at merge (catches WarpField / IRAMP alignment bugs)
- **No phantom edges from dropped cams** — composite anchor pre-fusion working (catches the `libcp+0x2b3410` kernel absence)

**NOT required** (darkroom-correctable):
- Exact exposure match to Lumen
- Exact white-balance CCT match (within ~500K is fine)
- Pixel-level MAD parity

Validation = **eyeball the 4 output TIFFs**. If all 4 look right → investigation confirmed.

## Discipline (Rich's rules, CRITICAL)

1. **Clean-room (Rule #0):** NO linking against libcp.dylib, NO dlopen, NO byte-copying from libcp. Every constant either parsed from the `.lri` at render time, published/CIE-standard (Wyszecki-Stiles, sRGB math), or reimplemented from a documented algorithm in TRUTH.
2. **No prior images:** do NOT reuse 2026-04-13 spike code or its output TIFFs. Write fresh Python.
3. **Spike outputs OK, spike bytes NEVER flow into TRUTH:** If the spike reveals a TRUTH error, open a NEW OPEN item — never silently edit TRUTH from spike observations.
4. **Spike ends at the gate:** once validation passes, spike is throwaway. Phoenix (production) will be written from the spec, not copied from spike.
5. **`.lris` is not needed** (it is `lri_process`'s depth-cache output, not an input). Parse `.lri` directly.

## Target LRIs

Selected from the 9390-LRI corpus via `/Volumes/Dev/lumen-phoenix-scratch/lightheader_scan_raw.csv`. Avoided the 4 previously-investigated LRIs (L16_02130/02285/02951/03434). All from a single controlled capture session 2017-12-01.

| Focal | LRI | Size | Fired cams | Notes |
|---|---|---|---|---|
| 28mm | `/Volumes/Base Photos/Light/2017-12-01/L16_00007.lri` | 170 MB | 10 | Tier 0 anchor (A1 + B1..B5 + dropped A2..A5 via composite anchor) |
| 35mm | `/Volumes/Base Photos/Light/2017-12-01/L16_00001.lri` | 170 MB | 10 | Tier 0 with crop (same 6-cam dispatcher as 28mm) |
| 70mm | `/Volumes/Base Photos/Light/2017-12-01/L16_00004.lri` | 188 MB | 11 | Tier 1 anchor (B4 + C1..C5 + dropped B1/B2/B3/B5/C6) |
| 150mm | `/Volumes/Base Photos/Light/2017-12-01/L16_00005.lri` | 188 MB | 11 | Tier 1 with crop (takes outer_enum=1 = 70mm tier per `zoom_tier_and_vignetting.md`) |

## Pipeline (per TRUTH v2.1.3)

```
.lri file
  │
  ▼ LightHeader + Calibration parse (Blocks 3/4/6/8)
  │
  ▼ 10-bit MIPI Bayer unpack per cam (pattern from LightHeader.cam[i].field[13] — NOT hardcoded BGGR)
  │
  ▼ Per-camera ISP (10 or 11 cams in parallel):
  │   • LensUndistortCRA — radial 4096-LUT warp (TRUTH §2.2 I6)
  │   • BLC — linear (raw - 42) / 981 (TRUTH §2.4 K1; NOT Anscombe)
  │   • AWB — MULTIPLY BY 1/stored_gain (reciprocal, TRUTH §2.3 C1)
  │     context = (1/R_gain, 1.0, 1.0, 1/B_gain) from LRI Block 8 f19.f15
  │   • DemosaickLightV1 — Hamilton-Adams 21-tap polynomial, divisor=1/64 (TRUTH §2.2 I3; V2 is DORMANT)
  │   • Per-cam CCM setup (only for cams passed by IRAMP dispatcher)
  │   • Vignetting — multiply, scale 0.7373 from per-cam grid (TRUTH §2.2 I5)
  │
  ▼ Composite anchor pre-fusion (NEW — TRUTH v2.1 M14.1):
  │   At 28/35mm: A1..A5 → 4-way weighted blend → src1, src2 composite IGs
  │   At 70/150mm: B1..B5 → 4-way weighted blend → src1, src2 composite IGs
  │   (Weights: 16-entry LUT per M6 — reimplement from RE understanding or fit symmetrically)
  │
  ▼ IRAMP cross-camera merge (7-input N→1):
  │   args = (dst, src1, src2, vec[5 contributors], warps[5], scale, roi)
  │   28/35mm: vec = B1..B5; 70/150mm: vec = C1..C5
  │   Wavelet super-res via CDF 9/7 lifting (JPEG2000 spec, constants in TRUTH §2.1 M7)
  │   Per-contributor pre-norm: sqrt(max(0, in × FOV_ratio)) per-channel (M14)
  │   Per-tile CCM applied INSIDE IRAMP in chromaticity space: out = M @ (R/G, 1, B/G), green→1 (C3)
  │
  ▼ Post-IRAMP:
  │   • Tile-cubic B-spline resample (Mitchell-Netravali 64-entry LUT per M8 / 0x3ebb80)
  │   • Tone curve apply per-tile — light_v1 (bridge default, NOT light_v2)
  │     Reimplement from Hable/Naka-Rushton fit (per phoenix_tone_curves.py ≤0.5% RMS)
  │
  ▼ Output canvas Image<vec4x32f> at 10432×7824 (or cropped for 35/150mm)
  │   35mm crop RectF = (0.0957, 0.1045, 0.8957, 0.9045) → 8345×6259
  │   150mm crop RectF = (0.2668, 0.2673, 0.7332, 0.7327) → 4865×3641
  │
  ▼ Write TIFF (float32 or uint16 per output spec)
```

Bridge lri_process hardcodes outsize {10432, 7824} — all tiers upsample to this for the spike output.

## Architecture / CCM placement (TRUTH §2.3)

- **CCM source:** LRI Block C field 3 (color_matrix), NOT field 2 (forward_matrix).
- **CCM lerp:** mired-space MatLerpClamped with `α = clip((1/T - 1/T_B)/(1/T_A - 1/T_B), 0, 1)`, no extrapolation.
- **CCT default:** 4300K when `neutral_temp` not in protobuf.
- **CCT forward path:** 28-entry Robertson forward table (Wyszecki-Stiles published — use CIE xyY values, NOT byte-copy from libcp 0x66d420).
- **CCT reverse path:** DEAD on bridge HDR (9390-LRI scan shows zero LRIs persist `neutral_color`). Skip.

## Calibration block layout (TRUTH §2.3 C6)

For reference (parse from each LRI's block table):
- Block 3 @ cal region: geometric + Bayer (32,832 B, 16 records)
- Block 4 @ cal region: vignetting + CRA (262,969 B, 16 records)
- Block 6 @ cal region: CCM 14×3×9 (35,266 B, 42 records = 14 zooms × 3 illums)
- Block 8 @ cal region: AWB gains `f19.f15 = [R_gain, 1.0, 1.0, B_gain]`

Parse each block per TRUTH; do not hardcode any calibration values.

## Module structure

```
spike_v2/
  src/
    lri_parser.py       — LRI block-table + LightHeader + cal blocks + raw pixel extract
    per_cam_isp.py      — 9-stage per-camera ISP
    composite_anchor.py — A1..A5 (or B1..B5) → src1/src2 pre-fusion
    iramp_merge.py      — 7-input wavelet super-res merge
    post_merge.py       — tile-cubic resample + light_v1 tone map
    main.py             — orchestrator: argparse LRI path → render → write TIFF
    utils.py            — CIE math, 10-bit MIPI unpack, common helpers
  outputs/              — per-LRI TIFF outputs
  logs/                 — per-run stdout + intermediate dumps
  reference/            — (optional) per-cam intermediate TIFFs for debug
  SPEC.md               — this file
  README.md             — human-readable run instructions + known limits
```

## Execution

```
python3 src/main.py /Volumes/Base\ Photos/Light/2017-12-01/L16_00007.lri outputs/L16_00007_28mm.tiff
```

Per LRI, target wall-clock = 2-10 min on M1/M2 Mac mini (numpy-bound, no GPU).

## Validation protocol

1. Render all 4 LRIs → 4 TIFFs in `outputs/`.
2. Open each in Preview / Quick Look.
3. Eyeball checks:
   - Is R in red, G in green, B in blue? (purple shift = AWB reversed or CCM inverted)
   - Are sub-images aligned? (ghosting = warp math wrong)
   - Are there phantom edges where dropped cams should be? (composite anchor not firing)
   - Is tone reasonable (not crushed blacks, not blown highlights)?
4. If all 4 pass → spike is complete. Write a brief PASS report. Phoenix spec writing unblocked.
5. If any fails → diagnose per-tier (which kernel contributed most) and either (a) open NEW OPEN items in TRUTH or (b) fix spike bug if it's a reimplementation error not a TRUTH error.

## Known limits

- Weights for `libcp+0x2b3410` composite-anchor 4-way blend are not byte-decoded. TRUTH M6 says "16-entry LUT applied per-pixel as separable spatial kernel" — for spike, approximate with uniform weights first (1/N per contributor); revisit if output shows ghosting only in composite anchor regions.
- WarpField 80 B layout is structurally decoded (TRUTH M2) but field semantics partial. For spike, extract what we can from IRAMP args; approximate what we can't.
- CDF 9/7 lifting constants ARE bit-exact (TRUTH M7 values). Use them verbatim — they are public JPEG2000 spec values.

## Clean-room sources allowed

- TRUTH v2.1.3+ (internal RE reference; not library code)
- Wyszecki-Stiles Robertson (u,v,slope) 28-entry table (published, public domain)
- CIE standard illuminant xy, sRGB primaries, CIE 1931 math
- JPEG2000 spec CDF 9/7 lifting constants
- Hamilton-Adams 21-tap demosaic (published algorithm)
- `lightheader_scan_full.py` READ ONLY as format-decode reference; do not copy code

## Clean-room sources FORBIDDEN

- `libcp.dylib` bytes of any kind
- `lri_process` output as reference
- `cal_color_l16_02130.npz` (that's a reference extract, not runtime input; Phoenix parses from LRI at render time)
- 2026-04-13 spike code
