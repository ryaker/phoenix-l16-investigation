# Lane A5 addendum — resampler APPLY structure (Q16.16, separable 4-tap) — machine-anchored

**Status:** byte/instruction anchors are deterministic (OBSERVED); recursive control-flow framing is LEAD.
`NEEDS_CODEX_VALIDATION` for the framing. Binary `libcp.dylib` sha256 `b38dc4b3…`, VA == file offset.

Completes the resampler spec begun in `kernel_identity.md` (the kernels) — this is HOW the LUT is applied.

## Machine-verified facts (OBSERVED — byte-read or quoted instruction)

- **Coordinates are Q16.16 fixed-point.** The scale constant at `0x5abed8` is the IEEE-754 double
  `65536.0` (= 2^16), byte-verified. Source coords are computed as doubles then `cvttsd2si` to Q16.16
  ints (`0x2b3208` etc.).
- **64-phase sub-pixel index.** `phase = (coord_q >> 10) & 0x3f` →
  `0x2b3398 shrl $0xa,%ebx` ; `0x2b339b andl $0x3f,%ebx`. (Bits 10..15 = top 6 bits of the 16-bit
  fraction.) The integer source index is `coord_q >> 16`.
- **LUT indexing.** `phase << 6` (`shlq $0x6` = ×0x40) selects the phase row; the 4 taps are at
  `+0x00/+0x10/+0x20/+0x30` (16-byte broadcast each) — matches the 4096-byte (64 phases × 4 taps × 16 B)
  LUT from `kernel_identity.md`.
- **4-tap separable accumulate** (per output pixel), `0x2b3410..0x2b3435`:
  ```
  0x2b3410 movaps (%rax),%xmm0 ; 0x2b3413 mulps (%r8),%xmm0    ; row0 * LUT[phase][0]
  0x2b3417 movaps (%rcx),%xmm1 ; 0x2b341a mulps (%r9),%xmm1    ; row1 * LUT[phase][1]
  0x2b341e addps %xmm0,%xmm1
  0x2b3421 movaps (%rsi),%xmm0 ; 0x2b3424 mulps (%r10),%xmm0   ; row2 * LUT[phase][2]
  0x2b3428 addps %xmm1,%xmm0
  0x2b342b movaps (%rdi),%xmm1 ; 0x2b342e mulps (%r11),%xmm1   ; row3 * LUT[phase][3]
  0x2b3432 addps %xmm0,%xmm1
  0x2b3435 movaps %xmm1,(%rdx)                                 ; store 4-channel output pixel
  ```
  Inner loop = output-row width (`decl %ebx; 0x2b344e jne 0x2b3410`); 4 channels per pixel (16 B).
- **4 vertical taps selected** by a `cmpq $0x4`/`jne 0x2b32c0` loop (`0x2b3387/0x2b338b`) into row
  pointers `-0x50(%rbp,%r12,8)`.
- **Second (orthogonal) phase extraction** in the column-fetch helper `0x2b3710`:
  `0x2b37a6 shrl $0xa,%r13d` ; `0x2b37aa andl $0x3f,%r13d` ; `0x2b37cc movaps (%r11,%r13),%xmm3` —
  same 64-phase scheme on the other axis. Corroborates **separable per-axis 4-tap** (not a 2D 16-tap).
- **Destination addressing** (`0x2b33e8..0x2b3400`): `dst = view.base[ stride*y + x0 ]`, `stride` at
  `view+0x18` (pixels), `base` at `view+0x20`, pixel = 16 B.
- **Leaf dispatch:** vtable `0x6685b8` slot `+0x30 = 0x2b3180` (byte-verified) → thunk → `0x2b31c0`
  operator(). `0x5440` unit-cell test `0x54cd cmpl $0x1,%eax`, leaf call `0x5506 callq *0x30(%rax)`.

## Clean-room reproduction (verified shape)

For each output pixel (x,y), per axis:
1. `coord_q = round((offset + i*scale) * 65536)` (Q16.16); `srcIdx = coord_q >> 16`;
   `phase = (coord_q >> 10) & 0x3f`.
2. Gather 4 taps `src[srcIdx-1 .. srcIdx+2]` (clamped), each a 4-channel float vector.
3. `out = Σ_{t=0..3} src[tap_t] * LUT[phase][t]` (`mulps`/`addps`), LUT = the B-spline or Catmull-Rom
   table from `kernel_identity.md`.
4. Store 4 floats to `dst.base[stride*y + x]`.
Applied separably (one 4-tap pass per axis; both axes use the same 64-phase quantization).

## LEAD / non-claims
- `0x5440` as a recursive subdivision driver and `0x2d30` as the recursion/task re-entry are LEAD
  (`0x2d30` not extracted). The leaf APPLY math above does not depend on the driver framing.
- "Whole resampler is V-then-H separable in two passes" is LEAD; what is OBSERVED is a 4-tap accumulate
  + a second per-axis phase extraction. The exact two-pass wiring (one `0x5440` call with transposed
  step vs two) was not extracted — next step: the `0x2b2be0` tail / `0x5440` caller.
- Static only; no runtime confirmation of which output buffer is written.
