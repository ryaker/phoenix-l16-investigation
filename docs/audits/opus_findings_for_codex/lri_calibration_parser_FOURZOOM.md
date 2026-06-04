<!-- GRADUATED finding. provenance: W3 four-LRI re-parse (a6f8ca771a056bf56) + orchestrator block-count verify, 2026-06-03. Consolidates the lane-B2 LRI-calibration staging working-docs. -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to four-LRI OBSERVED** (Tier 1). For LRI-resident findings,
re-parse across all four canonical LRIs IS the four-zoom rigor (these are deterministic file-structure facts,
not render-path behavior). Tool: `tools/lri_field_inspect.py` (`scan_lri_blocks` + `parse_proto_fields`).
**Scope (UPDATED 2026-06-03, `unit2_universality_calibration.md`): STRUCTURE = CROSS-UNIT (Unit-1 + Unit-2
both parsed); VALUES = per-body** (Unit-1 `722a6e72…` ≠ Unit-2 `223961c6…`). The 7 structural claims below
hold on BOTH bodies; any specific numeric value (fx, CCM entries, distortion k1/k2/k3, lens-shading content)
is Unit-1-specific. NEW cross-unit invariants: **CCM row-sums [0.9642,1.0,0.8252]** and **Block-5 vignetting
(byte-identical `37a0a85e` both bodies = shared/firmware constant, not per-body)**. ⚠ The documented Unit-2
"twins" are really focals (28,70,150,150) not (28,35,70,150) — `2018-10-28/L16_03041` is f4=74, `2020-07-14/
L16_03434` is f4=149 (orchestrator-verified); does not affect calibration universality (per-cam tables are
focal-independent) but the CLAUDE.md corpus note is wrong on this.

# L16 LRI calibration parser spec — four-LRI-confirmed (28/35/70/150, Unit-1)

Consolidates + graduates the lane-B2 staging working-docs (lri_block_inventory, camera_focal_map_excluded_pair,
distortion_*, block6_*, awb_wb_gains_block8, lightheader_block0, crosscorpus_*). Per-LRI data below; all four
LRIs agree unless noted.

## Block inventory (Claim 1 — GRADUATED with structural correction)
**Block COUNT is NOT constant:** 28mm/35mm = **11 blocks**; 70mm/150mm = **12 blocks** (extra small raw/anc
block early shifts every post-block-2 role index +1). Orchestrator-verified (`scan_lri_blocks`: 28mm→11,
70mm→12). **Role key is PAYLOAD SIZE, not block index** — "intrinsics=block3" wording is correct only for
28/35mm. Role set + payload sizes are identical across all 4: LightHeader (blk0), intrinsics (32832 B),
lens-shading (262968 B), vignetting (1786 B), color/CCM (35266 B), AWB (54 B).

## Block-3 intrinsics → 5+5+6 focal tiers (Claim 2 — GRADUATED)
Path `f13[cam]→f3→f3.2[0]→f3.2.2.1` (9 fixed32 K-matrix: f1=fx,f3=cx,f5=fy,f6=cy). Per-camera fx **byte-
identical across all 4 LRIs**: cam0=3375.9, cam5=8283.4, cam10=18794.7 ⇒ tiers 28mm{0–4} / 70mm{5–9} /
150mm{10–15} = **5+5+6**, all four LRIs. (Intrinsics block = factory calib, same body every capture.)

## Distortion (Claim 3 — GRADUATED, wording fixed)
`f3.3.1.3` = 5×f32 `(k1,k2,p1,p2,k3)`; **p1=p2=0 exactly, all 16 cams, all 4 LRIs** ⇒ pure-radial
Brown-Conrady. LUTs `f3.3.2.5` (**101** points) + `f3.3.2.6` (**30** points), each a *repeated {f1=radius,
f2=y} sub-message* (NOT a packed float array — wording fix); 101-pt y-range **[0.000, 31.651] px** all 4.
**Optical groups = 3** when clustered on the FULL `(k1,k2,k3)` vector (k1-alone gives a misleading 2):
cams0-4 k2≈+0.14/k3≈-0.55; cams5-9 k2≈-0.075/k3≈+0.045; cams10-15 k2≈-0.26/k3≈+0.30 — aligned to the 3 tiers.

