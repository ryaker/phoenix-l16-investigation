<!-- provenance: workflow wf_6de845a7-df9 (l16-b2-lri-w5), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, deterministic LRI byte-parse, single seed 28mm Unit-1 unless noted).
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## Clean-room undistort spec — Block-3 distortion fields (seed L16_02130.lri, 2018-07-23, Unit-1)

All values OBSERVED via deterministic byte-parse with `tools/lri_field_inspect.py` (`scan_lri_blocks`, `parse_proto_fields` wrapped in `list()`). Re-extractable.

### Field tree (path resolution for the thread's "f3.3.x" notation)
- Block idx **3**, abs payload offset **0x9ac6020** (162291744), 32832 B.
- Top level: field6,7 (varint), field8 (3B), **field13 repeated x16** (one per camera, 1944/2149 B), field18 (12B).
- Per camera: `field13[cam]` -> field1 = camera index (0..15), field3 = 1924 B calib sub-msg, field7 = 13 B.
- `field3` -> field1=0, field2 x3, **field3 = 1682 B ("f3.3")**, field4/5 = 10B.
- **f3.3** -> field1 = "**f3.3.1**" (63 B), field2 = "**f3.3.2**" (1614 B).

### (1) f3.3.1.3 — 5-coeff polynomial (CANDIDATE Brown-Conrady [k1,k2,p1,p2,k3])
20 bytes = 5x LE float32. cam0 @ abs **0x9ac6137**: `[0.03264, 0.15008, 0.0, 0.0, -0.57745]`.
**Positions 3 & 4 (p1,p2) = EXACTLY 0.0 for ALL 16 cameras** -> pure-radial, tangential disabled. CONFIRMED.
Three optical-group clusters (matches L16 5x28 / 5x70 / 6x150 layout):

| group | cams | k1 | k2 | k3 |
|---|---|---|---|---|
| wide(28) | 0-4 | +0.033..0.038 | +0.13..0.15 | -0.55..-0.58 |
| tele(70) | 5-9 | +0.021..0.023 | -0.067..-0.083 | +0.036..0.060 |
| super(150) | 10-15 | +0.027..0.039 | -0.24..-0.28 | +0.27..0.33 |

Also in f3.3.1: field1 = principal point (cx,cy) e.g. cam0 (2063,1534); field2 = (4160,4160) (sensor extent); field4 = small float (~3.8e-4); field5 = 10B sub-msg (un-decoded).

### (2) f3.3.2.5 (101-entry LUT) and f3.3.2.6 (30-entry LUT)
Each entry = 10 B sub-msg `{field1=fixed32 x, field2=fixed32 y}`. cam0 LUT5 entry#1 @ abs **0x9ac6188**.

**f3.3.2.5 (101 pts):** x = UNIFORM-step radius-like domain. Group-dependent x-max: 2.891 (wide), 3.001 (tele), 3.074 (super). y = a magnification/displacement curve, **non-monotone in wide+tele** (cam0 peak 31.65 @ idx72 then down to 29.71; cam5 peak 11.59 @ idx83) but **monotone increasing in the 150mm group** (cam10 peak 13.28 @ idx100). Origin slope dy/dx = 22.40 (cam0) / 5.83 (cam5) / 4.30 (cam10) -> a per-group gain, NOT unity. LEAD: y's physical unit (px vs mm vs normalized) is NOT pinned by bytes; corner radius ~2620px ≠ y-range cleanly.

**f3.3.2.6 (30 pts):** x = UNIFORM 0.1-step over [0, 2.9], **identical grid for all cameras/groups**. y = small SIGNED residual, range ~[+0.00047 .. -0.0237], shape: tiny positive bump near r~0.4, then descending negative. CANDIDATE = fine residual-correction curve riding on top of the coarse LUT5/poly.

f3.3.2 scalars: field4 = 0.0011 (constant); field2/field3 per-group (3.700/2.557 wide, 9.297/9.827 tele, 20.271/13.321 super) — likely domain-scale or focal constants; field9 per-camera int-like float; field10 per-camera small float; field7 = 0.0.

### (3) Redundant vs complementary + evaluation order
**COMPLEMENTARY, not redundant** (byte-level): feeding LUT5.x into the 5-coeff poly as r diverges (r_d = -90.6 @ x=2.08, -940 @ x=2.89) whereas LUT5.y stays bounded ~30. They are different objects in different domains/scales (poly slope 1 at origin vs LUT5 slope 22.4).

**Proposed clean-room evaluation order (LEAD — derived from byte semantics, not runtime-verified):**
1. Pick the per-camera distortion record: block3 -> field13[cam] -> f3 -> f3.3.
2. Normalize pixel (px,py) -> centered by principal point f3.3.1.1 (cx,cy), giving radius r.
3. Map r into the LUT domain using the per-group scalar(s) f3.3.2.2 / f3.3.2.3 (these set x-domain scale; exact formula is a LEAD).
4. Evaluate the COARSE curve: either the 5-coeff radial poly f3.3.1.3 (compact form) OR interpolate the 101-pt LUT f3.3.2.5 (tabulated form). They are alternate representations of the coarse radial map; the LUT covers the field edge where the poly diverges, so a renderer almost certainly prefers the LUT for r near the corner.
5. Add the FINE residual from the 30-pt LUT f3.3.2.6 (signed, ~1e-2 magnitude) — this is the "+ residual" stage that makes the pair complementary.
6. Convert corrected radius back to pixel coords (rescale, re-add principal point).

### Scope-bound disclaimer
Parsed ONE seed (Unit-1, 28mm-tier file). Did NOT: confirm which encoding libcp's renderer actually consumes at runtime, pin LUT5.y's physical unit, decode f3.3.1.5 sub-msg, or verify field names (ALL names CANDIDATE). Universality across the second physical body untested.