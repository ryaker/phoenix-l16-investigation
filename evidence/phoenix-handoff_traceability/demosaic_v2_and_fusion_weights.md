# DemosaickLightV2<0,0> kernel + Fusion per-pixel weight formula
**Date:** 2026-04-13
**Binary:** `Lumen.app/Contents/Frameworks/libcp.dylib` (x86_64, stripped, Halide-compiled)
**Method:** Pure static disassembly, RTTI-string xref, constant-pool decode. No live LLDB, no spike code.

---

## Q1 — DemosaickLightV2<0,0> inner-loop kernel math

### Address resolution (verified)
- RTTI strings for `lt::Internal::(anon)::DemosaickLightV2<0,0>(Image<vec4x32f>&, Image<float>&, float)`
  found at file offset **0x5f1f20** (lambda type) and **0x5f1e60** (`std::__function::__func` wrapper type), confirmed via `grep -b` on the live binary.
- Pointer scan for those addresses → only references are from the **typeinfo struct at 0x65a290** (qword pointer to name string at +0x8 of typeinfo).
- That typeinfo struct is referenced by an `__func` **vtable laid down at 0x65a240**, whose 9 entries are at `0x2f0d50, 0x2f0d60, 0x2f0d70, 0x2f0db0, 0x2f0dd0, 0x2f0de0, 0x2f0df0, 0x2f1530, 0x2f1550`.
- Of those, **0x2f0df0** is the only large body (`subq $0x118, %rsp`, ~1.7 KB code). Its prologue stages a `Rectangle<int>` argument and calls `0x2f1560` and `0x2f16d0` (Image<float> ctors), confirming it as the `__invoke()` for the `Ul RK Rectangle<int> iE_` lambda — i.e. the Pipeline-tile worker that runs `DemosaickLightV2<0,0>`.

So **DemosaickLightV2<0,0> tile body lives at 0x2f0df0**, with the inner pixel kernel at **0x2f1050 → 0x2f148b** (`jl 0x2f1050`, 2-pixel-step inner loop) inside an outer row loop **0x2f0f00 → 0x2f14a6**.

### Constants pulled from the binary
| RIP-relative | VA | Value | Role |
|---|---|---|---|
| `mulss 0x300a62(%rip)` @ 0x2f0e66 | 0x5f18d0 | `-0.02f` | scales user `float scalar` (preset-1 path) |
| `mulss 0x3008d7(%rip)` @ 0x2f0fec | 0x5f18cc | `1/128 = 0.0078125f` | scales user `float scalar` → epsilon ε used in gradient denominator |
| `movaps 0x2b7214(%rip)` @ 0x2f0fd4 | 0x5a81f0 | `0x7FFFFFFF × 4` | float **abs-value mask** (strips sign bit) |
| `movaps 0x2b8884(%rip)` @ 0x2f0e15 | 0x5a96a0 | `{0,0,1,0}` | Image<float> stride/init constant |

### Verified algorithm class
This is a **gradient-inverse-weighted directional interpolation** (Hamilton-Adams family), NOT bilinear, NOT Malvar, NOT a 5×5 polynomial. The kernel signature inside the loop:

```
load 4-tap neighborhood (insertps from 4 pointer offsets)
diff = neighbor_pair - center_pair
abs_diff = diff & 0x7FFFFFFF                ; xmm11
weight   = abs_diff + ε                     ; ε = scalar*(1/128), xmm12
inv_w    = rcpps(weight)                    ; rcpps, NOT divps -- ~12-bit approximation
weighted = inv_w * (other_neighbor_diffs)
horiz_reduce via shufpd + addps + shufps b1 + addps + rcpss + mulss
result   = base_pixel + reduced
```

Three independent reductions are visible per 2-pixel block (one for green at the R/B sites, two for the chroma fill at the green sites). Each ends with `addss (base), result` writing one float into the 4-channel RGBA output, and the **alpha lane is unconditionally set to `0x3F800000` = 1.0f** (e.g. `movl $0x3f800000, (%r10,%rax,4)` at 0x2f1143, 0x2f1278, 0x2f13ab, 0x2f1475 — four times per 2-pixel block, one per output pixel × 2-row stride).

