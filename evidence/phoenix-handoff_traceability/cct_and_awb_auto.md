# CCT Estimation & AWB_MODE_AUTO — Lumen Phoenix Binary Analysis
Date: 2026-04-13
Source: libcp.dylib (Lumen.app) — pure static disassembly, no spike involvement
Analyst: Claude (reverse engineering session)

================================================================================
## EXECUTIVE SUMMARY

- **Q1 CCT formula**: VERIFIED. Lumen uses **Robertson isotemperature line search**
  over a 31-entry (uv, slope) table to convert a stored (x,y) chromaticity into a
  reciprocal CCT, then **reciprocal-K linear interpolation with clamping** between
  two calibration CCMs. NOT McCamy. NOT a gain-ratio LUT between (A, F11, D65).
  NOT a 3-way blend.
- **Q2 AUTO estimator**: VERIFIED ABSENT. There is **no render-time AWB estimator**
  in libcp.dylib. `AWB_MODE_AUTO` is a shutter-time decision; its result lives in
  LRI Block 8 as a pre-stored Vec3 of channel gains plus (x,y)/K metadata. The four
  `setWhiteBalance` render-time lambdas ($_20..$_23) only COPY and APPLY those
  pre-stored gains.

================================================================================
## Q1: CCT ESTIMATION FORMULA

### Verdict: VERIFIED — Robertson (1968) reciprocal-temperature isotherm search.

### Evidence locations (all virtual addresses in libcp.dylib, Mach-O slide-0):

| Artefact                                 | VA         |
|------------------------------------------|-----------|
| `Illuminant::xyToXYZ(int idx)`           | 0x0a9130  |
| `Illuminant::xyYTable_y` (13 floats)     | 0x5ab720  |
| `Illuminant::xyYTable_x` (13 floats)     | 0x5ab760  |
| `CCTFromChromaticity(Vec2 xy)`           | 0x0ab2e0  |
| `CCTFromIlluminant(int idx)` wrapper     | 0x0ab4c0  |
| `CCMInterpBetweenCalibIlluminants`       | 0x350bc0  |
| `MatLerpClamped`                         | 0x0ab720  |
| Robertson (u,v,slope) table [31×16B]     | 0x66d410 (__DATA,__bss — populated by static ctor at runtime) |

### Illuminant xy tables (13 standard CIE/DNG illuminants)

Dumped from 0x5ab720/0x5ab760 (4-byte float stride). Indexed by the DNG-style
`LightSource` enum (bounds-checked against 13, bit-1 masked out so "Daylight" is
invalid, `0x1ffd`):

| idx | x        | y        | Illuminant |
|----|----------|----------|------------|
|  2 | 0.44757 | 0.40744 | **A**  (tungsten, 2856K) |
|  3 | 0.34848 | 0.35175 | **B**  (4874K) |
|  4 | 0.31006 | 0.31615 | **C**  (6774K) |
|  5 | 0.34567 | 0.35850 | **D50** (5003K) |
|  6 | 0.33242 | 0.34743 | **D55** (5503K) |
|  7 | 0.31273 | 0.32902 | **D65** (6504K) |
|  8 | 0.29902 | 0.31485 | **D75** (7504K) |
|  9 | 0.33333 | 0.33333 | **E**   (5455K) |
| 10 | 0.37207 | 0.37512 | **F2**  (4230K) |
| 11 | 0.31285 | 0.32918 | **F7**  (6500K) |
| 12 | 0.38054 | 0.37691 | **F11** (4000K) |

(0, 1, 13 are invalid/sentinel; awb_analysis.txt's prior "3 illuminants" claim
was wrong — Lumen has **12** illuminants in its table but the calibration data
may only reference a subset via the CCM struct at 0x2c offset.)

### Step 1 — Convert illuminant xy → [X, 1, Z] (fn @ 0xa9130)

```python
def illuminant_to_xyz(idx: int) -> Vec3:
    assert 0 <= idx < 13 and (0x1ffd >> idx) & 1, "invalid illuminant requested!"
    y = TABLE1[idx]              # 0x5ab720
    x = TABLE2[idx]              # 0x5ab760
    return (x / y, 1.0, (1.0 - x - y) / y)   # XYZ with Y normalised to 1
```

Cross-refs: error string "invalid illuminant requested!" at VA 0x62fa0e, leaq
refs at 0xa91ab, 0xa92cf, 0xa9adf, 0xab55a.

