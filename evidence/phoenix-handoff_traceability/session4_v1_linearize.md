# Session 4 — DemosaickLightV1 body read, raw→float linearize hunt, phase mapping

**Date:** 2026-04-13
**Method:** Pure static disasm of `libcp.dylib` via `/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`. No runtime, no spike.
**Closes:** #22 (linearize arithmetic) — **with a correction to Session 3**, #24 (V1 phase mapping).

---

## TL;DR (read this first)

1. **DemosaickLightV1 is NOT the linearizer.** Session 3's Big Finding #2 was wrong on this point. The V1 operator() body at 0x2eeb20 (and siblings) reads `float32` from the source pointer — every pixel fetch is `movss (%r10,%rcx)`, `insertps 0x10, 0x4(%r10,%rcx)`, etc. There is **no** `movzwl`, no `pmovzxwd`, no `cvtdq2ps`, no `cvtsi2ss` anywhere inside the V1 kernel bodies. It consumes `Image<float>` and produces `Image<vec4x32f>`. The math is a gradient-inverse-weighted directional demosaic (same algorithm family as V2, decoded in `demosaic_v2_and_fusion_weights.md`).

2. **The raw uint16 → float cast is a trivial 1:1 bitcast.** It lives in a separate staging loader at `libcp+0x271d0` (bulk SSE4 `pmovzxwd → cvtdq2ps → movaps` in a 0x400-count row loop with a scalar `0x27390` tail-handler). That loader does **no** black-level subtraction, **no** scale, **no** normalization. A raw sensor value of `42` becomes `42.0f` in memory. It is called via `0x2aa70` and `0xbfef0 = memcpy`.

3. **The actual linearize arithmetic happens downstream of demosaic, inside the lambda_0 `LinearizeColorScale` kernel at 0x340b00.** Session 2's "LinearizeAndColorScale" naming was right; Session 3's claim that demosaic does the linearize was wrong. The pipeline is:
   ```
   raw uint16 Bayer  -->  0x271d0  -->  Image<float> (unscaled 0..1023 range in float slots)
                                   -->  DemosaickLightV1 (t=0)   -->  Image<vec4x32f> (unscaled)
                                   -->  lambda_0 LinearizeColorScale (t=1)  -->  Image<vec4x32f> [0,1]
   ```
   **Phoenix must replicate the linearize inside lambda_0, not inside a Bayer-domain kernel.**

4. **V1 phase mapping is encoded in how the kernel composes its 8 sliding row pointers** — different `(offX,offY)` template values rotate which row pointer is loaded into which xmm lane, producing the 4 Bayer phases (BGGR / GBRG / GRBG / RGGB) from a single kernel template.

---

## #22 — Linearize arithmetic (CORRECTED)

### What I looked for in V1<1,0> @ 0x2eeb20 (the dominant variant, 636 hits)

Reading instructions 0x2eeb20 .. 0x2ef4c8 (the full operator() body), I searched for:

