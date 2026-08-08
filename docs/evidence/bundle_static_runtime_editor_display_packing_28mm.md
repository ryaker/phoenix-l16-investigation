# Static/Runtime Evidence: Lumen Editor Display Route And Packing

**Date:** 2026-07-16  
**Status:** VERIFIED, scoped `CLM-COMPAT-001` addendum  
**Runtime scope:** canonical Unit-1 `28mm`, profile 3, RenderType `1`,
five-level coarse-to-fine pyramid construction  
**Static scope:** installed Lumen/libcp display-format policy; body- and
focal-independent

## Question

What image layout does the installed editor expose after initial profile-3
construction, which cache and per-level pipeline produce its four-float
display pixels, and how does Lumen convert those floats into GUI bytes?

This bundle tests rather than assumes editor/export identity. It proves the
two float images are not identical and byte-isolates their complete tested
difference to one in-place per-level Color-pipeline call. A follow-up bundle
formula-closes the selected ACRE core inside that call.

## Installed Custody

```text
Lumen executable SHA-256:
1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d

libcp.dylib SHA-256:
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier checks instruction bytes and public symbol binding directly in
these installed files.

## Correct Output-Record Route

The live editor update is not queue record type `4`. The level-4 write-watch
packet captures its parent record as:

```text
type      13
priority  2
```

Installed body `0x3bf820` writes those exact values and inserts the record at
`0x3bf8bc -> 0x3bfc40`. RTTI names its callable:

```text
lt::RendererPrivate::requestRenderROI(...)::$_12
```

with effective signature
`void(shared_ptr<Image<vec4x32f>> const&, int, Rectangle<int> const&)`.

Type `4` is a separate public serialization request. Exported
`CIAPI::Renderer::serialize` at `0x3903c0` is the sole direct caller of
`0x3b6ca0`; that producer stores type `4` and inserts it through
`0x3b6d6e -> 0x3bfc40`. The probe harness does not call `serialize`.

## Display-Float Producer

The record's float image is produced before `requestRenderROI::$_12` queues
it. At the stable final-byte watchpoint, `RendererPrivate+0x8a0` contains a
function object whose loaded address point rebases to `0x65ea88`. Installed
RTTI names it:

```text
lt::RendererPrivate::RendererPrivate(CIAPI::RendererProfile)::$_2
```

with effective signature
`void(Image<vec4x32f>&, int, Rectangle<int> const&)`. Its invoke slot is
`0x65ea88+0x30 = 0x3bb2b0`.

For the captured default level-4 request:

```text
RendererPrivate+0x774 rendering mode       0
RendererPrivate+0x888 depth-ready state    0
request scale from RendererPrivate+0x48    15.217391014099121f
DOF threshold from DOFCache+0x98           15.217391014099121f
```

Mode-0 body `0x3bb524` compares those floats. Equality takes its `jae` arm at
`0x3bb55d`, selecting `RendererPrivate+0x688`. Installed callable RTTI names
the two 512x512 cache records unambiguously:

| RendererPrivate field | Installed identity | Relevant callable |
|---:|---|---:|
| `+0x688` | `lt::PipelineCache` constructor callback receiving `Tile<Vec3<Float16>>` | `0x65f5e0`, sink slot `+0x30 = 0x3ec960` |
| `+0x6b8` | `lt::DOFCache` constructor callback receiving `Tile<Vec3<Float16>>` | `0x65f870`, render slot `+0x30 = 0x3f0b90` |

The live level-4 mode-0 request therefore selects `PipelineCache`, not
`DOFCache`. After `0x3d0650` reads the selected cache, `0x3bb822` indexes the
five-entry per-level vector at `RendererPrivate+0x870` and `0x3bb867` calls
`0x31b110`. A before/after capture of that exact in-place call proves:

```text
before 0x31b110 SHA-256  10b6b96a1caf6f45fa394af50a6d531ba72754272b99c5fdc235597b6461f694
HDR-writer input SHA-256  10b6b96a1caf6f45fa394af50a6d531ba72754272b99c5fdc235597b6461f694