## Block-6 color (Claim 4 — GRADUATED, wording fixed)
Payload 35266 → f13 = **42 records (14 cams × 3 light-source variants)**; cam ids = {0,2..14}, **ids {1,15}
EXCLUDED** (all 4 LRIs). `f2.2`/`f2.3` = two DISTINCT 3×3 CCMs stored as **9-fixed32 proto sub-msgs** (NOT raw
36-byte float blocks): f2.2 row-sums **[0.9642, 1.0, 0.8252]** (byte-identical all 4), f2.3 row-sums
[0.5878, 1.03, 0.6984]. `f2.8` (950 B, in the f2.f1==2 variant) = per-camera **spectral curves 3 channels ×
76 f32** (380–755nm @5nm). All Y across 4 LRIs.

## Block-8 AWB (Claim 5 — GRADUATED, path corrected)
**AWB lives in the 54-BYTE block** (idx 8 @28/35mm, idx 9 @70/150mm), path **f19.15** = 4×fixed32 (R,G,G,B),
G-normalized. Per capture (scene-dependent, all G=1.0): 28mm [1.7178,1,1,1.5888]; 35mm [1.7191,1,1,1.6021];
70mm [1.8128,1,1,1.5831]; 150mm [1.7636,1,1,1.6007]. (The 1786-B block is vignetting, NOT AWB — corrects prior
wording.)

## Depth has no LRI origin (Claim 6 — GRADUATED, LRI side)
LightHeader f13 (depth_config) **ABSENT** in all 4; **0** `DepthConfig`/`stereo`/`disparity`/`tof_range` proto
signatures filewide, all 4. (Literal "ToF" ASCII substrings occur 3–167×/file = incidental raw-plane byte
coincidences, not depth proto.) ⇒ depth is runtime stereo-matched, no LRI store. (The libcp runtime side —
`DepthCache`/`StereoLayer` constructors — is in the staging doc `depth_stereo_no_lri_origin.md`, static, not
yet runtime-graduated.)