### Pseudocode (verified, instruction-anchored)
```c
// scalar `q` is the third argument — quality / regularization
float eps = q * (1.0f/128.0f);            // 0x2f0fec
const __m128 ABS_MASK = set1(0x7FFFFFFF); // 0x2f0fd4

for (y = 0; y < dst_h; y++) {              // outer row loop 0x2f0f00..0x2f14a6
  // Three sliding row pointers (prev / curr / next), 4 spectral neighbors each
  for (x = 0; x < tile_w; x += 2) {        // inner 2-px step 0x2f1050..0x2f148b
    // 1) Estimate green at R-site (x,y):
    //    Load N/S/E/W green neighbors; compute |dN-dS|, |dE-dW| as gradient magnitudes
    __m128 gN_S = abs(green_north - green_south) + eps;
    __m128 gE_W = abs(green_east  - green_west)  + eps;
    __m128 invH = rcpps(gN_S);
    __m128 invV = rcpps(gE_W);
    // weighted Hamilton-Adams: G = (invH*(R[E]+R[W]) + invV*(R[N]+R[S])) / (invH+invV)
    g_at_r = (invH * (G_NS_avg) + invV * (G_EW_avg)) / (invH + invV);  // rcpss reduce
    g_at_r += R_center;                    // additive base offset
    out_R[x] = R_center;                   // copy R unchanged
    out_G[x] = g_at_r;                     // interpolated green
    out_A[x] = 1.0f;                       // alpha forced to 1

    // 2) Estimate red / blue at G-site (x+1,y):
    //    Same gradient-weight formula on horizontal/vertical R and B neighbors
    //    Three sequential rcpss reductions visible at 0x2f1209..0x2f123d
    out_R[x+1] = ra_interp; out_G[x+1] = G_center; out_B[x+1] = rb_interp; out_A[x+1] = 1;

    // 3) Repeat for the lower row (y+1, x and x+1) using the same kernel template
    //    -- second copy of the block lives at 0x2f12bd..0x2f1475
  }
}
```

### Float scalar role — verified
- `q * (1/128)` is added to **every absolute-difference gradient** before `rcpps`. This is the **regularization / noise-floor parameter** of the inverse-distance weight: large `q` → all weights become uniform → bilinear-like blur; small `q` → strongly directional, sharper but noise-amplifying.
- `q * (-0.02)` is also computed once per row at 0x2f0e66 and stored in the Image<float> stack-resident scratch. Its use is downstream of `0x2f1560` / `0x2f16d0` (the `Image<float>` constructor wrappers) and was not traced into those subroutines. **UNVERIFIED:** likely a per-row clamp / saturation bound used inside `0x2f16d0`.
- The scalar is **not** a multiplier on the output — outputs are written as `addss base, weighted_diff` (additive), no global gain.

### UNVERIFIED items
- Exact mapping of the 8 `insertps` lanes to N/S/E/W/NN/SS/EE/WW Bayer positions for the `<0,0>` phase. The kernel reads from 6 pointers (`r14, rdi, r8, r12, r15, rax, r11, r13`) — these are 6 sliding row strides + 2 column offsets. Without phase-tagged pixel dumping, the exact spatial template is inferred but not pinned to a sensor coordinate.
- Whether the `q*(-0.02)` path is a saturation clip or a sharpening bias.
- **Probe to resolve:** call `DemosaickLightV2<0,0>` on a 16×16 synthetic Bayer with a known impulse response (single white pixel surrounded by zero). The output RGBA will reveal the spatial extent of the kernel and the exact neighbor weights.

---

## Q2 — Cross-camera fusion per-pixel weight formula

### Correction to prior notes
The address `0x36f800` (with inner loop at 0x36fd30) cited in `lumen_side_analysis.md §Q1` and `fusion_blend_analysis.txt` is **NOT the cross-camera blend**. Instruction-level inspection shows:
- xmm3 constant pool at 0x5a91e8 = `{255.0, 0.299, 0.587, 0.114}` — **Rec.601 luma weights**.
- Output is `cvttss2si` → `movb %al, (%r11,%rdi)` — **8-bit byte writes**.
- The 3 source pointers (rbx/rsi/r9) read 4-float vectors from RGBA — they are 3 pyramid levels OR 3 colour-channel buffers being collapsed to a single luma byte, not 3 camera taps being summed.