after 0x31b110 SHA-256   f8acda7264f7b7e458bbbe6acd69fe38ea172771fa938b65f0cffb5ebf1bc860
editor float SHA-256     f8acda7264f7b7e458bbbe6acd69fe38ea172771fa938b65f0cffb5ebf1bc860
```

Both descriptors are `652x489`, stride `652`, four float32 lanes, and have
identical alpha `1.0`. Thus the exact editor/export difference for this tested
request is the in-place `0x31b110 -> 0x33fb30` Color pipeline, not the cache
read, resampler, queue, or byte packer.

A gate on this exact call records seven callbacks in this exact vector order.
Installed RTTI names them independently:

| Index | Target | Installed identity |
|---:|---:|---|
| 3 | `0x340f70` | default Color-payload color/AWB scaling callback |
| 10 | `0x347680` | `Pipeline::setColorCorrection(... ColorCorrection)::$_62` |
| 11 | `0x341040` | default Color-payload Lab-L sharpen callback |
| 12 | `0x346110` | `Pipeline::setLensShading(... LensShading)::$_56` |
| 13 | `0x3496e0` | `Pipeline::setToneAdjust(... ToneAdjust)::$_68` |
| 14 | `0x349e80` | `Pipeline::setContrastAdjust(... ContrastAdjust)::$_69` |
| 15 | `0x34ad50` | `Pipeline::setToneMapping(... ToneMapping)::$_71` |

The earlier admitted source-payload callback order does not substitute for
this display-configured sequence. Full-image hashes after every callback show
that lens shading and contrast adjustment are exact no-ops on this tested
request, despite their live callback records. Sharpen and tone-adjust/clarity
reuse already admitted formulas. The follow-up ACRE bundle formula-closes the
selected tone mapper's core operation; exact display index-10 color correction,
the tone mapper's following `0xaebd0` color conversion, and alternate-route
parameters remain open.

This closes the formerly unnamed immediate display-float route and proves the
editor/export images differ exactly across the named in-place Color pipeline
for the tested default request. It does not yet formula-close every callback
in that display-configured sequence.

## Public GUI Format Policy

Installed Lumen helper `TuneRendererOnLoad` at `Lumen+0x20010` compares the
GUI OpenGL input format against `0x80e1` (`GL_BGRA`) and calls the exported
public method:

```text
CIAPI::RendererBase::setProperty(CIAPI::ParamInt, int)
```

with numeric `ParamInt` key `10` and value:

```text
1  when GUI format == GL_BGRA
0  otherwise
```

The installed application selects between `GL_BGRA` (`0x80e1`) and
`GL_RGBA` (`0x1908`) according to GPU fail-safe/extension policy. The normal
BGRA-capable route uses `GL_BGRA`; fail-safe or unsupported-BGRA operation
uses `GL_RGBA`. `ImagePlanes::ImagePlane::uploadUpdate` passes that selected
format and `GL_UNSIGNED_BYTE` (`0x1401`) to `glTexSubImage2D`.

This gives the property an operational public meaning even though no installed
string names enum member `ParamInt(10)`.

## Exact Packing Branches

Renderer worker `libcp+0x3bca90` reads key `10` at `0x3bda06`. Both branches
use the exact float32 vector at `libcp+0x5a8890`:

```text
[255.0f, 255.0f, 255.0f, 255.0f]
```

For source display pixel `p = [R,G,B,A]`, each lane is multiplied by `255`,
converted with SSE `cvtps2dq` under the current MXCSR rounding mode, then
passed through signed-16 and unsigned-8 saturation.

The two destination layouts are:

```text
ParamInt(10) == 0 / GL_RGBA fallback:
  out = sat_u8(round_nearest_even(255 * [R,G,B,A]))
  helper body libcp+0x27e0d0

ParamInt(10) == 1 / GL_BGRA normal route:
  out = sat_u8(round_nearest_even(255 * [B,G,R,A]))
  inline body libcp+0x3bdb30
```

The BGRA branch's `shufps $0xc6` is exactly lane order `[2,1,0,3]`. There is
no premultiplication in either packing body. Alpha is packed as supplied.

## Runtime Custody

The probe-only local renderer exposes an allocated pyramid pixel immediately
before rendering. A hardware write watchpoint on that pixel identifies the
first real writer without assuming a conversion address.

At level `4`, coordinate `(326,244)`, the clean-exit runtime packet records:

```text
writer                 libcp+0x27e1c7 (stop PC 0x27e1cd)
source float32          [0.433192640542984,
                         0.5748528242111206,
                         0.6556504368782043,
                         1.0]