## LightHeader block0 (Claim 7 — GRADUATED)
f4 image_focal = 28/35/70/**149** (150mm stored as 149); f5 reference_camera = **0** (28/35) / **8** (70/150);
f18 hw_info present all 4 (54 B wide / 48 B tele).

## Block-4 lens-shading grid (GRADUATED — W3b, dims confirmed, correction)
Payload 262968 → 16× field-13 (one per camera, ids {0..15} ALL present). Per-cam `f4→f1`: **rows=17, cols=13
(=221 points) × a 4×4 channel-mixing matrix per point = 14144 B = 3536 f32**. Center point ≈ identity
(diag [1.000,1.003,0.997,1.000]); corners rise (corner diag [1.026,0.978,0.989,0.949], off-diag ±0.018) =
radial near-identity channel-mix. **CORRECTION: the old "hard-zeros at cams {3,6,9,12}" is REFUTED** — no cam
is zero; **camids {1,15} are EXACT identity (no correction, sum 884=221×4), all other 14 carry real matrices.**
This CORROBORATES the Block-6 excluded pair {1,15} (same two cams special across blocks). Byte-identical 4 LRIs
(SHA-256 `f0c34433…`) = factory-constant.

## Block-5 vignetting (GRADUATED — W3b, structure refined)
Payload 1786 → single field-16 (GLOBAL, not per-camera) → f2 = header (`f1=42.0, f2=1023.0, f3=2.0`) + **28×
field-4 entries**, index 100→775 step 25 (monotonic), each = scalar falloff `f3` (73.79→26.78, decreasing) +
4 per-channel (R/Gr/Gb/B) 2-coeff polynomials. ⇒ richer than "radius→gain LUT": a **28-knot × 4-channel
2-coeff-poly + scalar-falloff table.** Byte-identical 4 LRIs (SHA-256 `37a0a85e…`) = factory-constant.

## Verified sub-facts addendum (2026-06-04, deterministic four-LRI re-parse — `bbatch-lri`)
Independently re-parsed across all four canonical LRIs (+ Unit-2 28mm twin for cross-unit); all PASS.
- **Block-1 = per-capture AE (NEW — not a calibration block):** `msg_type 1`, fields **f10=f18=analog gain
  (f32)**, **f11=f19=exposure_µs (varint)**, f16=status; f10≡f18 and f11≡f19 bit-identical every file.
  28mm gain=1.5348/exp=14646091; 35mm 1.0/2616931; 70mm 1.0/1768733; 150mm 1.0002/510859 (exposure
  monotone-decreasing with focal; gain≈1.0 except the bright 28mm day-shot). Scene-dependent per capture.
- **Block-6 triad order confirmed {2,0,6}** (sizes `{1472:14, 519:28}`): first three records =
  (1472,f2.1=2,has f2.8)=True, (519,0)=False, (519,6)=False — `f2.8` spectral curve only on the 1472/f2.1=2
  record; identical all four zooms. `f3.2` scalars 28mm: inst0 f1=818.0, inst1 f1=1500.0.
- **Cross-unit cam0 (values per-body, schema identical):** U1-28mm fx=fy=3375.884, cx=2084.516, cy=1541.342,
  dist=[0.03264,0.15008,0,0,−0.57745]; **U2-28mm** fx=fy=3372.511, cx=2088.966, cy=1551.829,
  dist=[0.03309,0.14954,0,0,−0.56928]. Every value differs; identical 9-field K `[fx 0 cx;0 fy cy;0 0 1]` +
  5-coeff Brown-Conrady with p1=p2=0.
- **Block-3 cam0 field map (28mm) fully resolves:** f3.3.2.5 LUT=101 pts (x 0→2.8907; y non-monotone, max
  31.6512), f3.3.2.6 LUT=30 pts, f3.4=(−1.0,−1.0), f3.5=(100.0,54000.0), f7 calib date = 2017-11-04 17:47:16.
  (⚠ method note: the K and f3.4/f3.5 sub-messages are proper nested protobuf sub-fields — reading them as
  packed-f32 blobs yields garbage; the documented nesting paths are correct.)
- **LELR block count (assigned corpus):** 28mm=11, 35mm=11, 70mm=12, 150mm=12, U2-28mm=11 — **wide=11 /
  tele=12** (corrects any "12 for all" prose; the wide-tier seeds are 11). The "182 unassigned use 0–4
  blocks" claim is untestable here (no unassigned file in the 8-seed corpus) — flagged scope limit.
- **Intrinsics block — full 8-seed (four-zoom × two-unit) confirmation (graduates `four_zoom_two_unit`):**
  all 8 seeds carry the 16×field-13 intrinsics block with the 5+5+6 layout. **Per-body constant** — within a
  unit the payload + unit-sig + tier fx are identical across all four zoom captures (intrinsics are
  focal-independent factory calib). **Two units differ:** U1 fx[cam0/5/10]=`3376/8283/18795` (sig
  `722a6e72…`, payload 32832 B); U2 `3373/8281/18684` (sig `223961c6…`, payload 32833 B). **Block index
  varies** (blk3 or blk4 per file) ⇒ the "smallest 16×f13 block" selection heuristic is necessary (a fixed
  index mis-selects). (U1 fx corroborates Claim 2 above; U2 cam0 3373 corroborates the cross-unit cam0
  re-parse. U2 cam5/cam10 = the tool's deterministic parse, not separately spot-checked.)

## Residuals (still owed)
- **Unit-2 universality** — all parses here are Unit-1; factory-constant proven within one body across 4 focals,
  NOT across bodies (identity camids {1,15}, corner magnitudes, AWB may differ on Unit-2).
- Block-4 `f2` secondary 896/897-B table role; channel ordering (R/Gr/Gb/B by position, not proven); vignetting
  index 100..775 semantics (ISO/radius?) inferred not proven.
- How libcp CONSUMES these grids at render time (this is static LRI parse; runtime apply not in this doc).
- Each filewide "ToF" ASCII hit's byte context not individually classified (proto-signature scan = 0 is the
  load-bearing negative).