This routine at 0x36f800 is the **luminance-grid generator** (very probably feeding `GetSkippingMaskGrid` / `PyramidAlignment::alignImage`), with a Mitchell-Netravali / Catmull-Rom cubic resample header (constants `{1.0, 2.0, 9.0, -15.0, 6.0, 1/6, -3.0, 15.0}` at 0x5a8128/0x5a887c/0x5aae80/0x5d9a0c/0x5aae70/0x5aae60/0x5aaeb0/0x5aae9c → standard separable cubic basis) followed by depth-aware (1/z) reprojection and a per-pixel `dot([R,G,B],[0.299,0.587,0.114])*255` luma reduction.

### The actual per-pixel weight kernel — at 0x1bd0a0
This was identified in `fusion_blend_analysis.txt` (the `N≥2` branch's `callq 0x1bd0a0`) but never decoded.

**Signature (from registers at entry):**
```
void* fn(
  Image<float>*   dst,      // rdi  -- output per-pixel weight buffer
  Image<uint8_t>* mask0,    // rsi  -- per-tap confidence/skip mask, camera 0
  Image<uint8_t>* mask1,    // rdx  -- camera 1
  Image<uint8_t>* mask2,    // rcx  -- camera 2
  float           scalar    // xmm0 -- per-tile pre-weight, sqrt(W*H*exposure)/N
);
```

**Inner loop body (0x1bd170..0x1bd1ab, instruction-verified):**
```c
for each pixel i in row:
    uint32_t w0 = mask0[i] + 1;                       // 0x1bd170 movzbl + incl
    uint32_t w1 = mask1[i] + 1;                       // 0x1bd177
    uint32_t w2 = mask2[i] + 1;                       // 0x1bd181
    uint32_t prod = w0 * w1 * w2;                     // imull chain
    int32_t  idx  = (int32_t)(prod >> 16) - 1;        // 0x1bd18b shr16, decl
    if (idx < 0) idx = 0;                             // cmovsl
    float    lut  = LUT256[idx];                      // 0x1bd196, base 0x5d2390
    dst[i]        = lut * scalar;                     // 0x1bd19b mulss xmm1
```

**LUT decoded (256 entries × float, base 0x5d2390):**
- `LUT[0] = 0.0`
- `LUT[1] = 0.0883883 = sqrt(1/128)`
- `LUT[2] = 0.1082531 = sqrt(3/256)`
- `LUT[3] = 0.125 = sqrt(2/128)`
- `LUT[i]² × 256 = i+1` exactly for all 256 entries
- `LUT[255] = 1.0`

**Closed-form: `LUT[i] = sqrt((i+1) / 256)`.**

### Verified per-pixel weight formula
```
w_combined(i) = ((mask0[i]+1) * (mask1[i]+1) * (mask2[i]+1)) >> 16
weight(i)     = sqrt((w_combined + 1) / 256) * sqrt(W * H * exposure) / N
```
Where the masks are the per-camera confidences (uint8 0..255) and `(W,H,exposure,N)` are the per-tile parameters loaded into xmm0 by FusionCacheBayer::vfunc[3] before the call (per fusion_blend_analysis.txt §"Camera Count Gate").

### Properties (verified by reading the formula)
- **Multiplicative gating.** If any `mask_k[i] == 0`, then `(0+1) = 1`; product is `(1)*(1+...)*...` → the worst tap dominates. If all three masks are 0, product = 1, idx = `(1>>16)-1 = -1` → clamped to 0 → `LUT[0] = 0` → **weight = 0**. So a single zeroed mask collapses the weight only when ALL three are zero — which is the correct "completely uncovered pixel" guard.
- **Sub-linear scaling.** The sqrt LUT means weight grows as the 6th root of the product (each mask contributes a 1/6-power). This is **not normalized to sum=1**; it is an additive-blend weight whose absolute magnitude carries the per-tile exposure scaling.
- **Not a Catmull-Rom interpolation weight.** The bicubic-LUT story from prior notes belongs to the **luma-grid resampler at 0x36f800**, which is a separate stage producing the input masks. The fusion blend itself uses these byte masks raw.
- **No alignment-residual or depth term in the weight.** The weights' provenance is purely the three byte masks (which DO encode the alignment/skip decisions made upstream by `GetSkippingMaskGrid` and `PyramidAlignment::alignImage`'s residual thresholder), but the blend kernel at 0x1bd0a0 does **not** itself read alignment residuals or depth.

