# Exact Final Radiance RGBE Writer Formula

**Date:** 2026-07-03  
**Status:** Admitted partial evidence for `CLM-OUTPUT-002`  
**Scope:** Installed writer body; Unit-1 `28mm` float-to-byte runtime replay;
existing same-render writer custody on Unit-1 `28/35/70/150mm` plus Unit-2
exact `28mm`

## Result

The canonical CLI HDR route dispatches the final `10432 x 7824` linear
ProPhoto `vec4x32f` descriptor to writer body `libcp+0x902b0`. The writer
ignores lane 3 and converts RGB float32 to four-byte Radiance RGBE.

For a finite pixel `(r,g,b)` with `m=max(r,g,b)>0`:

```text
(fraction, exponent) = frexp(m)
scale = float32(float32(fraction * 256) / m)

R = trunc(clamp(float32(r * scale), 0, 255))
G = trunc(clamp(float32(g * scale), 0, 255))
B = trunc(clamp(float32(b * scale), 0, 255))
E = exponent + 128
```

Bytes are stored in `R,G,B,E` order. Negative channels are clamped to zero.
The installed body reconstructs the `frexp` fraction/exponent through IEEE-754
bit operations and has explicit zero/subnormal/nonfinite handling; canonical
captured values take the finite normal path above.

The output file is:

```text
#?RADIANCE
FORMAT=32-bit_rle_rgbe

-Y 7824 +X 10432
<10432 * 7824 flat RGBE pixels>
```

`-Y +X` is top-to-bottom row order and left-to-right column order. Despite the
conventional `FORMAT=32-bit_rle_rgbe` declaration, this writer emits the
legacy flat form: no `2,2,width_hi,width_lo` scanline marker and no channel
RLE. File size is exactly header plus `width*height*4`.

## Static Proof

Installed binary SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

At `0x9042b`, the writer obtains one source float32 RGB row. The vector loop
`0x904a0..0x90666` and scalar tail `0x90690..0x9075e`:

- load three channels;
- compute their maximum;
- derive a shared exponent and scaling fraction;
- multiply each channel;
- clamp to `[0,255]`;
- truncate to integer;
- pack RGB in low bytes and exponent in the high byte.

At `0x90772`, row width is multiplied by four and the packed row is passed
directly to the output stream. The loop then advances to the next source row.

## Runtime Replay

A focused stop at `0x90764` captured:

- final row index `0`;
- row width `10432`;
- the first 128 source RGB float32 triplets; and
- the corresponding 512 packed RGBE bytes.

The independent verifier reproduces every packed byte. Captured packed-row
prefix SHA-256:

```text
1103f7d5686cba739540780be6bb7b6dffda8352bf8158d1a793c31c262aa972
```

The first pixel demonstrates the exact truncation policy:

```text
input  = (0.1697998046875, 0.2939453125, 0.1768798828125)
output = (86, 150, 90, 127)
```

## Complete File Check

The complete Unit-1 `28mm` repeat used by the verifier has SHA-256:

```text
fe0401ad4a6e6fa971b064e2320d3d88ace1452529936d4d9b88a3e2a47ff1d1
```

It has the exact header, dimensions, orientation, and flat-body size above.
The host `file` utility identifies it as `Radiance HDR image data`; macOS
ImageIO through `sips` reports width `10432`, height `7824`, and format
`pic`. This establishes a concrete modern host photo framework that reads the
artifact.

Existing writer-custody evidence proves the same `0x902b0` route on the
canonical Unit-1 four-focal quartet and one Unit-2 exact-`28mm` discriminator.
The encoding body is input-data independent, so a duplicate byte replay at
every focal is not needed.

## Reproduction

- `tools/lldb_probes/output_rgbe_writer/output_rgbe_writer_probe.py`
- `tools/lldb_probes/output_rgbe_writer/unit1_28mm.lldb`
- `tools/lldb_probes/output_rgbe_writer/run_probe.sh`
- `tools/lldb_probes/output_rgbe_writer/verify_output_rgbe_writer.py`

Raw captures are under `runs/output_rgbe_writer/`.

## Remaining Output Gap

This closes the exact tested writer encoding and proves that its artifact is
readable. It does not close the parent output claim:

- the header does not contain Radiance `PRIMARIES` metadata;
- it does not embed an ICC profile;
- therefore the file does not self-identify the already proved linear
  ProPhoto primaries/white point; and
- alternate final image placement, if any is live for supported inputs, still
  requires exclusion or custody.

An independent app may use this exact readable RGBE encoding, but correct
self-describing color requires either explicit Radiance primaries or a
properly tagged modern container. Choosing that container belongs to the
later specification; the investigation still must establish that no
additional live final-image surface changes the pixels or placement.
