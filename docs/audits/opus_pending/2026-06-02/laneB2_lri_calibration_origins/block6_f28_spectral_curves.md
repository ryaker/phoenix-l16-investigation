<!-- provenance: workflow wf_6de845a7-df9 (l16-b2-lri-w5), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, deterministic LRI byte-parse, single seed 28mm Unit-1 unless noted).
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## Block-6 f2.8 decode — seed `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (28mm, Unit-1)

**Verdict (OBSERVED, parsed bytes):** f2.8 is a per-camera, per-channel **spectral sensitivity curve set** — NOT a lens-shading grid, NOT a LUT, NOT a matrix, NOT a polynomial.

### (1) Field enumeration of the ~950B f2.8 sub-message
`block[6].field13[rec].field2.field8` (rec = an f2.f1==2 "large"/1472B record):

| Path | Wire | Count | Value / Range |
|---|---|---|---|
| f2.8.f1 | varint (wt0) | 1 | =1 (selector/version) |
| f2.8.f2 | bytes (wt2) | **3** | each len=313 (one per channel) |

Each 313B channel sub (`f2.8.f2[k]`):

| Path | Wire | Value |
|---|---|---|
| .f1 | varint | **380** (start nm) |
| .f2 | varint | **755** (end nm) |
| .f3 | bytes | **304 B = exactly 76 float32 LE** |

### (2) Classification — parsed evidence
- 304/4 = **76 float32**, does not re-parse as nested proto.
- `(755-380)/75 = 5.0` exactly => **76 samples @ 5nm step, 380-755nm** (visible + near-IR).
- Curve is **non-monotonic**: single broad peak then decay (so NOT a ramp/LUT; NOT a grid — count 76 is prime-ish and the two leading scalars are wavelengths, not W/H; NOT a small polynomial).
- 3 channels peak at distinct wavelengths => **R/G/B spectral response**:
  - chan0 peak @ **595nm** (idx43)
  - chan1 peak @ **525nm** (idx29)
  - chan2 peak @ **470nm** (idx18)

### (3) Cardinality
- f2.8 present **only** in f2.f1==2 variant, **exactly once per camera (14x)**.
- All 28 records with f2.f1 in {0,6} have **f2.8_len=0**.
- All 14 share range (380,755) + 3-channel layout; curve **values differ per camera** (per-unit calibration). Cameras 10-14 show ~35% lower peak transmission than 0-9 (likely a distinct module/lens class).

### Re-extraction
```
python3 tools/lri_field_inspect.py  (use scan_lri_blocks -> blocks[6]['payload'];
 parse field13 records; rec.field2 -> field8 -> field1=1 + 3x field2(313B);
 each 313B -> f1=380,f2=755,f3=304B; struct.unpack('<76f', f3))
```

**LEAD (inferred, not byte-proven here):** these 76-tap spectral curves are render-time color/white-balance inputs (consistent with Block 6 = per-camera color/shading calibration, alongside the f2.2/f2.3 3x3 color matrices). The exact libcp consumer was NOT traced in this LRI-only parse.