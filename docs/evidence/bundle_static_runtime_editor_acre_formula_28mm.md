# Static/Runtime Evidence: Editor ACRE Tone Formula And LUT

**Date:** 2026-07-16  
**Status:** VERIFIED, scoped `CLM-COMPAT-001` addendum  
**Runtime scope:** canonical Unit-1 `28mm`, profile 3, RenderType `1`, default
level-4 mode-0 display request  
**Static scope:** SHA-pinned installed `libcp.dylib`; formula and table are
body/focal independent, while their observed selection and parameters are
only the runtime scope above

## Question

What exact pixel operation does the final active editor callback at display
pipeline index `15` perform?

The preceding display-route bundle proved that this callback is the complete
last stage between the pre-tone image and the retained editor float image, but
did not decode its implementation.

## Installed Identity And Custody

The live `Pipeline+0x1668` object has callable address point `0x659b30`.
Installed RTTI names it exactly:

```text
lt::TMO_ACRE
```

Its process slot `+0x10` is `0x2d7780`. That method builds callback address
point `0x659b78`; RTTI names the callback
`lt::TMO_ACR::process(...) const::$_0`, and its worker slot `+0x30` is
`0x2d7a30`. The class-name difference is retained literally rather than
normalized.

The wrapper, process entry, and first worker entry agree exactly:

```text
source descriptor       == destination descriptor
image shape              652x489, stride 652, vec4 float32
TMO object               identical at all three boundaries
ColorSpace packet        identical at all three boundaries
first worker rectangle   [0,0,256,256]
process exit             0
```

## Runtime Parameters

The live 24-byte TMO object is:

```text
+0x00 vtable address point   libcp+0x659b30
+0x08 EV offset float32      1.0001065731048584 (word 0x3f80037e)
+0x10 LUT pointer            libcp+0x5e41b4
```

The worker computes:

```text
exposure_scale = exp2f(EV offset) = 2.000147819519043f
```

The table is exactly 1025 contiguous float32 values:

```text
table VA       libcp+0x5e41b4
byte count     4100
SHA-256        0d5997a0708dec35863113bb4516dd056ed927dd75609e8c3a2c935953107de1
first values   0, 0.00079000002, 0.00164000003, 0.00255999994, ...
last values    ..., 0.9986500144, 0.9990800023, 0.9995099902, 1
```

The worker reads both `LUT[index]` and `LUT[index+1]`, so 1025 values, not
1024, are part of the implementation contract.

## Exact Core Formula

For input RGB component `c`, first compute float32 `x = c * exposure_scale`.
The installed piecewise shaper is:

```text
if x <= 0.002500000176951289:
    s = 0
else if x < 0.007500000298023224:
    s = 100.50251007080078 * (x - 0.002500000176951289)^2
else:
    s = 1.0050251483917236 * (x - 0.005000000353902578)
```

All operations are float32 in the installed instruction order. Then:

```text
u = 1024.0f * s
i = clamp(trunc_to_int(u), 0, 1023)
y = LUT[i] + (u - float(i)) * (LUT[i+1] - LUT[i])
```

The index is clamped, but `u` itself is not. Values above the nominal range
therefore extrapolate from the last table segment rather than clamping to
`LUT[1024]`.

After computing independent `yR/yG/yB`, the worker ranks the three shaped
components. It preserves the LUT outputs at the minimum and maximum channels.
For the middle channel it uses:

```text
y_mid = y_min
      + (s_mid - s_min) * (y_max - y_min)
      * rcp_ss(s_max - s_min)
```

where `rcp_ss` is the SSE reciprocal approximation used by the installed
body. Equal triples retain their direct LUT values. Alpha is copied bit for
bit from the source pixel.

## Independent Replay

A reusable C implementation contains no call into Lumen or `libcp`. It reads
the pre-tone stage image and the extracted table, applies only the formula
above, and reproduces the first installed pre-color-conversion tile:

```text
installed intermediate SHA-256  ccb4b056be2b806f467c856d2dcb194673c99be1cbadc2dcae2d16c1b777380b
clean-room replay SHA-256        ccb4b056be2b806f467c856d2dcb194673c99be1cbadc2dcae2d16c1b777380b
compared bytes                   1,048,576
first pixel                      [1.0295236111,1.0404888391,0.9868522882,1]
```

