# Lane A5 addendum — post-merge per-pixel 3×3 matrix (`0x36acf0`) is RUNTIME-populated

**Status:** `NEEDS_CODEX_VALIDATION`. Structural finding (deterministic section mapping); the matrix
*values* require a runtime read (deferred). Binary `libcp.dylib` sha256 `b38dc4b3…`.

## What it is (OBSERVED)

At the tail of IRAMP func `0x3661b0`, after the weighted-add (Lane A7) and the guided detail-transfer,
a per-pixel **3×3 matrix multiply** is applied to the result buffer (`-0x4270`), preserving lane 3:
```
0x36ad08 movaps (%rcx),%xmm4            ; pixel (R,G,B,A)
0x36ad0e shufps $0  -> R; mulps %xmm0   ; R * col0
0x36ad18 shufps $0x55 -> G; mulps %xmm1 ; G * col1 ; addps
0x36ad22 shufps $0xaa -> B; mulps %xmm2 ; B * col2 ; addps
0x36ad2c blendps $0x8,%xmm3,%xmm4       ; keep lane 3 (alpha) from xmm3
0x36ad32 movaps %xmm4,(%rcx)            ; out.rgb = M·in.rgb, alpha preserved
```
The 3 columns (`xmm0/xmm1/xmm2`) are assembled from 9 coefficients loaded rip-relative from
`0x671980..0x6719a0`.

## Key result: the coefficients are in `__bss` (runtime-populated), NOT file constants

Mach-O section map (otool -l): `__DATA __bss` addr `0x66d170`, size `0x6f80` (→ `0x6740f0`),
**`fileoff = 0`**. All six load targets `0x671980/0x671988/0x67198c/0x671994/0x671998/0x6719a0` fall
inside `__bss`. `__bss` is zero-initialized on load and **written at runtime**. Therefore:

- The 3×3 matrix is **not a fixed embedded Light constant** — it is **computed/populated per render**,
  almost certainly the **color-correction / white-balance matrix derived from the LRI** (calibration
  block / AWB gains).
- A static decode of the matrix is impossible (the bytes are not in the file); it requires a runtime
  read (lldb breakpoint at `0x36ad08` reading `xmm0/xmm1/xmm2`, or reading `0x671980..` after pipeline
  init).

## Clean-room implication (GOOD)

Because the matrix is LRI-derived runtime data (not an embedded constant like the tone-curve LUTs), it is
**clean-room-friendly**: Phoenix parses the color matrix from the LRI at render time (Rule #0 source
class 1), no libcp bytes shipped. Contrast with the tone-curve LUTs at `0x5e31b0..` which ARE embedded
constants and are a known clean-room blocker.

## Non-claims / open
- Matrix VALUES not decoded (runtime; deferred). Whether it is exactly camera-RGB→XYZ, a CCM, or a WB
  diagonal-plus-correction is unknown until read at runtime.
- The exact `__bss` writer (which init path populates `0x671980..`) is not traced here.
- Method correction: an earlier static read of `0x671980..` produced garbage precisely because `__bss`
  has `fileoff=0` (file offset ≠ VA there) — recorded to prevent repeating the mistake.
