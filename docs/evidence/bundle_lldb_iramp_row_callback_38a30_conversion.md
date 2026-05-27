# Bundle + LLDB IRAMP Row Callback `0x38a30` Conversion Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the row callback reached from the caller-side `0x3e5720`
executor setup after IRAMP return, square-copy, and vector-scale handoffs.

It proves:

- callback auxiliary first qword `0x38a30` is the row callback reached by the
  canonical four-zoom bridge HDR quartet
- for the observed `512`-wide rows, `0x38a30` copies the first three lanes of
  each source 16-byte `vec4` into a contiguous float-triple buffer
- `0x38a30` calls `0xbfef0` with `ecx = 0` and a count of `3 * width` channels
- the used `0xbfef0` branch converts those float channels into 16-bit binary16
  bit patterns and writes three 16-bit words per input `vec4`
- first captured callback rows at `28mm`, `35mm`, `70mm`, and `150mm` all
  produce destination words matching the installed-bundle conversion formula

It does not prove public pixel-format names, final file output, final display
semantics, or final merge acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_row_callback_38a30_conversion/row_callback_conversion_probe.py`
- `tools/lldb_probes/iramp_row_callback_38a30_conversion/row_callback_28mm.lldb`
- `tools/lldb_probes/iramp_row_callback_38a30_conversion/row_callback_35mm.lldb`
- `tools/lldb_probes/iramp_row_callback_38a30_conversion/row_callback_70mm.lldb`
- `tools/lldb_probes/iramp_row_callback_38a30_conversion/row_callback_150mm.lldb`

Process output-path placeholders go under ignored
`runs/iramp_row_callback_38a30_conversion/`; the probe stops at the callback
return before render completion.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The previous executor proof showed worker `0x3e58c0` calls the row callback
through callback auxiliary first qword `0x38a30`. At the callback entry,
arguments are:

```text
rdi = destination row pointer, 6 bytes per pixel
rsi = source row pointer, 16-byte vec4 per pixel
edx = source descriptor width
```

For the canonical quartet, runtime setup had already proven source and
destination descriptors are `512x512`, stride `512`. In the `512`-wide case,
`0x38a30` skips its 1024-pixel large-block path, copies source lanes 0, 1, and
2 into a contiguous stack buffer, and calls `0xbfef0` with a channel count of
`3 * width`:

```asm
0x38b44  movl  %r12d, %r10d
0x38b52  andl  $-0x20, %r10d
...
0x38b90  movq  -0x8(%rdi), %rax   ; source lanes 0..1
0x38b94  movl  (%rdi), %edx       ; source lane 2
0x38b96  movq  %rax, -0x8(%rsi)
0x38b9a  movl  %edx, (%rsi)
...
0x38c1f  leal  (%r12,%r12,2), %edx
0x38c23  leaq  0x40(%rsp), %rsi
0x38c28  xorl  %ecx, %ecx
0x38c2a  callq 0xbfef0
```

The used `0xbfef0` branch is the `cl == 0` branch at `0xc00b3`, because
`0x38a30` passes `ecx = 0`. For the observed `512`-pixel rows,
`edx = 1536`, which is divisible by `32`; the vector body covers the row and
the scalar tail is not used on the captured path.

The relevant constants are:

| VA | Word | Meaning in used branch |
|---|---:|---|
| `0x5a81f0` | `0x7fffffff` | absolute-value bit mask |
| `0x5ab7a0` | `0x38800000` | binary16 normal/subnormal boundary, `2^-14` |
| `0x5ab7b0` | `0x4b800000` | subnormal scale, `2^24` |
| `0x5ab7c0` | `0x477fe000` | binary16 max finite magnitude, `65504.0` |
| `0x5ab7d0` | `0xc8000000` | normal-path exponent/mantissa adjustment before `>> 13` |

The static converter formula for each source float channel is:

```text
bits = float32_bits(value)
sign = (bits & 0x80000000) >> 16
abs_bits = bits & 0x7fffffff

if abs_bits < 0x38800000:
    magnitude = trunc(abs(value) * 2^24)
else:
    magnitude = ((min(abs_bits, 0x477fe000) + 0xc8000000) mod 2^32) >> 13

output_word = sign | magnitude
```

That is a float32-channel to 16-bit binary16 bit-pattern conversion for this
path. This is an internal representation fact only; it is not a public file
format or final-render semantics claim.

## Runtime Proof

The LLDB probes stop at `0x38c39`, immediately after `0x38a30` returns from
`0xbfef0` and before it tears down the stack frame. Runtime addresses are
normalized to installed-bundle VAs:

- callback return site: `0x38c39`
- caller return site after indirect callback call: `0x3e5918`
- saved 1024-pixel block count: `0`
- remaining width in `r12d`: `512`

The first captured row is a scheduler-dependent callback row, not necessarily
image row zero. Values below are first-hit samples that prove live conversion
math, not stable image constants.

| Zoom | First source channels | Destination first 3 words | Predicted words | Match |
|---|---|---|---|---|
| `28mm` | `(0.288162202, 0.498504847, 0.299227715)` | `0x349c, 0x37f9, 0x34c9` | `0x349c, 0x37f9, 0x34c9` | yes |
| `35mm` | `(0.007351109, 0.014337762, 0.009477693)` | `0x1f87, 0x2357, 0x20da` | `0x1f87, 0x2357, 0x20da` | yes |
| `70mm` | `(0.057570606, 0.107754953, 0.062299024)` | `0x2b5e, 0x2ee5, 0x2bf9` | `0x2b5e, 0x2ee5, 0x2bf9` | yes |
| `150mm` | `(0.308382928, 0.620296955, 0.430475771)` | `0x34ef, 0x38f6, 0x36e3` | `0x34ef, 0x38f6, 0x36e3` | yes |

Raw probe packets also recorded the first 12 destination bytes after
conversion:

| Zoom | First 12 destination bytes |
|---|---|
| `28mm` | `9c 34 f9 37 c9 34 97 34 f1 37 c3 34` |
| `35mm` | `87 1f 57 23 da 20 2b 1f fe 22 9f 20` |
| `70mm` | `5e 2b e5 2e f9 2b 1d 2c dd 2f 71 2c` |
| `150mm` | `ef 34 f6 38 e3 36 fc 34 03 39 f4 36` |

The first six bytes in each row are the three 16-bit words in little-endian
order for the first captured source `vec4`'s first three lanes.

## Limits

This proof closes the previously open row-callback conversion math for the
observed `0x3e5720 -> 0x38a30 -> 0xbfef0` path on the canonical four-zoom
bridge HDR quartet.

It does not close:

- public names for the three channels
- whether later code treats the 6-byte rows as final pixels, intermediate HDR,
  or another internal image representation
- complete downstream policy after this conversion
- candidate acceptance / rejection or contributor suppression logic