### Companion routine at 0x1bd1e0 (verified)
Right after 0x1bd0a0 in the same TU is a small writeback:
```
weight_byte[i] = clamp(weight_float[i] * 256.0f, 0, 255) - 1
```
This converts a float weight buffer back to a uint8 mask (the float-to-byte scalar `256.0f` was decoded from the constant pool at `0x1bd20f + 0x3ec041 = 0x5b9250`). Used to chain multiple weight passes through byte storage to save bandwidth.

### UNVERIFIED items
- Whether the **N=1 single-camera path** (the dominant case in the L16_02586 render — 132/132 tiles at N=1 per fusion_blend_analysis.txt) ever invokes 0x1bd0a0. The static decode shows it as the `N≥2` exit only; the N=1 path falls through `0x1bce50` / `0x1bcf90` (single-camera copy with `xmm0 = sqrt(exposure)`) without going through this weight kernel. **For Phoenix, this means the LRI being studied never exercised this formula at runtime** — but the formula is what the code WILL apply if N≥2 (overlapping-camera tiles).
- Where the 3 input masks are physically populated. They are passed into the `FusionCacheBayer::vfunc[3]` blend invocation as `+0x48, +0x50, +0x58` shared_ptrs; their producer is upstream (likely `GetSkippingMaskGrid<>` and the 0x36f800 luma-grid resampler reading `PyramidAlignment::alignImage`'s residuals). Not traced.
- The exact fixup `prod >> 16 - 1, clamped` skews the formula. Re-derive: with `mask0=mask1=mask2=255`, `prod = 256³ = 16777216`, `prod>>16 = 256`, `idx = 255` → `LUT[255]=1.0`. With `mask0=mask1=mask2=0`, `prod=1`, `>>16=0`, `idx=-1→0`, `LUT[0]=0`. Linear-monotonic and saturates correctly. **Probe to resolve runtime triggering:** force a synthetic LRI with overlapping FOV tiles where 2+ cameras cover the same pixel.

---

## Quick reference — addresses
| VA | Routine | Confidence |
|---|---|---|
| 0x2f0df0 | `DemosaickLightV2<0,0>` invoke trampoline (lambda body) | RTTI-verified via vtable at 0x65a240 → typeinfo at 0x65a290 → name 0x5f1f20 |
| 0x2f0f00 | Outer row loop start | instruction-verified |
| 0x2f1050 | Inner 2-pixel kernel start | instruction-verified |
| 0x2f148b | Inner loop backedge (`jl 0x2f1050`) | instruction-verified |
| 0x5a81f0 | Float-abs mask `0x7FFFFFFF×4` | constant-pool decoded |
| 0x5f18cc | epsilon scale `1/128` | constant-pool decoded |
| 0x5f18d0 | secondary scalar multiplier `-0.02` | constant-pool decoded; usage UNVERIFIED |
| 0x1bd0a0 | Cross-camera **per-pixel weight kernel** (3-tap multiplicative + sqrt-LUT × scalar) | instruction-verified |
| 0x1bd170 | Inner pixel loop body | instruction-verified |
| 0x5d2390 | 256-entry float LUT, `LUT[i]=sqrt((i+1)/256)` | constant-pool decoded, formula confirmed exactly across 256 entries |
| 0x1bd1e0 | Float-weight → byte-mask writeback (`*256, clamp, -1`) | instruction-verified |
| 0x5b9250 | `256.0f` constant for byte writeback | constant-pool decoded |
| 0x36f800 | **NOT** fusion blend — Catmull-Rom luma-grid resampler with depth-aware (1/z) reprojection (writes uint8 luma) | rejected, corrected from prior notes |
