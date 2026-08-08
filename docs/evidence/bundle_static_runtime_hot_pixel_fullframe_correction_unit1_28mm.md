# Static/Runtime Evidence: Default Hot-Pixel Full-Frame Correction

## Purpose and scope

This bundle corrects the earlier focused-patch interpretation in
`bundle_static_runtime_index5_guidance_collapse2_hot_pixel.md`. It uses the
SHA-pinned installed worker plus a complete pre/post worker capture for the
Unit-1 exact-`28mm` A2 source in `L16_02130`.

The result is exact over the complete interior domain
`x in [8,4152), y in [8,3112)`. The outer eight-pixel frame is not yet
formula-closed: 118 of 12,979,200 samples remain different. This evidence is
therefore corrective and `PARTIAL`, not a full-stage admission and not
four-focal closure.

This residual is superseded by
`bundle_static_runtime_hot_pixel_fullframe_boundary_two_body_wide.md`, which
reconstructs the installed six-sample parity-preserving median halo and
replays complete outputs exactly across Unit-1 `28/35mm` and Unit-2 exact
`28mm`.

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Artifacts

Reusable harnesses:

- `tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_hotpixel_preprocess_probe.py`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/run_hotpixel_preprocess_unit1_28mm.sh`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/diagnose_flow_source_hotpixel.py`
- `tools/lldb_probes/index5_guidance_channel_origin/verify_hot_pixel_formula.py`

Rerunnable captures under
`runs/prefusion_monofusion_flow_origin/unit1_28mm_hotpixel_preprocess/`:

```text
11458e2ed1fc5ba35d4235398da66f432be322530ad6c9e4014b6dbaec65caa2  a2_hotpixel_input.u16le
fd9bee8a5a5dc84f0b2d9c4d5dd45708fd9e4ce1c41b353e093f09c1faefe12  a2_hotpixel_output.u16le
```

The captured input is byte-identical to the public RAW10 reconstruction over
all `4160*3120` words. The captured worker executes 192 nonoverlapping
`256x256`-maximum rectangles, exactly tiling the frame. Its four live LUT
pointers are byte-identical (SHA-256
`81e8a6d1cd2ccb74bd2569ad85c352594bdefd48de985cbdf98768d817ea9eef`)
and match the independently generated installed panchromatic gain-150 row.
The separate hot-pixel-leakage route has zero entries in this run.

## Correct worker formula

The installed scalar/SIMD body at `0x2e8cc0` forms one rank residual for each
source row retained in its nine-row rolling ring. It does not apply two serial
rank filters. The earlier one-pixel receipt happened to produce `40` under
both a real first residual and a hypothetical second residual, so it could not
distinguish the two models.

For an interior pixel, with `phase = phase_x XOR phase_y`:

```text
far = ((x & 1) == ((y & 1) XOR phase))
neighbors = distance-2 cross
          + (distance-2 diagonals if far else distance-1 diagonals)
r = max(0, source(x,y) - sixth_smallest(neighbors))
c = source(x,y) - r
marker = (c | 0x8000) iff float32(r) > 4.0f * LUT[c], else 0
```

The isolation branch selector is row-varying:

```text
phase_selector(y) = (y & 1) XOR phase
```

It is not the frame-constant `phase` value. The installed two-branch spatial
predicate in `verify_hot_pixel_formula.py` is otherwise unchanged. A live
discriminating receipt at `(3952,179)` captured the same complete marker
window as the public replay. Because the row selector is `1`, the alternate
diamond branch computes `cross + adjacent = 2` and rejects the candidate,
matching Lumen. The former constant-selector replay incorrectly accepted it.

## Full-frame result

With the one-residual construction and row-varying selector:

```text
pixels_exact=12979082/12979200
interior_mismatch=0
border_mismatch=118
false_changes=0
unequal_shared_changes=0
```

Thus every accepted/rejected decision and every replacement value is exact in
the complete eight-pixel-inset interior. The 118 residual differences are
strictly confined to the global outer eight-pixel frame. Standard `reflect`,
`symmetric`, `edge`, and `wrap` padding do not close that frame; the installed
`0x178b0` clipped-region helper and the worker's `0xffff/0x7fff` initialized
rolling storage require a separate exact boundary transcription.

## Admission consequence

- Refute the former two-serial-residual statement.
- Admit the one-residual and row-varying-selector correction at focused
  Unit-1 exact-`28mm` scope.
- Keep the default hot-pixel stage `PARTIAL` for its outer-eight-pixel boundary
  policy and for cross-body/focal full-frame validation.
- Do not weaken the independently proven collapse2, YUV, G-42, SGM, or depth
  portions of `CLM-STEREO-001`.
