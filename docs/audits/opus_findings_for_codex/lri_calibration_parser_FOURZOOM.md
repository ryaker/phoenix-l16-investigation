<!-- GRADUATED finding. provenance: W3 four-LRI re-parse (a6f8ca771a056bf56) + orchestrator block-count verify, 2026-06-03. Consolidates the lane-B2 LRI-calibration staging working-docs. -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to four-LRI OBSERVED** (Tier 1). For LRI-resident findings,
re-parse across all four canonical LRIs IS the four-zoom rigor (these are deterministic file-structure facts,
not render-path behavior). Tool: `tools/lri_field_inspect.py` (`scan_lri_blocks` + `parse_proto_fields`).
**Scope: all four are Unit-1 → Unit-2 universality UNTESTED** (same-name twins `2018-07-04/L16_02130`,
`2018-10-28/L16_03041`, `2020-07-14/L16_03434`, `2018-07-07/L16_02285` not parsed).

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

## Residuals (still owed)
- **Unit-2 universality** — all 4 here are Unit-1.
- Block-4 lens-shading internal grid dims (16×17×13×4×4) and Block-5 vignetting internal grid NOT re-verified
  by W3 (inventory-level only) — those staging docs stay Tier-0 pending an internal-grid 4-LRI pass.
- Each filewide "ToF" ASCII hit's byte context not individually classified (proto-signature scan = 0 is the
  load-bearing negative).
