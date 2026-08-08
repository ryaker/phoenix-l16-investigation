# Exact 64-Phase Four-Tap Resample Formula

**Date:** 2026-07-03  
**Status:** Admitted evidence for `CLM-RESAMPLE-001`  
**Scope:** SHA-pinned installed `libcp.dylib`; complete runtime table capture
on canonical Unit-1 `28mm`; previously admitted weighted-store and boundary
mechanics on Unit-1 `28/35/70/150mm`

## Result

`libcp+0x36f800` constructs a `64 x 4` Catmull-Rom cubic-convolution
coefficient table. For phase `p in [0,63]`, let `t=p/64`. The four
coefficients apply to source indices
`floor(x)-1, floor(x), floor(x)+1, floor(x)+2` and are:

```text
[K(1+t), K(t), K(1-t), K(2-t)]

K(d) = ( 9*d^3 - 15*d^2 +  6) / 6,  0 <= d < 1
K(d) = (-3*d^3 + 15*d^2 - 24*d + 12) / 6, 1 <= d < 2
K(d) = 0,                                      d >= 2
```

This is the interpolating Catmull-Rom kernel, including its expected negative
outer lobes. Each scalar is replicated to four float32 SIMD lanes. The
instruction-ordered complete `4096`-byte table has SHA-256:

```text
a5e2489fcfbf711cfec05d3ae2b165f970aec02d8d72a2c7c61bdb43ac174b9f
```

Representative phases are:

| Phase | Four scalar coefficients |
|---:|---|
| `0` | `(0, 1, 0, 0)` |
| `32` | `(-0.0625, 0.5625, 0.5625, -0.0625)` |
| `63` | `(-0.0001201629638671875, 0.008295059204101562, 0.9993953704833984, -0.0075702667236328125)` |

The existing worker proof supplies the separable application:

```text
fixed = trunc(input_double * 65536.0)
integer = fixed >> 16
phase = (fixed >> 10) & 63
indices = clamp(integer + [-1,0,1,2], source bounds)
output = sum(source[index[k]] * table[phase][k], k=0..3)
```

`0x372760` performs the horizontal row-cache pass and `0x372210` applies the
same four weights vertically to four cached rows. Existing four-focal runtime
packets reconstruct both stores.

## Installed Static Proof

Installed binary:

```text
/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
SHA-256 b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The loop at `0x36f890..0x36fa9d` runs exactly 64 times. It converts the loop
index to float32, multiplies by exact `1/64`, evaluates the four distances,
and writes four replicated `vec4` coefficients at 64-byte phase stride.
Its installed constants are:

```text
1/64, 1, 2, 9, -15, 6, 1/6, -3, 15, -0.375, -12, 0.375, -36
```

Algebraically, the inner and outer instruction sequences reduce to the two
pieces above. The verifier preserves each `mulss`/`addss` float32 rounding
step and the compiler's phase-index forms of the outer linear term, so its
table is a bit-level reconstruction rather than a double-precision
reevaluation of the displayed polynomial.

## Runtime Equality

The reusable owner-route probe now captures the complete table at the accepted
`0x36fb1f` setup stop:

- byte count `4096`;
- `64 x 4 x vec4` shape;
- all four lanes equal in every vector; and
- runtime bytes exactly equal the independently generated static table.

The accepted runtime packet is:

```text
runs/owner_f0_resample_36f800/owner_f0_resample_28mm.json
```

Raw run outputs remain ignored and rerunnable. No `/tmp` artifact is a proof
dependency.

## Offset And Scale Semantics

The selected-cache caller `0x3d0650` gives operational names and formulas to
the two pairs passed to `0x36f800`. For selected source-level dimensions
`(Sw,Sh)`, requested dimensions `(Dw,Dh)`, and requested ROI
`(x0,y0,x1,y1)`:

```text
sx = float32(Sw) / float32(Dw)
sy = float32(Sh) / float32(Dh)

tx0 = max(0, floor(float32(x0*sx - 2)))
ty0 = max(0, floor(float32(y0*sy - 2)))
tx1 = min(Sw, ceil(float32(x1*sx + 2)))
ty1 = min(Sh, ceil(float32(y1*sy + 2)))

offset = (
  float32(x0*sx) - float32(tx0),
  float32(y0*sy) - float32(ty0)
)
scale = (sx, sy)
```

The temporary source descriptor is read over `(tx0,ty0,tx1,ty1)`. The
float32 offset and scale components are promoted to double before
`0x36f800`, which converts them to signed 16.16 by truncation. Thus they mean
the source-space origin inside the expanded temporary ROI and source pixels
per destination pixel. They are derived runtime values, not missing public
protobuf fields.

## Reproduction

Reusable tooling:

- `tools/lldb_probes/resample_64_phase/verify_resample_64_phase.py`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_36f800_probe.py`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_28mm.lldb`

```bash
arch -x86_64 lldb -s \
  tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_28mm.lldb \
  tools/lri_process

python3 tools/lldb_probes/resample_64_phase/verify_resample_64_phase.py \
  --runtime-json runs/owner_f0_resample_36f800/owner_f0_resample_28mm.json \
  --report runs/resample_64_phase/static_runtime_verification.json
```

Expected verifier status: `PASS`.

## Scope And Admission

The table generator and worker bodies are installed static code with no
camera, focal, firmware-record, or LRI-dependent coefficients. One complete
runtime table capture is therefore sufficient to join static reconstruction
to execution. Existing worker/store evidence supplies canonical Unit-1
four-focal coverage, including live boundary-clamp segments at `28mm` and
`70mm`.

This closes the exact four-tap resampler basis, quantization, indexing,
clamping, separable stores, and the selected-cache offset/scale derivation. It
does not close the separate distortion table, contributor-selection policy,
or final output encoding.

The earlier quarantine text saying Catmull-Rom was contradicted by negative
outer lobes is refuted: negative outer lobes are a defining feature of this
Catmull-Rom kernel.
