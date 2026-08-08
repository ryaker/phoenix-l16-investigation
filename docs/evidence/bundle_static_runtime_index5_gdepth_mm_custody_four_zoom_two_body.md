# Bundle Proof: Index-5 Ray Depth Uses Millimeters

## Scope

This bundle joins the admitted `StereoLayer<false>` index-5 depth path to the
installed public GDepth export boundary. It resolves the physical unit of:

- the one-scalar Triangulator ray depth and its `[200,640000]` bounds;
- the index-5 and `UpsampleLayer+0x90` depth-map pixels; and
- the generated reciprocal ray-depth lookup.

The lookup entries have reciprocal units: `mm^-1`, not `mm`.

## Artifacts

- Probe:
  `tools/lldb_probes/index5_gdepth_export_bridge/gdepth_export_probe.py`
- Unit-1 four-focal scripts:
  `tools/lldb_probes/index5_gdepth_export_bridge/unit1_{28,35,70,150}mm.lldb`
- Exact-focal Unit-2 discriminator:
  `tools/lldb_probes/index5_gdepth_export_bridge/unit2_28mm.lldb`
- Runners:
  `tools/lldb_probes/index5_gdepth_export_bridge/run_unit1_four_zoom.sh`
  and
  `tools/lldb_probes/index5_gdepth_export_bridge/run_two_body_28mm.sh`
- Verifier:
  `tools/lldb_probes/index5_gdepth_export_bridge/verify_gdepth_export_bridge.py`
- Ignored rerunnable outputs:
  `runs/index5_gdepth_export_bridge/*.{json,log,dng}`

The `.dng` filenames contain format-4 JPEG/XMP output, as already documented
for the repo-local CLI. This proof uses the embedded public GDepth metadata and
the live writer path; it does not claim that those files are raw DNG images.

## Static Formula

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It checks direct call targets, vtable targets, constants, and SHA-256 ranges
for this chain:

```text
StereoLayer<false> index 5, descriptor +0x2a8
  -> 0x26aa10 / 0x29ed90
  -> UpsampleLayer+0x90
  -> depth-cache selected descriptor
  -> 0x3d9050
       0x2673a0 / worker 0x267890: depth -> approximate reciprocal depth
       0x38c380 / worker 0x38c720: resize reciprocal field
       0x2674d0 / worker 0x267b30: reciprocal -> depth, cap 100000.0
  -> 0x3d8fe0: swap working descriptor +0x48 into provider slot +0x18
  -> provider 0x41aba0
  -> 0x3daf50: focal-crop/output resampling
  -> 0x41e180 GDepth writer
```

The two reciprocal workers use `rcpps` / `rcpss`; the second also applies
`minps` / `minss` against installed float `100000.0`. The intervening helper
resizes the reciprocal field. There is no length-unit conversion in this
chain: reciprocal and second reciprocal preserve the input depth unit.

The writer computes the minimum and maximum of its final float descriptor at
`0x41eb5a..0x41ec90` and streams those exact floats as `GDepth:Near` and
`GDepth:Far`. Installed public metadata states:

```text
GDepth:Format="RangeInverse"
GDepth:Units="mm"
```

## Runtime Custody

Complete no-auto-LRIS format-4 runs cover canonical Unit-1
`28mm/35mm/70mm/150mm` and exact-focal Unit-2 `28mm`.

Every run records:

- six completed StereoLayer descriptors at indices `0..5`, with dimensions
  `65x49`, `130x98`, `260x195`, `520x390`, `1040x780`, and `2080x1560`;
- seven depth-cache selections;
- exact descriptor-address and data-pointer identity between each of the six
  StereoLayer descriptors and the first six cache selections;
- exact descriptor-address and data-pointer identity between
  `UpsampleLayer+0x90` at `4160x3120` and the seventh cache selection;
- seven cache update calls;
- one `0x3d8fe0` working-to-provider descriptor swap;
- dynamic provider target `0x41aba0`;
- one final `10432x7824` GDepth float descriptor;
- exact runtime `Near` / `Far` values at the float-stream calls; and
- matching `RangeInverse`, `Near`, `Far`, and `Units="mm"` XMP in the output.

Two write watches on cache data-pointer fields prove the final promotion.
After the seven `0xf340` working-descriptor writes, stops at
`0x3d902b/0x3d902f` show the complete `+0x48` descriptor moved into `+0x18`
while the old `+0x18` descriptor moves to `+0x48`. The later provider reads
the exact promoted data pointer.

Observed extrema are run-specific:

| Body | Focal | Provider depth geometry | GDepth Near | GDepth Far |
|---|---:|---:|---:|---:|
| Unit-1 | 28mm | `10432x7824` | `598.125` | `20772.0` |
| Unit-1 | 35mm | `8320x6240` | `160.0297546` | `121502.453125` |
| Unit-1 | 70mm | `8832x6624` | `467.0308228` | `118351.9296875` |
| Unit-1 | 150mm | `4160x3120` | `52595.83984375` | `104708.171875` |
| Unit-2 | 28mm | `10432x7824` | `3326.0009766` | `111063.734375` |

The provider geometry is focal-dependent; the writer's final GDepth descriptor
and XMP image dimensions are `10432x7824` in every run. The numeric extrema
are observations, not constants or body effects.

## Admission

Admitted for `CLM-WARP-003`:

- index-5 ray depth and `UpsampleLayer+0x90` / `record+0x40` depth pixels use
  millimeters;
- the shared `[200.0,640000.0]` index-5/Triangulator bound pair is
  `[200 mm,640000 mm]`;
- the generated lookup is reciprocal ray depth in `mm^-1`;
- the public export name for the resulting surface is GDepth
  `RangeInverse`, with `Units="mm"`.

This is four-focal Unit-1 runtime proof plus an exact-focal Unit-2 body
discriminator and deterministic installed-binary formula proof. The canonical
`CLM-WARP-003` row remains `PROVEN`; the broader Lane B public-origin blocker
remains open at the scopes listed below.

## Non-Claims

- This does not assign an LRI/protobuf calibration field origin to the
  installed depth bounds.
- This does not give public names to the source-index `(lower,count)`
  descriptor or its source records.
- This does not make run-specific Near/Far extrema stable constants.
- This does not establish final source contribution, anti-ghosting policy, or
  merge acceptance/rejection.
