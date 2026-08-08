# Row-Image Public Names and Output Policy, Four Zooms

## Question

Resolve the public meanings of the IRAMP weight/shaping vectors, name the
six-byte row pixel type, and bound the downstream row-image policy through the
tested CLI HDR writer.

## Reusable artifacts

- `tools/lldb_probes/row_image_public_policy/verify_row_image_public_policy.py`
- admitted runtime reports under
  `runs/codex_opus_iramp_terminal_validation/`,
  `runs/codex_final_compositing_case1_case3_boundary/`, and
  `runs/codex_final_output_hdr_writer_boundary/`
- the earlier producing probes cited by
  `bundle_lldb_iramp_36e530_accumulator_prep.md`,
  `bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`,
  `bundle_lldb_iramp_post_weighted_add_shaping.md`,
  `bundle_lldb_iramp_caller_post_square_scale.md`,
  `bundle_lldb_iramp_caller_3e5720_executor_setup.md`, and
  `bundle_lldb_owner_f0_downstream_consumer.md`

Reproduce the independent aggregate check:

```bash
python3 tools/lldb_probes/row_image_public_policy/verify_row_image_public_policy.py
```

No live `/tmp` or `/private/tmp` artifact is an evidence dependency.

## Public weight and shaping meanings

The 16 first-stage weights and the later width-`N` weights have the exact
operational identity

```text
h_N(i) = sin^2(pi * (i + 1/2) / N),  0 <= i < N
```

within the installed generator's float precision. This is a symmetric,
half-sample-centered Hann window. Both accumulator sites apply the separable
two-dimensional product `h_N(x) * h_N(y)`. The verifier independently checks
the first live lane-3 product at `N=40` for `28mm`/`35mm` and `N=34` for
`70mm`/`150mm`.

The invariant transform rows captured at all four focals are:

```text
( 1/sqrt(3),  1/sqrt(3),  1/sqrt(3))
( 1/sqrt(2),          0, -1/sqrt(2))
( 1/sqrt(6), -2/sqrt(6),  1/sqrt(6))
```

The body multiplies input lanes by these rows to produce RGB. This is the
orthonormal opponent-color `I1/I2/I3 -> RGB` inverse transform. Consequently,
the clamped-update vector `(2,0,0,0)` is an `I1`-only intensity correction;
its `[-0.1,+0.1]` clamp does not alter the two chroma/opponent lanes. Lane 3
is the accumulated separable blend-weight mass: the preceding loop explicitly
replaces source lane 3 with `reciprocal_sum * 0.2`, multiplies all four lanes
by `h_N(x)h_N(y)`, and accumulates them together. It is normalization weight,
not a fourth color channel.

The post-square vector is publicly named by installed RTTI. Vtable
`0x65b8c8` belongs to
`lt::Internal::Pipeline::setWhiteBalance(lt::Internal::PipelineBase::AWB)::$_23`,
and its body `0x342a80` obtains the three channel values through the live
CCM/AWB calculation. Helper `0x1bea20` copies those values from object
`+0x74/+0x78/+0x7c`; the IRAMP caller constructs
`(awb_r, awb_g, awb_b, 1)` and applies it with `0x2d7320`.

## Public pixel types and cache policy

Installed C++ RTTI closes the formerly inferred six-byte format:

| Surface | Exact installed identity |
|---|---|
| `0x65f5e0`, sink slot `0x3ec960` | `PipelineCache` constructor callback receiving `Tile<Vec3<Float16>>` |
| `0x66b020`, writer setup `0x3e5720` | `ImageConvertPixelType<Vec3<Float16>, vec4x32f>` |
| `0x66a690`, worker `0x3d5290` | `ImageConvertPixelType<vec4x32f, Vec3<Float16>>` |
| `0x66a728`, route `0x3d5400` | `TileCache<Vec3<Float16>>::renderROI<vec4x32f>` |

Template argument order is destination then source. Thus the owner `+0xf0`
row store is exactly three binary16 color channels (`Vec3<Float16>`, six
bytes/pixel), not an unnamed packed format. Reads expand it to
`vec4x32f` (16 bytes/pixel), and the proven converter writes lane 3 as `1.0`
before tile-cache resampling.

## Downstream row-image and file policy

For the canonical bridge-HDR quartet:

1. IRAMP's RGB result is multiplied by the live AWB three-channel vector.
2. `PipelineCache` stores the `512x512` result as `Tile<Vec3<Float16>>`.
3. Selected-cache reads expand the tile to `vec4x32f` with lane 3 equal to
   `1.0`; `TileCache<Vec3<Float16>>::renderROI<vec4x32f>` performs the already
   admitted weighted four-tap row resampling.
4. Final case `3` selects installed `linear_prophoto_rgb`, passes a populated
   `10432x7824` `vec4x32f` descriptor (`166912 = 10432 * 16` row bytes) to the
   `.hdr` writer, and emits installed Radiance
   `FORMAT=32-bit_rle_rgbe`.

The output-config join is observed at `28mm`, `35mm`, `70mm`, and `150mm`.
The installed binary contains both the `linear_prophoto_rgb` selector arm and
the Radiance RGBE writer marker. This proves the tested CLI row/file policy;
it does not claim that every GUI/export format uses this route.

## Admission boundary

Admit to `CLM-MERGE-005`:

- half-sample Hann separable weights;
- `I1/I2/I3` opponent-vector meanings, intensity-only clamp, and lane-3
  normalization-weight meaning;
- public AWB identity of the post-square channel vector;
- exact `Vec3<Float16>` cache and `vec4x32f` working-row names; and
- the four-focal `linear_prophoto_rgb` float-row to Radiance RGBE output
  policy.

This resolves checklist C3's naming and row-policy request. It does not by
itself close the separate contributor acceptance/rejection predicate still
tracked under `CLM-MERGE-005`.
