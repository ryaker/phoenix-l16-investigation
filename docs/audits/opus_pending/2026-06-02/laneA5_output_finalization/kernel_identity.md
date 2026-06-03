# Lane A5 addendum — IRAMP resampler kernel identity (BYTE-VERIFIED)

**Status:** `NEEDS_CODEX_VALIDATION` for the call-graph framing; the **kernel coefficients and family
identification are deterministic (byte-verified rodata + exact canonical match), not LLM-asserted.**
Binary `libcp.dylib` sha256 `b38dc4b3…`, VA == file offset.

## Result

The two IRAMP output resamplers (`0x2b2be0` and byte-sibling `0x36f800`, called from the `0x3661b0`
finalization tail — see this packet's `observations.md`) each build a **separable 4-tap cubic-convolution
kernel sampled at 64 sub-pixel phases** (LUT = 64 phases × 4 taps × 16-byte broadcast = 4096 B). They are
**two different members of the cubic family**:

| Resampler | Kernel | Mitchell (B,C) | inner `|x|<1` form | byte-verified |
|---|---|---|---|---|
| `0x2b2be0` | **cubic B-spline** | B=1, C=0 | `(3|x|³ − 6|x|² + 4)/6` | yes |
| `0x36f800` | **Catmull-Rom** | B=0, C=0.5 | `(9|x|³ − 15|x|² + 6)/6 = (3/2)|x|³ − (5/2)|x|² + 1` | yes |

Outer segment `1≤|x|<2`: B-spline `(−|x|³ + 6|x|² − 12|x| + 8)/6`; Catmull-Rom `a=−0.5` cubic-convolution
outer lobe. Both reconstructions reproduce the canonical weights to ≤3e-8 (single-precision rounding)
across all 64 phases, with per-phase weight sum = 1.0.

## Byte-verified coefficients (read directly from rodata; VA == file offset)

Verification: `python3 -c "import struct; print(struct.unpack('<f', open(DYLIB,'rb').read()[VA:VA+4])[0])"`

`0x2b2be0` (B-spline) inner: `0x5a9b04=3.0`, `0x5d7fe8=-6.0`, `0x5a8870=4.0`, `0x5aae60=0.16666667` (1/6).
`0x36f800` (Catmull-Rom) inner: `0x5aae80=9.0`, `0x5d9a0c=-15.0`, `0x5aae70=6.0`, `0x5aae60=1/6`.
Shared generics: `0x5abed4=0.015625` (1/64 = phase step), `0x5a8128=1.0`, `0x5a887c=2.0` (segment bound).

All constants are rodata `movss` rip-relative loads (none are immediates). The phase index `i` (0..63) is
the only register-computed input (`cvtsi2ss %ecx`, scaled by 1/64).

## Why this matters (parity)

Clean-room Phoenix must reimplement these resamplers exactly. Per the distribution model (no libcp at
runtime), the LUT bytes cannot be shipped — but these are **standard published kernels** (cubic B-spline;
Catmull-Rom / cubic-convolution a=−0.5), reimplementable from formula. This packet supplies the exact
formula + parameters, byte-verified.

## Non-claims

- The mapping of WHICH resampler runs for WHICH zoom tier / IRAMP stage is NOT established here (the
  "IRAMP output resampler" caller framing is from Lane A5's finalization trace, `NEEDS_CODEX_VALIDATION`).
- LUT consumption order (separable H-then-V vs other) and the `0x5440` leaf gather were not traced here.
- No runtime confirmation (static + byte decode only).
