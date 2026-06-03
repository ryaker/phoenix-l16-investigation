<!-- provenance: workflow wf_79b566a0-51d (l16-b2-finish-w7), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed).
**Verifier reliability:** core structure PASS; a value-characterization claim FAILED and is corrected below (LEAD)

## Distortion LUT decode — cam0, L16_02130 (2018-07-23), block3 f13[0]

Nesting confirmed (NOT in block0 LightHeader; per-camera calib is block3 f13, 16 entries):
`block3 -> f13[cam] -> f3(calib) -> f3(distortion,1682B) -> {f1 intrinsics 63B, f2 LUT-container 1614B}`

### (4) f3.3.1.1 / f3.3.1.2 (asked) — cam0
- **f3.3.1.1 principal point = (2063.0, 1534.0) px** (two fixed32 in 10-byte sub-msg)
- **f3.3.1.2 sensor dims = (4160.0, 4160.0) px**
- f3.3.1.3 = 20-byte PACKED f32 (not sub-msg): **[k1=0.032641, k2=0.150078, 0.0, 0.0, k3=-0.577447]** pure-radial Brown-Conrady (matches KNOWN).
- f3.3.1.4 = 0.000376374 (scalar). f3.3.1.5 = 10-byte sub-msg, fields did not parse as fixed32 (likely zero/empty pair) — not investigated further.

### (1) f3.3.2.5 — 101 (x,y) pairs CONFIRMED
- Wire: each entry 10 bytes = `0x0d`+f32(x) + `0x15`+f32(y).
- **x: strictly increasing, 0 -> 2.890720, uniform step ~0.028907** (= x_max/100). Domain matches KNOWN 0->2.89.
- **y: non-monotone, 0 -> peak 31.6512 @ idx72 (x=2.0848) -> 29.7071 @ idx100.** Fold-back confirmed.
- **x meaning (LEAD):** a NORMALIZED field/object radius on a uniform grid; NOT field angle in radians (2.89 rad = 165 deg is unphysical for these FOVs). NOT r-squared (uniform-in-x, monotone).
- **y meaning (LEAD):** an IMAGE-side radius (forward field map object-radius->image-radius). Fold-back rules out magnification (would be ~O(1)) and rules out a monotone corrected-radius. Near-origin slope dy/dx ~ 22.4 for cam0, and this slope drops with focal (cam8 5.83, cam15 4.30) — i.e. it scales like an effective focal/projection factor.

### (2) f3.3.2.6 — 30 (x,y) pairs CONFIRMED
- **x: uniform 0 -> 2.9, step 0.1** (same domain as c5, coarser grid).
- **y: tiny signed, -0.000016 -> +0.000472 @idx4 -> monotone-ish down to -0.023715 @idx29** (thousandths). This IS a small correction/residual-magnitude curve (units of normalized radius), distinct y-scale from c5.

### (3) Redundant vs Complementary — COMPLEMENTARY (verdict, byte-level)
- Best-fit scaled poly `B*poly(A*x)` (A=0.404, B=42.1, chosen so fold peaks coincide) fails to match c5: **max abs error 36.9 on y-range 31.65 (>100% at field edge).** Poly is a 3-term gross model; c5 is a finely-sampled empirical curve. NOT two encodings of one function.
- c6 is NOT c5's residual: ratio c5(dev-from-linear)/c6 is non-constant (-16 .. 1.6e5). c5 and c6 are independent curves with independent y-scales.
- Direct poly eval over c5's domain diverges negative for x>~1.4 (k3=-0.577 dominates) -> the poly's valid domain is far smaller than the curve domain, so the poly cannot be the runtime full-field undistort.

### Per-camera variation (corpus caution)
- Curves are per-lens: cam0/1 (wide) ymax 31.65 slope 22.4; cam8 ymax 11.59 slope 5.83; cam15 (tele) ymax 13.28 slope 4.30. f3.3.2.2/2.3 scalars scale with each curve (cam0 3.70/2.56; cam8 9.30/9.83) — candidate per-curve x/y axis scale factors (LEAD, unconfirmed).

### Proposed clean-room undistort eval order (LEAD — needs libcp runtime confirmation)
A parser should treat the **101-entry f3.3.2.5 LUT as the primary forward field map** (interpolate y as a function of normalized field radius x over [0,2.89]), use **f3.3.2.6 as a small additive correction** on the normalized radius (likely a higher-order or chromatic/residual term), and treat **f3.3.1.3 poly as the analytic base/seed model** (the LUT's likely generator over its valid sub-domain) — apply the LUT, not the poly, where their domains diverge. f3.3.2.2/2.3 are candidate axis scales to map normalized -> physical units. I did NOT trace which structure libcp consumes, so the consumption order is a LEAD, never proven.

## Verifier correction(s)
- **Computed: rd=ru*(1+k1*ru^2+k2*ru^4+k3*ru^6) with coefficients from f3.3.1.3, evaluated over c5.x domain [0, 2.890720]**: Polynomial goes negative at x=1.145 (binary search: zero crossing between 1.14 and 1.15), NOT at ~1.4. Discrepancy: 0.26 in x (23%). Conclusion that poly diverges within c5 domain is correct; stated threshold ~1.4 is wrong. Actual valid domain is roughly [0, 1.14], claim states [0, 1.4].