scale float32           [255.0, 255.0, 255.0, 255.0]
MXCSR                   8096 (round-control bits 00: nearest/even)
packed bytes            6e 93 a7 ff
process exit            0
```

The independent replay is exact:

```text
round([0.43319264,0.57485282,0.65565044,1] * 255)
  = [110,147,167,255]
  = 6e 93 a7 ff
```

The local harness did not call installed `TuneRendererOnLoad`, so this packet
exercises the key-`10 = 0` RGBA fallback body. It must not be mislabeled as
the installed GUI's normal BGRA byte order. Installed static proof closes the
conditional BGRA branch.

## Pyramid Layout

The same completed `28mm` run exposes five packed four-byte levels:

| Level | Width | Height | Row bytes |
|---:|---:|---:|---:|
| 0 | 10432 | 7824 | 41728 |
| 1 | 5216 | 3912 | 20864 |
| 2 | 2608 | 1956 | 10432 |
| 3 | 1304 | 978 | 5216 |
| 4 | 652 | 489 | 2608 |

The same clean-exit run retains the complete pre-pack float image and packed
output:

```text
float32 RGBA SHA-256  f8acda7264f7b7e458bbbe6acd69fe38ea172771fa938b65f0cffb5ebf1bc860
packed RGBA8 SHA-256  6e647328940c4a436760b2462677e89439211ebb101ab2bbbe7f0da8d023bcf1
```

An independent float32 replay matches every one of the `1,275,312` packed
bytes. All `318,828` source alpha lanes are exactly `1.0f` and all destination
alpha bytes are `255`. Source RGB remains finite but reaches about
`[1.310,1.376,1.403]`; saturation therefore occurs at this final byte pack,
not by clamping the retained float image first. The observed `393` output
callbacks are a run count, not an algorithm constant.

## Reusable Proof

```bash
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_display_policy.py
```

The verifier checks:

- both installed-file SHA-256 values;
- exact `255.0f` constants and both packing instruction sequences;
- the public `RendererBase::setProperty(ParamInt,int)` binding;
- `GL_BGRA` / `GL_RGBA` selection and `GL_UNSIGNED_BYTE` upload constants;
- the clean-exit level-4 write-watch packet and bit-exact replay;
- type-13/priority-2 runtime custody and installed producer identity;
- separation from public type-4 `Renderer::serialize`;
- exact `RendererPrivate::$_2 -> 0x3bb2b0` producer identity;
- installed `PipelineCache` / `DOFCache` RTTI and the observed mode-0
  level-4 `PipelineCache` selection;
- the five-entry `RendererPrivate+0x870` per-level pipeline vector and
  `0x31b110` handoff;
- byte-exact export-input/before-call and editor-float/after-call equality; and
- the exact seven-callback display sequence with installed RTTI names; and
- pyramid geometry, both level-4 digests, complete-image byte replay, and
  exact source/destination alpha.

Reusable LLDB files are in
`tools/lldb_probes/editor_render_type_topology/`. The `/private/tmp` binary in
the watch scripts is only a Rosetta/debugserver launch workaround; all
durable scripts, reports, and summarized evidence are repo-owned.

## Admission Boundary

Admit under partial/reference-only `CLM-COMPAT-001`:

- exact profile-3 editor output-pyramid geometry for tested Unit-1 `28mm`;
- the tested default level-4 route through `PipelineCache`, the per-level
  Color pipeline, type-13 queue record, and final packer;
- exact installed float-to-byte rounding, saturation, and lane policy;
- conditional normal `GL_BGRA` and fallback `GL_RGBA` GUI upload policy;
- runtime writer custody and all-opaque level-4 alpha for the tested run.

Do not infer:

- a formula-complete mapping from the linear-ProPhoto HDR pixels to editor
  display pixels until the remaining display-specific callbacks are closed;
- `DOFCache` inactivity for other levels, modes, depth states, controls, or
  inputs;
- the active GPU branch on every host;
- identical pyramid dimensions after crop/orientation or at every input;
- complete edit-control formulas or profiles `1/2` behavior.
