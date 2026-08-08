# Cross-talk full-frame tile decomposition (corrective runtime evidence)

Probe: `tools/lldb_probes/correction_liveness/crosstalk_tiling_census_probe.py`
Harness: `run_crosstalk_tiling_census.sh "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" unit1_28mm_a1 0`
Report: `runs/correction_liveness/tiling_unit1_28mm_a1/report.json` (1207 records, `truncated=false`, `errors=[]`)
Analyzers: `analyze_crosstalk_tiling.py`, `analyze_crosstalk_tiling2.py`, `analyze_crosstalk_tiling3.py`

## What was open

The single admitted packet in `bundle_static_runtime_crosstalk_exact_formula_two_body.md` covered
one `260 x 260` region with `coordinate_offset_f32 = (0,0)` and
`coordinate_scale_f32 = (f32(1/260), f32(1/260))`. It was not proven how Lumen decomposes the full
`4160 x 3120` Bayer plane, nor whether interior tile seams read true neighbours or reflect.

## Census result

A complete profile-3 render of Unit-1 28mm camera A1 issues **1207** invocations of the scalar
interpolation helper `libcp+0x1019D0`, spread over **10 worker threads**.

### Uniform across all 1207 invocations

* `coordinate_scale_f32 == (0.003846153849735856, 0.003846153849735856)` — i.e. `f32(1/260)` on both
  axes, with **no** distinct values. Cell pitch is therefore globally `260` px:
  `4160 / 260 = 16` intervals across a `17`-wide grid and `3120 / 260 = 12` intervals across a
  `13`-tall grid. The fit-grid geometry maps exactly onto the frame with no residue.
* `parity_i32 == (1, 0, 0, 0, 1, 1, 0, 1)` — one Bayer phase for the whole frame, as expected.

### Two-level decomposition

Work is split by a dynamic tile executor into variable-size destination buffers
(observed destination sizes `276x276`, `532x532`, `276x314`, `276x266`, `330x276`, `266x276`,
`532x522`, `532x570`, `522x532`, `586x532`, `266x266`, `330x266`, `266x314`, `330x314`,
`586x522`, `522x522`, `522x570`, `586x570` — 195 distinct destination allocations, pooled and reused).

Each tile is then **subdivided at grid-cell boundaries**, one helper invocation per (tile, cell)
intersection. The signature is exact: the first sub-call along an axis carries
`offset = tile_origin mod 260` and ends at `260 - offset`; subsequent sub-calls carry `offset = 0`
and step by `260`, clipped to the tile size. Worked example (tile whose origin satisfies
`x0 mod 260 = 222`, `y0 mod 260 = 0`, size `276 x 266`):

```
off=(222,0) start=[  0,  0] end=[ 38,260]
off=(  0,0) start=[ 38,  0] end=[276,260]
off=(222,0) start=[  0,260] end=[ 38,266]
off=(  0,0) start=[ 38,260] end=[276,266]
```

`260 - 222 = 38` — the x split lands exactly on the cell boundary.

Every sub-call receives its **own** 4-matrix corner block (383 distinct `matrices_sha_prefix` values
over 190 distinct offsets), so the `offset = 0` blocks with `t` running `[j, j+1]` are supplied
corners pre-shifted for that parameterization. The evaluated bilinear field is therefore continuous
across cell boundaries and identical to evaluating cell `j` at `s = t - j`.

**Consequence:** the tiling is a pure work-partitioning artifact. The mathematically equivalent
whole-frame formulation is

```
gx = f32(x * f32(1/260))      # x = quad top-left column in frame coordinates
gy = f32(y * f32(1/260))
cx = trunc(gx), sx = gx - cx  # bilinear between grid columns cx, cx+1
cy = trunc(gy), sy = gy - cy
```

### Halo / seam policy

Source view descriptors carry a real low-side halo on every interior axis:

| n | src origin | src bounds | src size | src stride | data - allocation (bytes) |
|---|---|---|---|---|---|
| 586 | `(-2,-2)` | `(278,278)` | `(276,276)` | 280 | 2248 = `4*(2*280 + 2)` |
| 204 | `(-2,-2)` | `(534,534)` | `(532,532)` | 536 | 4296 = `4*(2*536 + 2)` |
|  55 | `(-2, 0)` | `(278,268)` | `(276,266)` | 280 |    8 = `4*2` |
|  38 | `( 0,-2)` | `(268,278)` | `(266,276)` | 268 | 2144 = `4*(2*268)` |

The data pointer is displaced from the allocation base by exactly the halo the origin declares:
`origin = -2` on an axis buys 2 rows/columns of **real neighbouring pixel data** before the tile.
`origin = 0` on an axis occurs only where the tile touches the true frame border, and there the
`bounds` grow by `+2` on the opposite side instead (`266 -> 268`, matching the single captured
packet in the two-body bundle, which was the frame's top-left tile: `origin (0,0)`, `size (266,266)`,
`bounds (268,268)`).

**Consequence:** interior tile seams read true neighbour samples, never reflections. Whole-sample
reflection (`-1 -> +1`) applies **only at the true frame border**. A whole-frame Phoenix
implementation that reflects only at the image edge is bit-equivalent to Lumen's tiled execution.

## Status

The last open sub-question of the cross-talk stage is closed. Combined with
`bundle_static_runtime_crosstalk_exact_formula_two_body.md` (amount selection, IR preparation,
prepared-matrix construction, scalar worker — all bit-exact on two physical bodies) and
`bundle_corrective_runtime_crosstalk_callback_liveness_two_body_four_zoom.md` (stage liveness at
28/35/70/150mm on two bodies), the stage is fully specified for re-implementation.