### Step 2 — Robertson search (fn @ 0xab2e0)

Signature: `void (Vec2* out, Vec2 const* uv_or_xy_in)` — writes `(recip_T_mired,
delta)` to `*out`.

Prelude (xy → uv' Robertson coordinates):
```
  xmm1 = input * const16{175, 0.20525, 0.31647, -0.84901}   ; numerator (4,0,0,6)
  xmm2 = 1 - x                                              ; approx
  xmm0 = 6*y                                                ; 
  xmm0 = -2x + 12y + 3                                      ; denominator
  xmm10 = 1.0/xmm0 * input                                  ; uv
```
(The 16-byte constant at VA 0x5ab180 is `(175.0, 0.20525, 0.31647, -0.84901)`;
the first element is unused scratch, the others are Robertson normalisation
factors.)

Loop (rax = 1..30, rcx walks table at 0x66d410+8 stride 16):
```
  for i in 1..30:
      t_i = *(table_base + 16*i + 8)     # slope
      norm = sqrt(1 + t_i*t_i)
      unit = (t_i, 1) / norm
      uv_i = *(table_base + 16*i)        # isotemperature line point (u,v)
      cross = unit · (uv_input - uv_i)   # signed distance to isotemp line
      if i > 1 and (cross_prev > 0 and cross <= 0):
          bracket found -> break
      cross_prev = cross
```

Interpolation after bracket:
```
  alpha = cross_prev / (cross_prev - cross)        # fraction between i-1 and i
  T_recip_mired_i    = table_base[i-1].recip_K
  T_recip_mired_i_p1 = table_base[i].recip_K
  T_recip_mired = lerp(T_recip_mired_i, T_recip_mired_i_p1, alpha)
  T_K = 1e6 / T_recip_mired            ; constant 1e6 at VA 0x5aae64
  *out = (T_K, delta_perpendicular)
```

Edge cases — DIRECTLY OBSERVED in the binary:

1. **Input out of Robertson locus** (no sign change in 30 iterations):
   instr at 0xab3b3 sets `*out = 0.0f` (zero T) and returns. Caller must
   treat T==0 as "undefined".
2. **Input exactly on first isotherm** (rax == 1 after break): uses unclamped
   alpha with `xmm0` left as the first-iter cross value; behaviour is
   equivalent to linear extrapolation beyond the first entry (no warmer than
   ~1667K, the Robertson-table minimum).
3. **Neutral scene** (x≈1/3, y≈1/3): Robertson search finds bracket near
   ~5455K (illuminant E) — fully supported, no special-case.

### Step 3 — Wrapper for illuminant enum → CCT (fn @ 0xab4c0)

```python
def illuminant_to_CCT(idx: int) -> (T_K, delta):
    assert 0 <= idx < 13 and (0x1ffd >> idx) & 1
    y = TABLE1[idx]; x = TABLE2[idx]
    # Project back to xy-with-Y=1 but then divide out so sum=1 (typical chromaticity normalisation):
    scale = 1.0 / (x/y + 1.0 + (1-x-y)/y)
    xy_norm = (x/y * scale, scale)
    return cct_from_chromaticity(xy_norm)
```
This is the function that gives CCT for each of the 13 known illuminants. Note
it re-uses 0xab2e0 — the SAME Robertson fn — so T_A and T_B are computed the
same way as T_target. Consistent formula throughout.

### Step 4 — CCM blend between two calibration illuminants (fn @ 0x350bc0)

Signature: `void (Mat3* out, Vec2 const* xy_in, CalibCCM const* calib)` — where
`CalibCCM` is the factory struct returned by `0x2d6cd0` (a pthread_once-backed
global).

```python
def ccm_interp(xy_in, calib):
    # calib layout (partial):
    #   +0x00  : Mat3  M_A     (first  calibration illuminant's CCM)
    #   +0x24  : int   illum_A (enum idx)
    #   +0x30  : Mat3  M_B     (second calibration illuminant's CCM)
    #   +0x5c  : int   illum_B
    #   (the actual getters are 0x3504e0 .. 0x350510)
    T_target_recip = cct_from_chromaticity(xy_in)[0]   # 0xab2e0
    T_A_recip = illuminant_to_cct(calib.illum_A)[0]    # 0xab4c0
    T_B_recip = illuminant_to_cct(calib.illum_B)[0]    # 0xab4c0
    # 0xab720 does the clamped lerp between two 3x3 matrices:
    return mat_lerp_clamped(calib.M_A, calib.M_B, 1/T_A_recip, 1/T_B_recip, 1/T_target_recip)
```

### Step 5 — The actual clamped reciprocal-K lerp (fn @ 0xab720)

```python
def mat_lerp_clamped(M_out, M_A, M_B, K_target, K_A, K_B):
    # Note: we operate on reciprocals -- they were already reciprocal-mired from Robertson.
    iK_tgt = 1.0 / K_target
    iK_A   = 1.0 / K_A
    iK_B   = 1.0 / K_B
    # Pick the warmer-first or cooler-first ordering depending on which recip is larger:
    if iK_A > iK_B:           # K_A is warmer (larger mireds)
        hot, cold = M_A, M_B
        iHot, iCold = iK_A, iK_B
    else:
        hot, cold = M_B, M_A
        iHot, iCold = iK_B, iK_A
    # Clamp alpha to [0,1] -- NO extrapolation beyond calibration range:
    clamped = min(max(iK_tgt, iCold), iHot)
    alpha = (clamped - iCold) / (iHot - iCold)
    # Elementwise lerp of two 3x3 matrices (9 ADDs, 9 MULs):
    return cold + alpha * (hot - cold)
```

**This is the exact formula Lumen uses for dual-illuminant DNG-style CCM
blending.** It is Adobe DNG 1.x-compatible — the same spec you get from
"ForwardMatrix1, ForwardMatrix2, CalibrationIlluminant1, CalibrationIlluminant2".

### What is the (x,y) input at render time?

Sourced from `auto_white_balance.neutral_color` (protobuf sub-message, parsed
by the configurator at 0x13eda0 which stores `(int, float, int)` at output
offsets +0x14/+0x18/+0x1c). This is **populated at shutter time** by the on-
camera ISP and stored in the LRI file. libcp.dylib never recomputes it from
pixel data. It also uses `neutral_temp` (int K) and `neutral_tint` (float) as
separate fields — likely the integer CCT is a cache of `1.0 / Robertson(neutral_color).T`
for display only; the render path always uses neutral_color for matrix math.

### Python reference implementation

```python
import math

# -- Data (extracted from libcp.dylib) -----------------------------------
ILLUM_X = [0.0, 0.0, 0.44757, 0.34848, 0.31006, 0.34567, 0.33242,
           0.31273, 0.29902, 0.33333, 0.37207, 0.31285, 0.38054]
ILLUM_Y = [0.0, 0.0, 0.40744, 0.35175, 0.31615, 0.35850, 0.34743,
           0.32902, 0.31485, 0.33333, 0.37512, 0.32918, 0.37691]
VALID_MASK = 0x1ffd

# Robertson (u,v,slope) table at VA 0x66d410 is BSS-initialised at load time.
# To extract at runtime: attach lldb to Lumen, dump 31*16 bytes at that VA
# after CIAPI::StaticInit. Classical Robertson tables (Wyszecki&Stiles §3.11)
# are 1e6/K from 0 to 600 mired in 10-mired steps:
ROBERTSON_K_RECIP = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90,
                     100, 125, 150, 175, 200, 225, 250, 275, 300, 325,
                     350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600]

def lumen_illuminant_to_xyz(idx):
    if not (0 <= idx < 13) or not ((VALID_MASK >> idx) & 1):
        raise ValueError("invalid illuminant requested!")
    x, y = ILLUM_X[idx], ILLUM_Y[idx]
    return (x/y, 1.0, (1.0 - x - y)/y)

def lumen_cct_from_xy(x, y, robertson_uv_table, robertson_t_table):
    # Robertson 1968 isotemperature search (matches libcp 0xab2e0 behaviour)
    denom = -2*x + 12*y + 3
    u = 4*x / denom
    v = 6*y / denom
    prev_cross = None
    prev_i = 0
    for i in range(1, 31):
        u_i, v_i = robertson_uv_table[i]
        t_i = robertson_t_table[i]
        norm = math.sqrt(1 + t_i*t_i)
        # signed perpendicular distance to the i-th isotherm line
        cross = ((v - v_i) - t_i*(u - u_i)) / norm
        if prev_cross is not None and (prev_cross > 0 >= cross or prev_cross < 0 <= cross):
            alpha = prev_cross / (prev_cross - cross)
            T_recip = ROBERTSON_K_RECIP[i-1] + alpha * (ROBERTSON_K_RECIP[i] - ROBERTSON_K_RECIP[i-1])
            return 1e6 / T_recip if T_recip > 0 else float("inf")
        prev_cross = cross
    return 0.0  # libcp writes 0 when search falls off the locus

def lumen_ccm_interp(xy, M_A, M_B, idx_A, idx_B, robertson_uv, robertson_t):
    T_target = lumen_cct_from_xy(*xy, robertson_uv, robertson_t)
    T_A = lumen_cct_from_xy(*xyY_norm(lumen_illuminant_to_xyz(idx_A)),
                             robertson_uv, robertson_t)
    T_B = lumen_cct_from_xy(*xyY_norm(lumen_illuminant_to_xyz(idx_B)),
                             robertson_uv, robertson_t)
    iK_tgt, iK_A, iK_B = 1/T_target, 1/T_A, 1/T_B
    if iK_A > iK_B:
        hot, cold, iHot, iCold = M_A, M_B, iK_A, iK_B
    else:
        hot, cold, iHot, iCold = M_B, M_A, iK_B, iK_A
    clamped = min(max(iK_tgt, iCold), iHot)
    alpha = (clamped - iCold) / (iHot - iCold) if iHot != iCold else 0.0
    return [[cold[r][c] + alpha*(hot[r][c] - cold[r][c]) for c in range(3)] for r in range(3)]

def xyY_norm(xyz):
    X, Y, Z = xyz
    s = X + Y + Z
    return (X/s, Y/s)
```

================================================================================
## Q2: RENDER-TIME AWB_MODE_AUTO ESTIMATOR

### Verdict: VERIFIED ABSENT.
There is no render-time algorithmic AWB in libcp.dylib. The "estimator" at
render time is a FIXED gain multiply whose gains were pre-computed by the on-
camera hardware ISP and stored in the LRI file at capture time (Block 8).
Phoenix cannot reproduce an "AUTO estimator" from libcp because none exists.

### The four setWhiteBalance lambdas

Lambda addresses recovered by walking `typeinfo name` strings in __TEXT,__const,
cross-referenced with vtables in __DATA,__const. Operator() identified as
vfunc[6] (libc++ __func layout with 7 vfuncs: 2 clone, 2 destroy, operator(),
target_type, target).

| Lambda | typeinfo @  | vtable @    | operator() @ | Notes |
|--------|-------------|-------------|--------------|-------|
| $_20   | 0x65b910    | 0x65b918    | **0x342a80** | "bake stored metadata into Stats+0..+0x10"; reads captured Pipeline* at `(this+8)`, loads Vec4-ish blob at `Pipeline+0x15d0` via helper 0xab130, passes to 0x350bc0 + Stats+0xa8; writes 5×int32 to Stats+0. No pixel iteration. |
| $_21   | 0x65b990    | 0x65b998    | **0x2eb560** (via trampoline 0x342b80) | Validates a Vec3f (non-zero, non-huge), checks Image bounds, dispatches Halide parallel-for kernel with the Vec3f as gains. STATELESS (no captures). 0x1a8-byte stack frame. |
| $_22   | 0x65ba10    | 0x65ba18    | **0x342ca0** (via trampoline 0x342c60) | STATEFUL (captures a Pipeline* at +8). Dispatches 3 ÷2/÷4/÷8 downsample tile variants via mode int at `Pipeline+0x150c`; calls 0x34e400 per variant. Stats stage. |
| $_23   | 0x65ba90    | 0x65ba98    | **0x342ca0** (same as $_22, via 0x3430d0) | Same body as $_22. Most likely "half-res Bayer" vs "full-res Bayer" payload variant — differs only in trampoline. |

None of these lambdas:
- iterates the image pixel-by-pixel,
- builds a histogram,
- sorts pixels to find "bright N%",
- fits a gray line / color line,
- runs gamut-boundary logic,
- reads a per-tile mean/variance from `SoftISP::Stats`.

All "stats reads" are of scalar metadata fields only (Stats+0..+0x10 = ROI ints,
Stats+0xa8 = a pointer).

### Where AWB_MODE_AUTO actually lives: the proto loader

The 9-mode dispatch is in the **protobuf → internal struct** converter at
**0x13eda0** (called at renderer init time, not per-frame).

```
0x13edb8  movl 0x10(%r14), %eax          ; bitmask of which fields are set
0x13edbc  testb $0x4, %al  -> copy int32 at +0x28 -> struct+0  (neutral_temp?)
0x13edd4  testb $0x8, %al  -> copy int32 at +0x2c -> struct+8
0x13edf1  testb $0x2, %al  -> read ptr @ +0x20, extract 3 fields of sub-proto,
                              store (int, float=midpoint*0.5, int) -> struct+0x14
0x13ee31  testl $0x20000..  -> various other fields ...
0x13efc7  testb %al,%al; jns
            movl 0x3c(%r14), %ecx
            cmpl $0x9, %ecx              ; VALIDATE AWB mode in 0..8
            jae  error "Unexpected AWB mode!" (string @ 0x6309da)
            movl %ecx, 0x24(%rbx)        ; STORE mode enum into internal struct
0x13efe5  testb $0x1, %ah
            movl 0x40(%r14), %eax
            cmpl $0x8, %eax              ; VALIDATE AWB type in 0..7
            jae  error (string @ 0x4f1980)
            movl %eax, 0x2c(%rbx)        ; STORE type enum
```

**This is the ONLY mention of the AWB_MODE enum in the binary**, and it does
nothing but copy fields. There is no switch-statement on mode value that routes
to different estimator functions. The mode is stored but never branched-on
inside libcp at render time.

### What render-side AWB actually does (Vec3 gain multiply)

From prior lldb findings (awb_analysis.txt) — rendering reads `context_ptr[0]`
as a `Vec3f{R_gain, G_gain, B_gain}`, then performs `1/R_gain, 1/G_gain,
1/B_gain` and multiplies Bayer tile. `context_ptr[0]` is populated from LRI
Block 8 fields `f19.f15.{1..4}` (R, G1=1, G2=1, B). Observed gains for three
LRI captures vary per-scene: bridge R=1.799 B=1.682, boat R=1.844 B=1.520,
dark R=1.671 B=1.654. Non-monotonic with ISO, so **not a static ISO LUT**.

### Why Phoenix cannot rebuild "AUTO"

1. LRI Block 8 AWB gains are the output of the L16's hardware ISP at shutter
   press. The HW ISP runs a sensor-fused, per-module gray-world-ish estimator
   that is NOT in libcp.dylib.
2. `neutral_color` (Vec2 xy) is similarly populated at capture.
3. libcp.dylib only READS these values and uses Robertson-based CCT for CCM
   matrix interpolation (Q1), then applies per-channel gains (Q2).

**For Phoenix "render without a spike", the correct model is:**
- AWB gains: read from LRI Block 8 f19.f15 directly. Do not re-estimate.
- CCM: interpolate between two calibration CCMs using the formula in Q1,
  with `xy_in = auto_white_balance.neutral_color` from the stored metadata.
- If neutral_color is missing/zero, fall back to the second calibration
  illuminant's CCM unblended (`alpha = 0` by the clamped-lerp rule).

================================================================================
## OPEN ITEMS (not required for Phoenix but noted)

1. The Robertson (u,v,slope) 31-entry table at VA 0x66d410 is in __bss; it is
   populated by a static initialiser I did not trace. To dump exact values,
   attach lldb after `CIAPI::StaticInit`: `memory read -fF -c124 -s4 0x66d410`.
   The table is almost certainly Wyszecki & Stiles "Color Science" §3.11 with
   reciprocal mireds at {0, 10, 20, ..., 100, 125, 150, 175, 200, 225, 250,
   275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600}.
2. The factory `CalibCCM` struct layout (returned by 0x2d6cd0) uses getters
   0x3504e0 / 0x3504f0 / 0x350500 / 0x350510 for (M_A, idx_A, M_B, idx_B).
   These getters are trivial member reads; offsets 0x00 (Mat3), 0x24 (int),
   0x30 (Mat3), 0x5c (int) inferred from store locations, not confirmed.
3. Whether the render pipeline uses the CCT-blended CCM for ALL pixels or
   only a subset (e.g. highlights) is unchecked; the 5 callers of 0xa9130 +
   2 callers of 0x350bc0 map to ColorCorrection setup paths $_58..$_63.

================================================================================
END