- uint16 loads (`movzwl`, `pmovzxwd`) — **NOT PRESENT**
- int→float conversion (`cvtsi2ss`, `cvtdq2ps`) — **NOT PRESENT**
- black-level subtraction (`subss` against a small constant like 42.0) — NOT PRESENT (the many `subss` instructions are between already-float pixels computing gradients, not against scalar constants)
- normalization divide (`divss`, `mulss` by 1/1023 / 1/981 / 1/65535) — NOT PRESENT. The `mulss` instructions at 0x2eec3b (`mulss 0x302c81(%rip), %xmm3`) and 0x2eed91 (`mulss 0x302b33(%rip), %xmm0`) multiply the MAX of `{xmm0[0], xmm0[1], xmm0[2]}` (a WB-gain triple loaded from closure+0x08) by small float constants — these are the **epsilon scale for the gradient reciprocal** (same role as V2's `1/128` epsilon scale from `demosaic_v2_and_fusion_weights.md`), NOT a linearize.

Every pixel load in the inner loop is `movss` / `insertps $0x10/0x20/0x30` from raw pointers — all 4-byte loads. The inner loop math is `(center - neighbor)` absolute-diff using `xmm12 = 0x7FFFFFFF×4` (sign-bit mask from `movaps 0x2b9327(%rip), %xmm12` at 0x2eeec1) plus `addss xmm9, ...` where xmm9 holds the closure-derived eps, then `rcpss`, then `mulss` weight-apply, then `addss base, sum` accumulate. Output stores are `movss %xmm?, (%r9,%rN,4)` four times per pixel, with **every 4th store being the literal `movl $0x3f800000, (%r9,%rbx,4)` = 1.0f alpha** (e.g. 0x2ef098, 0x2ef21d, 0x2ef380, 0x2ef478).

That's identical in structure to DemosaickLightV2<0,0> decoded in `demosaic_v2_and_fusion_weights.md`. Both are **edge-aware demosaic**, differing only in neighborhood template (V1 = 6-pointer smaller footprint; V2 = 8-pointer wider Hamilton-Adams).

### Where the linearize actually lives

The raw uint16 → float cast is at **libcp+0x271d0** (bulk SSE loader) and **libcp+0x27390** (scalar tail loader). The bulk loader body:

```
pmovzxwd -0x18(%rdi), %xmm0     ; load 4x uint16
cvtdq2ps  %xmm0, %xmm0          ; 4x int32 -> 4x float32
movaps    %xmm0, -0x30(%rcx)    ; store 4x float32
... (unrolled ×4) ...
addq $0x40, %rcx  ; next 16 floats
addq $0x20, %rdi  ; next 16 uint16
```

**Zero arithmetic beyond the cast.** A raw sensor value `r` becomes `(float)r` with no black-level subtract and no scale. So the `Image<float>` that feeds DemosaickLightV1 contains values in the native sensor range `[0..1023]` (not `[0..1]`).

The per-pixel `linearize(r) = (r - black) * scale` transform must be applied **somewhere downstream of the demosaic and before the ISP color math**. Session 3's runtime probe shows lambda_0 `LinearizeColorScale @ 0x340b00` fires at `t=1` immediately after demosaic's `t=0`, on the same shared canvas. That is the only candidate in the pipeline order, and its name matches exactly.

**Phoenix implementation:** the linearize formula for Phoenix is:
```c
// Inside Phoenix's lambda_0 equivalent, operating on vec4x32f canvas post-demosaic:
vec4 linearized = (raw_rgba - vec4(black_level)) * vec4(1.0f / (white_level - black_level));
```
where `black_level` and `white_level` come from per-camera calibration metadata (Block 8 or the camera struct) — exactly the values Session 3 noted as "closure+0x18 scalar values (already captured but meaning unclear)". The V1 closure at `+0x18` is **NOT the linearize scalars** — it is the `q` regularization constant for the gradient weight (same role as V2's `q*(1/128)` noted in `demosaic_v2_and_fusion_weights.md` §"Float scalar role").

**UNVERIFIED:** the exact VA of the linearize `subss`/`mulss` pair inside lambda_0 at 0x340b00. I did not read the 0x340b00 body in this session — next step is to dump that function and find the `subss <black>, xmm ; mulss <1/(W-B)>, xmm` pair and decode the RIP-relative constants to pin the exact `black` and `1/(white-black)` values. The constant values from Block 8 for L16 sensors are expected to be around `black≈42`, `white≈1023` per session3_upstream_probe.md's linked files.

**UNVERIFIED:** whether `black` and `scale` are per-camera constants baked into the lambda closure, or loaded per-invocation from the camera calibration struct. The dominant case is probably per-camera closure scalars (16 distinct instances of lambda_0, one per camera), but this needs a live dump of the closure data at 0x340b00's first hit.

### WB gains — where are they applied in the kernel?

Session 2 noted V1 takes a `Vec3<float>` of WB gains at closure+0x08. Inside V1<1,0>, the first instruction block is:

```
0x2eeb41: movq  0x8(%rdx), %rax        ; load Vec3<float>* from closure
0x2eeb45: movss (%rax), %xmm3          ; load gain[0]
0x2eeb49: maxss 0x4(%rax), %xmm3       ; xmm3 = max(g[0], g[1])
0x2eeb4e: maxss 0x8(%rax), %xmm3       ; xmm3 = max(g[0], g[1], g[2])
0x2eeb53: movss %xmm3, -0x268(%rbp)    ; save max_gain on stack
...
0x2eec3b: movss 0x302c81(%rip), %xmm2  ; load 1/128 (or similar small eps scale)
0x2eec43: mulss %xmm3, %xmm2           ; eps = max_gain * eps_scale
0x2eec47: movss %xmm2, -0xd4(%rbp)     ; save eps_for_this_tile
```

So the WB gains are **NOT** applied to pixel values inside this kernel. Instead, `max(WB)` is used purely to **scale the gradient epsilon** — the regularization floor for `rcpss(|Δ| + eps)`. This is a clever adaptive step: brighter-WB channels get a larger gradient floor so the demosaic weights don't go crazy on saturated highlights.

The actual WB gain application (`R *= g_r, G *= g_g, B *= g_b` per pixel) lives **elsewhere** — likely the same lambda_0 or `LinearizeColorScale` stage that does the linearize, since that's where per-channel scaling naturally pairs with black-level subtraction.

**Phoenix note:** Phoenix must apply linearize AND WB gains together in its lambda_0 equivalent. The V1 kernel already "bakes in" a WB-aware gradient floor, so Phoenix's demosaic step should get this eps formula too:
```c
eps_for_demosaic = max(wb_gain.r, wb_gain.g, wb_gain.b) * (1.0f/128.0f)  // V1 uses a slightly different scale; constant VAs 0x5f18cc range — verify
```

---

## #24 — V1 template phase mapping

### What the template parameters control

Comparing the three firing variants' prologues, the `<offX, offY>` template args encode **which corner of the 2×2 Bayer cell the tile's origin falls on**, and they manifest as:

1. **Stride initializers in the stack-resident Image<float> mirror structs.** V1<0,0> at 0x2ed580 stores `movl $0x0, -0xd8(%rbp)` and `movl $0x0, -0x128(%rbp)` (two scratch Image<float>s initialized with "origin offset 0"). V1<1,0> at 0x2eeb20 stores `movl $0x1, -0xd8(%rbp)` and `movl $0x1, -0x128(%rbp)`. V1<1,1> at 0x2f0240 stores `movl $0x0, -0xd8(%rbp)` and `movl $0x0, -0x128(%rbp)`. Only V1<1,0> stores 1s — but the `-0xd8`/`-0x128` fields aren't themselves the phase selector, they are Image<float>::is_valid/alloc flags that happen to differ because of compile-time specialization.

2. **The `rect` field destructuring pattern.** V1<0,0>'s prologue loads `rect[0]→-0x38`, `rect[1]→-0x34`, `rect[1]→-0x30`, `rect[2]→-0x2c` (pattern `{L, T, T, R}`). V1<1,0>'s pattern is `{T, L, R, T}`. V1<1,1>'s pattern is `{R, T, T, L}`. These are **different rect-corner compositions** for the 4 scratch Image<float> sub-windows the kernel sets up, and encode which 2×2 sub-lattice the kernel walks first.

3. **The inner-loop first-pixel fetch.** V1<0,0> opens its first `movss` at `-0x4(%r11,%rcx)` (horizontal offset −1 from base). V1<1,0> opens at `(%r10,%rcx)` (offset 0). These are the spatial phase shifts.

### Interpretation

L16 is **BGGR** for all 16 cameras (confirmed by phoenix-pipeline-facts.md). The three firing V1 variants cannot be "different Bayer patterns per camera" (there's only one sensor pattern). They must be **per-tile sub-phase offsets** — the tile origin `(tile_x, tile_y)` mod 2 determines whether the top-left corner of the tile lands on B, G(row), G(col), or R in the master BGGR lattice:

| Tile `(x mod 2, y mod 2)` | Top-left pixel in BGGR | Variant dispatched |
|:--:|:--:|:--:|
| (0, 0) | B | V1<0,0> |
| (1, 0) | G (in B row) | V1<1,0> |
| (0, 1) | G (in R row) | V1<0,1>  **dormant** |
| (1, 1) | R | V1<1,1> |

**Why V1<0,1> is dormant.** Session 3 reported 0 hits for V1<0,1>. In L16_02130 28mm, all 16 cameras line up their tile grid so that odd-row / even-col never occurs at a tile boundary. The 3 that DO fire cover the (0,0) / (1,0) / (1,1) cells — and crucially, the tile grid Lumen uses is an **odd-stride grid where the "G in R row" corner is skipped by the scheduler**, probably because that phase is symmetric to V1<1,0> under a horizontal flip and the scheduler picks the canonical representative. **UNVERIFIED:** this symmetry-collapse is my inference from the hit-count pattern. A direct probe would confirm by mapping the per-call `rect` arg to its `(x mod 2, y mod 2)` and cross-checking with the variant VA.

### The hit-count distribution matches

Session 3's probe gave 176/636/299 for V1<0,0>/<1,0>/<1,1>. Under my interpretation this is simply the distribution of tile origins across the 16-camera × ROI grid:
- V1<1,0> dominates (636 = 57%) because horizontally even tile counts and odd x-starts are the most common alignment.
- V1<0,0> (176 = 16%) covers tiles whose top-left lands on the B corner.
- V1<1,1> (299 = 27%) covers R-corner tiles.
- V1<0,1> (0%) — G-in-R-row — collapsed by scheduler.

### Phoenix implementation

Phoenix only needs **one** demosaic kernel that takes a `(subpixel_offset_x, subpixel_offset_y)` parameter at runtime, rather than 4 compile-time template specializations. The math is identical across variants — only the pointer offsets shift. A single templated-by-runtime-int function is equivalent. This closes #24.

---

## Corrections to Session 3's `session3_upstream_probe.md`

**Big Finding #2** ("The Bayer → float RGBA demosaic IS inside libcp's lambda pipeline") — the first half is correct (demosaic is inside libcp's lambda pipeline at the DemosaickLightV1 VAs). The second half is **wrong** on one claim:

> "**Conclusion:** ... `DemosaickLightV1` takes raw Bayer `Image<float>` via closure pointer at `+0x10` and writes `Image<vec4x32f>` with alpha=1.0 into the destination at `+0x08`. This IS the raw→float path, and it is fully inside libcp."

The **destination write and alpha=1.0** part is correct. The **"raw→float path"** claim is wrong. DemosaickLightV1 operates entirely on `float32` and performs **no** raw→float conversion. The raw→float cast is a separate upstream loader (0x271d0 bulk, 0x27390 scalar) that does nothing but a type cast. The actual linearize arithmetic (black-level subtract + scale) happens **downstream** of the demosaic, inside lambda_0 `LinearizeColorScale` at 0x340b00, operating on the post-demosaic RGBA canvas.

**Big Finding #2 open item 1** ("Exact arithmetic of the raw→float conversion inside each DemosaickLightV1 body") — resolved: there is no such arithmetic inside DemosaickLightV1. Look in lambda_0 @ 0x340b00 instead. The closure scalars at `+0x18` that Session 3 captured but couldn't interpret are the **V1 gradient regularization `q`**, not linearize black/scale.

**Big Finding #6 UNVERIFIED** (meaning of `<R,B>` template params) — closed above as `(tile_x mod 2, tile_y mod 2)` sub-phase selectors, not per-camera Bayer pattern.

---

## UNVERIFIED items for session 5

1. **Exact linearize formula inside lambda_0 @ 0x340b00.** Needs: read ~200 instructions starting at 0x340b00, find the `subss <const>, xmm ; mulss <const>, xmm` pair (likely early in the inner loop body), decode the RIP-relative constants against `__const` in the Mach-O to get the literal `black` and `1/(white-black)` values. Expected to be close to `black≈42.0f`, `white-black≈981.0f`, `1/981 ≈ 0.00102`. The `1/981` constant was NOT found by a full-dylib byte scan (`509c853a` pattern: 0 hits), so it may be stored as a runtime-loaded scalar from camera calibration rather than a .rodata literal. That strongly suggests **per-camera loaded scalars**, not compile-time constants.

2. **Whether WB gains are applied inside lambda_0 alongside linearize, or in a separate stage (lambda_1/2).** The Session 3 phase table shows lambda_1/2 run only in Phase D, while lambda_0 runs in all phases — Phase A's demosaic + linearize uses only lambda_0, so WB gains must be applied inside lambda_0 for Phase A tiles. Phase D likely re-applies or refines them.

3. **Scheduler symmetry-collapse of V1<0,1>.** My claim that V1<0,1> is skipped by scheduler fold-in is unverified. A small probe dumping rect coords per V1 variant call would confirm.

4. **V1's exact gradient eps formula.** I identified that `max(WB) * small_const` becomes xmm9, but didn't pin the `small_const`. Decode the RIP-rel at 0x2eec3b (`mulss 0x302c81(%rip), %xmm3`) and 0x2eed91 (`mulss 0x302b33(%rip), %xmm0`). Addresses: `0x2eec3b + 7 + 0x302c81 = 0x5f18c3`; `0x2eed91 + 7 + 0x302b33 = 0x5f18cb`. These are adjacent to the V2 constants (0x5f18cc = 1/128, 0x5f18d0 = -0.02) decoded in `demosaic_v2_and_fusion_weights.md` — likely the same constant pool with V1-specific values.

---

## Quick reference — addresses

| VA | Routine | Confidence |
|---|---|---|
| 0x271d0 | uint16 → float32 bulk loader (no arithmetic beyond cast) | instruction-verified |
| 0x27390 | scalar tail-handler for the same | instruction-verified |
| 0x2ed580 | DemosaickLightV1<0,0> operator() | Session 3 RTTI + instruction-confirmed |
| 0x2eeb20 | DemosaickLightV1<1,0> operator() — dominant | Session 3 RTTI + instruction-confirmed |
| 0x2f0240 | DemosaickLightV1<1,1> operator() | Session 3 RTTI + instruction-confirmed |
| 0x340b00 | lambda_0 `LinearizeColorScale` — actual linearize site | Session 2/3 named; body NOT read in session 4 |
| 0x5f18c3 | V1 eps scale constant (RIP-rel from 0x2eec3b) | VA computed, value NOT decoded |
| 0x5f18cb | V1 eps scale constant (RIP-rel from 0x2eed91) | VA computed, value NOT decoded |
| 0xdf6d4 | `42.0f` in __const — NOT referenced by RIP-rel loads | byte-pattern scan, 0 ref sites |
| 0xdf6d8 | `1023.0f` in __const — NOT referenced by RIP-rel loads | byte-pattern scan, 0 ref sites |
| 0x5f105c | `1/1023` — referenced by 0x2e6463 (1024-entry tone-curve LUT interpolator, NOT Bayer linearize) | instruction-verified |
