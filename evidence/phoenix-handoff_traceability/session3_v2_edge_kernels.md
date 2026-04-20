# Session 3 — DemosaickLightV2 Edge-Kernel Consumer of `scalar × -0.02`

## TL;DR
**Only VA `0x2f1840` reads the float at buffer offset +0x44.** VA `0x2f1c00` also reads
`0x44(%rdi)` but as an **integer** (`movl`, index arithmetic) — it is a row-coordinate /
row-fetch helper, not a math consumer. `0x2f1840` is called **once per output tile**;
`0x2f1c00` is the helper it calls 6× (rows y-2..y+2) to fetch neighbor rows.

## VA 0x2f1840 — Structure (disasm lines 725222–725467)

- Frame: `subq $0x58, %rsp`, 6 callee-saved regs.
- `%r13 = halide_buffer_t*` (the descriptor whose +0x44 holds the -0.02×scalar).
- Calls `0x2f1c00` six times with `%esi = y-2 … y+2` and the per-row dst (`y+0`). Each
  call returns a `float*` row pointer → stored at `[-0x38]`, `[-0x40]`, `%r14`, `[-0x48]`,
  `%rax`.
- The scalar at `0x44(%r13)` is broadcast once per iteration:
  ```
  2f195a: movss  0x44(%r13), %xmm10
  2f1960: shufps $0, %xmm10, %xmm10       ; xmm10 = {s,s,s,s}
  ```
- Constants:
  - `xmm11 = 0x2b681d(%rip)` → **abs-value mask** (0x7fffffff×4) — used for `|Δ|`.
  - `xmm9  = 0x2b78c5(%rip)` → a 4-lane float constant — the HA center weight (≈ 0.5).
  - `xmm10 = broadcast(scalar × -0.02)` → **floor clamp** applied via `maxps`.

## The Inner SIMD Loop (the hot path)

Per-lane (4 pixels/iteration), with `c = current row center pixel (xmm12 = row[x])`,
neighbors `W,E,N,S` from adjacent row pointers:

```
Hgrad = 2*c - W - E         (xmm6)
Vgrad = 2*c - N - S         (xmm7)

Hscore = |Hgrad| + |E - W|  (xmm3)   ; classic Hamilton-Adams H classifier
Vscore = |Vgrad| + |S - N|  (xmm0)

Hcand = max(Hgrad * k, floor) + (W + E)      ; k = xmm9 (~0.5), floor = xmm10 (s*-0.02)
Vcand = max(Vgrad * k, floor) + (N + S)

if (Hscore < Vscore) out = Hcand else out = Vcand
out *= k                                     ; final /2
; optional: blendvps with raw center using parity mask xmm8  (green/non-green bayer)
```

This is **Hamilton–Adams "adaptive color plane interpolation"** green-channel
reconstruction, with one Phoenix customization: the interpolated correction term is
**floor-clamped by `scalar × -0.02`** via `maxps %xmm10, %xmm6/7`. Because the scalar
is negative, the clamp lets the correction go as negative as `-0.02*scalar` but no
further — preventing the H/A correction from producing "dark halos" when gradients are
extreme (classic HA artifact).

The scalar tail loop (`2f1af0..2f1ba5`) performs the same math per-pixel with `maxss`
instead of `maxps` — identical semantics. It also reads `0x44(%r13)` into `xmm4`
(line 725407).

## Algorithm Interpretation

`0x2f1840` is `DemosaickLightV2_green_interp`: Hamilton-Adams green at red/blue sites
with a **negative-floor clamp on the Laplacian correction term**. The `-0.02 × scalar`
value is a "correction magnitude floor" — a scene-adaptive limiter that prevents HA from
over-shooting into negative green values in saturated highlights. It is NOT a typical
edge weight or gradient threshold — it is a **clamp on the output of the Laplacian
correction**, keeping V2 numerically stable vs V1 at the cost of slight loss of
micro-contrast. This matches the earlier observation that V2 is "softer but cleaner".

## Phoenix Python Pseudocode

```python
def demosaic_v2_green_ha(bayer, y, x, scalar, k=0.5):
    """
    Hamilton-Adams green interpolation at a red/blue site (y,x).
    scalar: the halide_buffer_t +0x44 value, previously computed as
            (some per-tile stat) * -0.02  (already negative).
    """
    c = bayer[y,   x  ]
    W = bayer[y,   x-1]; E = bayer[y,   x+1]
    N = bayer[y-1, x  ]; S = bayer[y+1, x  ]
    NN= bayer[y,   x-2]; SS= bayer[y,   x+2]   # for |E-W|, |S-N| extended if needed
    WW= bayer[y-2, x  ]; EE= bayer[y+2, x  ]

    Hgrad = 2.0*c - W - E
    Vgrad = 2.0*c - N - S

    Hscore = abs(Hgrad) + abs(E - W)
    Vscore = abs(Vgrad) + abs(S - N)

    # *** Phoenix-specific floor clamp on the correction magnitude ***
    floor = scalar           # already = raw_scalar * -0.02, negative
    Hcorr = max(Hgrad * k, floor)
    Vcorr = max(Vgrad * k, floor)

    Hcand = Hcorr + (W + E)
    Vcand = Vcorr + (N + S)

    g = Hcand if Hscore < Vscore else Vcand
    return g * k             # final /2
```

The per-parity `blendvps %xmm8, xmm12, xmm6` at `2f1a7f` selects **raw center** for
green sites (leaves G-at-G pixels untouched) and the interpolated value for R/B sites —
standard Bayer parity-aware write.

## Pending / Uncertain

- Exact value of `xmm9` (center weight k) — strongly inferred as 0.5 from HA structure
  and from the final `mulps xmm9, xmm6` acting as a /2. Confirm by dumping the
  constant at VA `0x5a92a0` (= `0x2f19db + 0x2b78c5`).
- Whether `xmm11` is truly the abs-mask `0x7fffffff×4` — inferred from its use pattern
  (`andps` immediately before subtract-then-compare). Confirm at VA `0x5a81f0`
  (= `0x2f19d3 + 0x2b681d`).
- The `xmm8` parity vector `{-1,0,-1,0}` or `{0,-1,0,-1}` depending on `r9 & 1` — this
  is the even/odd-column Bayer mask. Verified by construction at 2f1936–2f1943.
