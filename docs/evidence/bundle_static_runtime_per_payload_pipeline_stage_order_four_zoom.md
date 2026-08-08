# Static + Runtime Evidence: Per-Payload Pipeline Stage Order

## Question

What is the exact installed order of correction, denoise, sharpen, and tone
callbacks beneath the visible `src1` source-image producer path?

This closes callback/dependency order. It does not claim that lazy descriptor
callbacks evaluate every output pixel eagerly at callback time, or promote
this source-preparation order into a total order for every later output stage.

## Artifacts

- [verify_pipeline_stage_order.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/verify_pipeline_stage_order.py)
- [src1_virtual_target_census_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_target_census_probe.py)
- [lldb_src1_virtual_target_census_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_virtual_target_census_four_zoom.md)
- `runs/src1_virtual_target_census/src1_virtual_census_{28,35,70,150}mm.json`

Installed `libcp.dylib` SHA-256:
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## Fixed Order Table

The installed `Pipeline` constructor owns sixteen `0x40`-byte callback
records. It allocates a sixteen-pointer vector and copies records in this
exact order:

| Vector index | Record offset |
|---:|---:|
| 0 | `0x000` |
| 1 | `0x040` |
| 2 | `0x200` |
| 3 | `0x080` |
| 4 | `0x100` |
| 5 | `0x140` |
| 6 | `0x180` |
| 7 | `0x0c0` |
| 8 | `0x1c0` |
| 9 | `0x240` |
| 10 | `0x280` |
| 11 | `0x2c0` |
| 12 | `0x300` |
| 13 | `0x340` |
| 14 | `0x380` |
| 15 | `0x3c0` |

Each payload loop walks this vector in ascending index. A populated record's
callable is at `record+0x20`; `0x33f180`, `0x33f480`, and `0x33fb30` invoke
it through vtable slot `+0x30` for Bayer, BayerFloat, and Color respectively.

SHA-pinned setup instructions place public setter callables into the record
offsets above. Installed RTTI independently names `setHotPixelRemoval`,
`setHighlightRestore`, `setCrossTalkCorrection`, `setDemosaicking`,
`setColorNoiseReduction`, `setAdaptiveDesaturation`, `setDenoising`,
`setLensShading`, and `setToneMapping`. The constructor's second default
callback is the proven sharpen wrapper
`0x340b00/0x340cc0/0x341040 -> 0x3589c0`.

The three `Pipeline::setToneAdjust(... ToneAdjust)::$_68` RTTI families are
installed at record offset `base+0x340`, exactly vector index `13`, for all
three payload types. Their operators
`0x3491e0/0x349460/0x3496e0` call shared `0x2e6d50`, which calls the admitted
Laplacian-clarity construction through `0x2e40f0 -> 0x2e4cf0`. Clarity is a
separate tone-adjust callback at index 13, not part of index-11 Lab-L sharpen.

## Exact Active Orders

### Bayer: all four canonical focals

| Index | Target | Stage |
|---:|---:|---|
| 1 | `0x341770` | hot-pixel removal |
| 2 | `0x343e10` | highlight restore |
| 3 | `0x340a30 -> 0x350ff0` | default Bayer normalization/materialization |
| 5 | `0x342280` | cross-talk correction |
| 6 | `0x342c60` | demosaic |
| 7 | `0x34b3b0` | color-noise reduction |
| 8 | `0x343620` | adaptive desaturation |
| 9 | `0x345a10` | denoise |
| 11 | `0x340b00 -> 0x3589c0` | Lab-L sharpen |
| 12 | `0x345d50` | lens shading |
| 13 | `0x3491e0 -> 0x2e6d50` | tone adjust / Laplacian clarity |
| 15 | `0x34a610` | `setToneMapping`; conditional linear-ProPhoto materialization (classified by the follow-up bundle) |

### BayerFloat

Unit-1 `28mm` and `35mm`:

`default normalization/materialization (3) -> cross talk (5) -> demosaic (6)
-> Lab-L sharpen (11) -> lens shading (12) -> Laplacian clarity (13) -> tone
mapping (15)`.

Unit-1 `70mm` and `150mm`:

`default normalization/materialization (3) -> cross talk (5) -> demosaic (6)
-> CNR (7) -> adaptive desaturation (8) -> denoise (9) -> Lab-L sharpen (11)
-> lens shading (12) -> Laplacian clarity (13) -> conditional linear-ProPhoto materialization (15)`.

### Color

Unit-1 `28mm` and `35mm`:

`AWB/color scaling (3) -> CNR (7) -> adaptive desaturation (8) -> denoise (9)
-> Lab-L sharpen (11) -> Laplacian clarity (13) -> conditional linear-ProPhoto materialization (15)`.

Index 3 is `0x340f70 -> 0x3510f0`, whose reciprocal-AWB origin and
color-scale behavior are independently admitted by `CLM-AWB-001`. Unit-1
`70mm` and `150mm` gated complete runs record zero Color-loop hits.

## Runtime Join

The verifier checks every retained target tuple against its installed vtable
slot and requires these exact active target sets:

| Payload | 28mm | 35mm | 70mm | 150mm |
|---|---:|---:|---:|---:|
| Bayer | 11 | 11 | 11 | 11 |
| BayerFloat | 6 | 6 | 9 | 9 |
| Color | 6 | 6 | 0 hits | 0 hits |

All four processes exited `0`, with one accepted visible-src1 gate, no probe
error, and no drive-step cap. Each nonzero virtual site reached the probe's
`512` cap, so counts are lower bounds. The exact target set is the observed
bounded-window set joined to the fixed installed ordering table.

The separate retained Unit-1 `28mm` clarity report exits `0`, enters
`0x2e4cf0` 67 times, invokes clarity callbacks 590 times at levels `0..4`,
and matches the default seven-float public-property packet. The static
ToneAdjust call graph joins that runtime-active body to stage index 13. It
does not claim that all three payload variants are separately runtime-live in
that report.

## Consequence

For live wide Color payloads, CNR, adaptive desaturation, denoise, and Lab-L
sharpen are ordered source-payload transformations after public AWB/color
scaling; Laplacian clarity is the later index-13 tone-adjust callback before
tone mapping. These are not an unordered collection that may all be moved
after IRAMP without a separate equivalence proof. Tele BayerFloat similarly
adds CNR/adaptive/denoise before sharpen; wide BayerFloat does not activate
that trio in the observed gated window.

These callbacks update lazy image descriptors. This establishes callback and
descriptor-dependency order, not wall-clock order for later tile evaluation.

## Scope And Non-Claims

- Installed-static order is body/focal independent for the pinned dylib.
- Runtime liveness is Unit-1 `28/35/70/150mm` under first-visible-`src1`
  gated profile-3 runs.
- No Unit-2 target census or body/firmware cause is claimed.
- Zero Color hits are scoped to the complete gated Unit-1 tele runs.
- This does not order later IRAMP, resampling, and writer work against every
  source callback.

## Reproduction

```bash
python3 tools/lldb_probes/src1_virtual_target_census/verify_pipeline_stage_order.py
```

Expected terminal result: JSON ending in `"result": "PASS"`.