The comparison covers all 65,536 pixels in the `256x256` worker rectangle,
not a fitted sample set.

## Following Color Conversion

The callback treats the ACRE result as fixed linear-ProPhoto/D50 and converts
it to the live display output packet. That packet contains the standard
sRGB/D65 RGB-to-XYZ matrix, D65 white
`(0.31272661685943604, 0.3290231227874756)`, and selector `2`; installed public
property schema names selector `2` `srgb`.

Runtime callback custody at generic worker `0xbf4a0` proves selector tuple
`(5,2)` chooses exact worker `0xabf20`. It receives the fixed
linear-ProPhoto/D50 packet first, the live sRGB/D65 packet second, and this
exact D50-to-D65 adaptation matrix, row-major float32:

```text
[ 0.9555767775, -0.0230393261, 0.0631636381]
[-0.0282894168,  1.0099415779, 0.0210076459]
[ 0.0122981742, -0.0204830393, 1.3299101591]
```

The selected worker takes matrix branch `0xac600`. Its runtime-composed rows
are:

```text
[ 2.0340766907, -0.2288134694, -0.0085697845, 0]
[-0.7273342609,  1.2317303419, -0.1532866359, 0]
[-0.3067418933, -0.0029169153,  1.1618567705, 0]
```

For each ACRE RGB vector, the worker multiplies by those rows in captured SSE
order, clamps each result to at least zero, and applies the sRGB forward
transfer:

```text
if q < 0.0031308000907301903:
    out = 12.920000076293945 * q
else:
    out = 1.0549999475479126 * fast_pow(q, 0.4166666567325592)
        - 0.054999999701976776
```

`fast_pow` is the installed float32 mantissa/exponent log2-exp2 approximation,
including its exact polynomial constants and integer exponent reconstruction;
the clean-room C replay follows those instructions directly. Alpha is copied
from the matrix input after the transfer.

The independent converter replay matches the complete installed post-convert
tile:

```text
installed SHA-256   da68813263016b0b3cd82bf202db74d5b58b209bf30cb1d5583260e892d36cbb
replay SHA-256      da68813263016b0b3cd82bf202db74d5b58b209bf30cb1d5583260e892d36cbb
compared bytes      1,048,576
first pixel         [1.0150306225,1.0187051296,0.9906099439,1]
```

This first-tile result is also the corresponding region of the independently
captured final editor-stage image. Thus the selected complete index-15
operation, including its following display color conversion, is formula- and
byte-closed at the stated runtime scope.

## Reproduction

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/editor_render_type_topology/acre_runtime_28mm.lldb
bash tools/lldb_probes/editor_render_type_topology/run_acre_replay.sh
bash tools/lldb_probes/editor_render_type_topology/run_acre_converter_replay.sh
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_display_policy.py
```

Reusable files are under
`tools/lldb_probes/editor_render_type_topology/`. Runtime reports and raw
replay inputs remain in ignored `runs/editor_render_type_topology/`; the
verifier pins every admitted digest and installed body/table range.

## Admission Boundary

Safe admission under reference-only `CLM-COMPAT-001`:

- the selected default display tone object is exact `lt::TMO_ACRE`;
- its complete core exposure/shaper/LUT/hue/alpha formula is clean-room
  replayed byte for byte over one full `256x256` worker tile;
- the exact 1025-value table, live EV offset, linear-ProPhoto/D50 source,
  sRGB/D65 output, adaptation/composed matrices, selected `0xabf20 -> 0xac600`
  converter formula, and both full-tile replays are fixed at the stated scope.

Do not generalize the observed EV or selected table to other edits, inputs,
levels, bodies, focal tiers, profiles, or low-light state. Exact public origin
of the EV, a direct public-name join for the selected LUT, display index-10
color-correction math, and alternate DOF/mode behavior remained open at this
checkpoint. The subsequent
`bundle_static_runtime_editor_acre_public_origins_28mm.md` closes the selected
EV/LUT origins without broadening this runtime scope.
