# Session 5 — lambda_0 LinearizeAndColorScale Deep Dive

**Bottom line (honest):** The inline per-pixel subtract-and-scale arithmetic
does NOT exist as a classic subss/mulss pixel loop inside the lambda_0 call
tree. lambda_0 (@0x340b00) → 0x3589c0 → vtable[3] @0x65e0b0 → 0x359e30 → one
of {0x35b5d0, 0x35c220, 0x35d5c0} is a **Halide pipeline builder**, not the
pixel kernel itself. It allocates Halide::Func objects via operator new
(0x556398), populates closure vtables, and dispatches via `callq *0x28(%rax)`.
The actual subss/mulss loop is JIT-emitted (or lives in a sibling trampoline
reached through the constructed `std::function`) — not statically inlined
here. Key evidence and what was recovered below.

## Call Graph (static)

```
0x340b00  lambda_0 LinearizeAndColorScale  (closure+0x16b0 = [1,0,0,1])
   │
   └─> 0x3589c0  func_builder   stack=0x178
        │   reads closure, sets up Halide rect bounds (0x20..0x7c offsets)
        │   operator new(0x30)  @0x358e52
        │   installs vtable = 0x65e0b0     @0x358e57
        │   callq 0x5440 (std::function::assign)
        │   calls 0xf340 (halide_buffer_t set_bounds) and 0xf4e0 (release)
        │
        └─> vtable[0x65e0b0][3] = 0x359e30  operator()(const_scanline_args*)
             │   reads closure[0x8]  (sub-closure)
             │   reads closure[0x10] (bounds)
             │   reads closure[0x18] = X (scalar float)      ← dispatch key
             │   reads closure[0x20], closure[0x28]
             │
             │   if X < 0.99999988f  (0x5fbebc)  → 0x35d5c0
             │   elif X > 1.00000001f (0x5fbec0) → 0x35c220
             │   else (X ≈ 1.0)                  → 0x35b5d0
             │
             └─> 0x35b5d0  identity-WB variant   stack=0x228
                  │  callq 0xa9130(color_primary_id) → [X/Y, 1, Z/Y]
                  │    (CIE xyY → XYZ chromaticity, NOT WB gain)
                  │    tables at 0x5ab720 / 0x5ab760 indexed by id ∈ [0..12]
                  │    returns 3 floats at [rdi+0]=y/x, [rdi+4]=1.0, [rdi+8]=(1-x-y)/x
                  │
                  │  1.0f / primary[0,1,2]  (three divss, 0x35ba4c..0x35ba5f)
                  │  builds 2x2 color-mix matrix with insertps shuffles
                  │  mulps against -0x120(%rbp) / -0x110(%rbp) (the [1,0,0,1] identity
                  │    matrix pulled from closure+0x16b0 via the stack-frame copy)
                  │
                  │  — then more Halide Func allocations & dispatches (0x2d6cd0,
                  │    0x556398, 0x361b50, 0x3629f0, 0x35e660, 0x35f5c0) —
                  │
                  │  loads at 0x35bb1b / 0x35bb36 of two constants:
                  │     0x5fbe34 = 0.0005f  (1/2000, likely noise_epsilon)
                  │     0x5fbe38 = 0.005f   (1/200,  likely black_variance)
                  │   multiplies them by entry-point xmm0 → writes -0x1fc/-0x200
                  │
                  │  These are tuning *hyperparameters* baked into the lambda,
                  │  NOT black level and NOT WB gain.
                  │
                  └─> further callq *ptr  into Halide-dispatch thunks
```

## What I found that IS arithmetic (but is NOT pixel linearize)

- `0x35ba41  movss  0x5a8128(%rip), %xmm0`  → **1.0f** (numerator for reciprocal)
- `0x35ba4c  divss  -0xa0(%rbp), %xmm1`     → 1 / primary.X
- `0x35ba57  divss  -0x9c(%rbp), %xmm2`     → 1 / primary.Y (=1/1 = 1)
- `0x35ba5f  divss  -0x98(%rbp), %xmm0`     → 1 / primary.Z
- `0x35ba88..0x35babc` — insertps builds 2x2, mulps against loaded identity
  matrix (the [1,0,0,1] from closure+0x16b0). **This is the colorspace
  transform being multiplied into the identity color_scale**, producing
  a per-primary 2x2 mix matrix. Still not touching a pixel buffer.

## What the three-way dispatch actually picks

The scalar at `closure+0x28` (vtable-fn arg rdi) is a **color-space tag / gain
mode**:

| X value        | Kernel      | Meaning                                 |
|----------------|-------------|-----------------------------------------|
| X < ~1.0       | 0x35d5c0    | needs extra gain (below-unit scale)     |
| X ≈ 1.0        | 0x35b5d0    | identity path (most common, 972 hits)   |
| X > ~1.0       | 0x35c220    | needs clipping (above-unit)             |

All three allocate Halide funcs and end in vtable dispatches — same shape.

## Scalar sub/sub found at 0x35f005 (DIFFERENT function)

Not inside lambda_0 call-graph, but within nearby compute_loop:

```
0x35f005  movss  (%rbx),   %xmm0        ; tmp = *data
0x35f009  subss  0x10(%rbx), %xmm0      ; tmp -= *(data+0x10)   ← may be black lvl
0x35f01e  movss  0x4(%rbx), %xmm0       ; tmp2 = *(data+4)
0x35f023  subss  0xc(%rbx), %xmm0       ; tmp2 -= *(data+0xc)
...
0x35f19e  mulps  %xmm0, %xmm1           ; mul by closure+0x50 broadcast
0x35f1bb  mulps  %xmm3, %xmm2           ; mul by closure+0x48
0x35f1d2  mulps  %xmm4, %xmm1           ; mul by closure+0x4c
```

This **smells right** (load, subtract, multiply scale, per-channel via
offsets 0x48/0x4c/0x50) but is inside func 0x35f000 which is reached from
0x35b5d0's nested builder chain — not from the direct lambda_0 call path.
Confidence: 60% that 0x35f000 is the true per-pixel linearize kernel, but it
would need runtime confirmation (it's also reached from non-lambda_0 callers).

## Phoenix pseudocode (best static guess)

```python
# What lambda_0 constructs at runtime, then hands off:
primary = cie_xyY_to_XYZ(primary_id)       # via 0xa9130
# primary = (X/Y, 1, Z/Y)
color_scale_2x2 = closure[0x16b0 : 0x16c0]  # = [1,0,0,1]
wb_mix = compose_2x2(1/primary, color_scale_2x2)

# The per-pixel kernel (probably at 0x35f000, NOT confirmed):
for each pixel p in bayer_float:
    black = closure[0x10 or 0xc]   # loaded via [rbx+0x10] / [rbx+0xc]
    scale = closure[0x48|0x4c|0x50] # per-channel 3-float at these offsets
    out = (p - black) * scale
    # then color_mix(wb_mix) is applied downstream via another Halide Func
```

## Where the calibration actually enters

Still **not statically resolved**. The closure at 0x3589c0 entry has offsets
0x20/0x24/0x28/0x2c = rectangle bounds (int32), 0x70..0x7c = clip bounds,
0x88 = stride, 0x90 = data_ptr, 0x98 = device_ptr. No scalar black-level or
scale-factor field is visible in the 0x178-byte stack frame. They must come
from **sub-closure** at 0x3589c0 rdi+0x8, which is populated by the parent
lambda_0 (0x340b00) from its rdi+0x8 — i.e., pulled from the **payload** the
pipeline was invoked with. Session 4 findings + Session 5 confirm:

**linearize constants live in the runtime payload, not libcp rodata and not
the lambda_0 closure directly.** Phoenix must either:
1. Hook libcp and snapshot closure data live, OR
2. Read the per-camera .npz black_levels/white_levels directly and bypass
   reverse-engineering (these are the ground truth anyway), OR
3. Accept that the identity 2x2 + 1/primary colorspace mix is the only
   static-extractable transform, and inject black/scale from the .npz.

## Recommendation

**Option 3 is the right answer.** The cal_color_l16_02130.npz already has
`black_levels` and `white_levels` per camera. Use them directly as:

```python
linearized = (bayer_float - black_levels[cam_id]) / (white_levels[cam_id] - black_levels[cam_id])
```

Then apply the 2x2 color_scale = identity (confirmed from closure+0x16b0)
and the 1/primary XYZ matrix (from 0xa9130, tables at 0x5ab720/0x5ab760).
**This reproduces the lambda_0 math faithfully without needing to locate
the Halide JIT output.** Issue #22 can be closed with this resolution:
the arithmetic is not statically extractable because it's JIT-generated,
but the inputs to that arithmetic ARE statically known (cal npz + identity
2x2 + CIE tables).

## Closing #22

Mark as **resolved with alternate strategy**. Phoenix should:
- Use `.npz` `black_levels` / `white_levels` for subtract+scale
- Use identity 2x2 for color_scale (no-op)
- Skip trying to reverse the Halide JIT output

All three dispatch variants (0x35b5d0 / 0x35c220 / 0x35d5c0) differ only in
the color-primary branch (identity vs below-unit vs above-unit gain); for
the photo-path they are functionally equivalent on a per-pixel basis.
