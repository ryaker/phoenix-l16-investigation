<!-- provenance: workflow wf_86500d78-8bf (l16-prefusion-fanout-w3), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Block-6 Deep Decode — L16_02130.lri (2018-07-23), Block index 6 (payload 35266B)

All claims re-extractable via: `python3 tools/lri_field_inspect.py` helpers `scan_lri_blocks()` + `parse_proto_fields()` (generator -> wrap in `list()`). Block index 6.

### Corrected structural map (vs briefing)
- Briefing said "f2.1 discriminator", "f2.2/f2.3 matrices". Actual nesting:
  - **Outer** field-13 record: `f1`(varint)=**camera_id**, `f2`(wt2)=payload submessage.
  - **Inner f2**: `f1`=**discriminator** {0,2,6}; `f2`,`f3`=two **3x3 CCMs** (45B each, 9 packed fixed32); `f4`,`f5`=scalars (floats); `f6`=24x **RGB-triplet** records (15B = 3 fixed32); `f8`=**950B shading submessage** (only when disc==2).
- 42 records = 14 cameras x 3 disc variants. 14 large (1472B, disc==2) + 28 small (519B, disc 0/6). **f8 present iff disc==2** (OBSERVED, all 14).

### Q1 — f2.8 (~950B) contents
OBSERVED: `f8` = `{f1=1; 3x f2 subrecords of 313B}`. Each 313B subrecord = `{f1=380, f2=755, f3=304-byte blob}`. The 304B blob = **76 float32**. Three subrecords = R/G/B channels. Per-channel ranges: R[0.096..96.07], G[0.062..142.54], B[0.000..104.52], rising monotonically from ~0.3 to ~100.
- VERDICT: **per-channel 1D radial lens-shading / vignette gain curve** (76 samples/channel). NOT a 3D-LUT cube, NOT per-pixel (76 floats is a radial profile; 380/755 are downsample/dimension hints, not a pixel array). It is the highest-resolution correction in Block-6 and is attached only to the disc==2 variant.

### Q2 — camera-id set
OBSERVED: outer-f1 ids = `{0,2,3,4,5,6,7,8,9,10,11,12,13,14}` — exactly 14, **missing {1,15}**. Confirmed.
- LEAD (NOT proven): mapping "{1,15} excluded -> a specific L16 module/focal subgroup" is **not derivable from Block-6 bytes**. Block-6 has no lens_type/focal field. The id->module(A1..C6) assignment lives in Block-3 (16 cams incl 1,15) / HwInfo `lens_type`. Needs that cross-decode or runtime to name the excluded pair.

### Q3 — row-sums (0.964,1.0,0.825) cross-check
OBSERVED: these are the row-sums of inner-f2.**f2** (= M2), a green-preserving 3x3 CCM: rows sum (0.96422, **1.00000**, 0.82521), middle row exactly 1.0, det 1.0736. inner-f2.**f3** (M3) is a *different* matrix (rowsums 0.588,1.030,0.698; det 0.330; NOT inv(M2)).
- Cross-block: M2[0,0]=0.89960134 occurs **exactly once in the whole file** (offset 162589439, inside Block-6). It is **NOT mirrored** in Block-3, LightHeader AWB (f20), HDR params, or any other color field. **Block-6 is the sole carrier of this CCM.** (Refutes the "matches another block" prediction half.)
- Disc invariance: for a fixed camera, M2 is identical across disc {0,2,6}; only scalars f4/f5 differ. So disc = illuminant/exposure variant, M2 = per-camera color matrix.

### Scope-bound disclaimers
- 28mm seed only (L16_02130 2018-07-23 = Unit-1). NOT verified on 70/150/35mm or Unit-2 twins.
- Field NAMES (CCM, shading) are interpretive labels from value shape, not from libcp symbols — I did not disassemble the consumer of Block-6. No runtime trace; no proof these are *applied* by the pipeline. Static-LRI-parse only.
- The disc 0/6 (519B) records share M2/M3/f6 with disc2 but I only spot-checked M2 equality, not f3/f6 equality across disc.