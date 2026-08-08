# Static/Runtime Evidence: Default Hot-Pixel Full-Frame Boundary Closure

## Purpose and scope

This bundle supersedes the outer-edge residual left by
`bundle_static_runtime_hot_pixel_fullframe_correction_unit1_28mm.md`. It
decodes the six-sample region synthesized by installed helper `0x178b0`, joins
that region to the already admitted `0x2e8cc0` rank/LUT/isolation worker, and
replays complete `4160x3120` pre/post captures bit-for-bit.

Runtime full-frame scope is:

- Unit-1 exact `28mm` A2;
- Unit-2 exact `28mm` A2, providing an independent physical calibration body;
- Unit-1 canonical `35mm` A2, providing the other MonoFusion-active focal
  route.

Installed-static scope is the SHA-pinned generic `0x178b0` / `0x2e8cc0`
formula. Existing four-focal route proof supplies selected default-hot-pixel
liveness and phase-parametric applicability; canonical `70mm` / `150mm` do
not construct MonoFusion, so they are not presented as duplicate MonoFusion
captures. No unselected SoftISP, sampling-pattern, or profile arm is claimed.

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Reusable artifacts

- `tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_hotpixel_preprocess_probe.py`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/run_hotpixel_preprocess_unit1_28mm.sh`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/run_hotpixel_preprocess_unit2_28mm.sh`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/run_hotpixel_preprocess_unit1_35mm.sh`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/verify_hot_pixel_fullframe.py`
- `tools/lldb_probes/prefusion_monofusion_flow_origin/diagnose_flow_source_hotpixel.py`

Raw rerunnable captures are under
`runs/prefusion_monofusion_flow_origin/{unit1_28mm,unit2_28mm,unit1_35mm}_hotpixel_preprocess/`.
Each report retains the complete pre/post image, four runtime LUT payloads,
and full backing allocations for representative top, bottom, left, right, and
corner worker regions.

## Exact clipped-region construction

For output rectangle `[x0,y0,x1,y1]`, `0x2e8cc0` calls `0x178b0` with margin
`6`. The returned descriptor has logical origin `(-6,-6)`, logical upper
bound `(tile_width+6,tile_height+6)`, and therefore allocation extent
`(tile_width+12,tile_height+12)`. Its `data` pointer is biased to logical
coordinate `(0,0)`; its allocation pointer starts at `(-6,-6)`.

In-frame samples are exact copies from the full source. For an out-of-frame
global coordinate `(x,y)`, define parity-preserving projected coordinates:

```text
project(q, n) = q                         when 0 <= q < n
              = q & 1                     when q < 0
              = n - 2 + (q & 1)           when q >= n

cx = project(x, width)
cy = project(y, height)
S  = { source(cx+dx, cy+dy) |
       dx,dy in {-2,0,2}, coordinate remains in frame }
halo(x,y) = sort(S)[floor(len(S)/2)]
```

Thus even and odd Bayer coordinates project independently. At an edge the
available same-CFA set contains six samples; at a corner it contains four.
The selected element is the upper median for an even set. Static body
`0x178b0` gathers only valid `+-2` same-lattice samples, calls sorter
`0x19f90`, and stores element `count>>1`. Runtime reconstruction matches all
`317,312` words in the four representative backing allocations for every
run, including `8,004` out-of-frame words per run.

## Complete worker replay

The exact six-sample source halo is sufficient because an output decision
reads marker neighbors through distance four, while each marker's rank
residual reads source neighbors through distance two. Applying the admitted
worker formula over that halo gives:

```text
far = ((x & 1) == ((y & 1) XOR phase))
neighbors = distance-2 cross
          + (distance-2 diagonals if far else distance-1 diagonals)
r = max(0, source(x,y) - sixth_smallest(neighbors))
c = source(x,y) - r
lane = 2*(y&1) + (x&1)
marker = float32(r) > 4.0f * LUT[lane][c]
phase_selector(y) = (y & 1) XOR phase
```

The previously admitted two-branch isolation predicate then selects whether
to replace `source` by `c`. Four runtime LUT lanes are retained verbatim by
each capture; all four lanes are equal within each tested monochrome source,
but their payloads differ among the three runs.

## Deterministic results

| Scope | Source SHA-256 | LUT SHA-256 | Replacements | Exact output | Wrong-phase mismatch |
|---|---|---|---:|---:|---:|
| Unit-1 exact `28mm` | `11458e2e...aa2` | `81e8a6d1...eef` | 19,586 | `12,979,200 / 12,979,200` | 31,091 |
| Unit-2 exact `28mm` | `40a919ed...f87` | `06bc39ff...c92` | 8,404 | `12,979,200 / 12,979,200` | 7,505 |
| Unit-1 canonical `35mm` | `178fdcfa...e75` | `988bb887...25d` | 113,435 | `12,979,200 / 12,979,200` | 169,843 |

Observed output SHA-256 values are respectively:

```text
fd9bee8a5a5dc84f0b2d9c4d5dd45708fd9e4ce1c41b3533e093f09c1faefe12
7914fdcf97ce88d7e79ca96564762858a72cef0e8d365f0713840b400cc94be4
b83d128e9bd09df78849cdb50ae1a49408dbdac82f929c13a0eac31f705f2194
```

The wrong-phase controls establish unique phase selection rather than an
edge-only accidental match. The three distinct LUT payloads and correction
populations make the body/focal checks discriminating.

## Admission consequence

- Close the 118-sample Unit-1 outer-edge residual.
- Admit the selected default hot-pixel stage as full-frame formula-closed for
  the selected profile-3 route, with explicit Unit-1 `28/35mm` and Unit-2
  exact-`28mm` complete runtime replay plus installed generic formula scope.
- Restore `CLM-STEREO-001` to `PROVEN` / `SPEC_READY`; its stereo cost, SGM,
  hypothesis, depth, collapse2, and final-YUV portions were never reopened.
- Keep unselected SoftISP/sampling-pattern/profile arms outside this claim.
