# Static/Runtime Evidence: Lumen Editor Profile-3 Topology

**Date:** 2026-07-16  
**Status:** VERIFIED, scoped `CLM-COMPAT-001` addendum  
**Initial editor scope:** canonical Unit-1 `28/35/70/150mm`, profile 3,
GUI-style RenderType `1`, five-level coarse-to-fine pyramid sweep  
**Post-edit scope:** canonical Unit-1 `28mm`, one synthetic brush-depth edit
followed by the same five-level sweep

## Question

Does Lumen's interactive editor use the same calibrated IRAMP topology as the
profile-3 bridge/export path, and does a depth edit trigger a fresh raw
multi-camera merge?

## Installed-Bundle Custody

The checked installed files are:

```text
Lumen executable SHA-256:
1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d

libcp.dylib SHA-256:
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

`verify_lumen_editor_callgraph.py` deterministically checks these installed
Lumen call-graph facts:

1. `ImageWriter::ImageWriter` constructs its inline renderer at `+0xf8` with
   `RendererProfile = 3` (`0x10006122a -> 0x10016e692`).
2. `ImageViewer` embeds `ImageWriter` at `+0x40`, making that same renderer
   `ImageEditor+0x138`.
3. `ImageEditor::ImageEditor` constructs `DepthEditor` at `+0x200` over the
   exact renderer at `+0x138` (`0x1000687c5..0x1000687d6`).
4. `ImageEditor::postDepthEdit` cancels requests on renderer `+0x138`, invokes
   the supplied edit on `DepthEditor+0x200`, and marks editor state dirty.
5. `ImageEditItem::commitDepthEdit` calls `postDepthEdit`; on success it clears
   known regions and calls `pushRenderRequest()`.
6. Per-level requests pass `RenderType = 1` into `ImageViewer::render`, which
   forwards to `CIAPI::Renderer::render` on the same renderer with the final
   bool argument `0`.

The verifier writes body-window SHA-256 values and these facts to
`runs/editor_render_type_topology/static_gui_callgraph.json`.

## Reusable Harness

`tools/lldb_probes/editor_render_type_topology/` contains:

- the installed-app static call-graph verifier;
- single-request type-`1`/type-`2` comparison scripts;
- four-focal GUI-style full-pyramid scripts;
- a synthetic `BrushDepthEditingParams` run with a breakpoint snapshot at
  `CIAPI::DepthEditor::pushBrushDepthEdit`; and
- aggregate verification scripts.

The repo-local renderer accepts the additive probe-only switches
`--render-type`, `--render-only`, `--sync-render`, `--gui-level-sweep`, and
`--brush-edit-rerender`. Existing default behavior remains type `2` and does
not use these probe-only scheduling paths.

Rerunnable JSON reports live under ignored
`runs/editor_render_type_topology/`. No `/tmp` artifact is an evidence
dependency; output names there are unused placeholders only.

## Runtime Results

### One request is not the GUI schedule

One synchronous level-1 request reaches neither `initResAmp`, `processLevel0`,
IRAMP, nor the three wrapper families for either RenderType `1` or `2`.
Both requests still reach calibration, wide MonoFusion, and partial index-5
depth work. Therefore a one-request probe cannot classify editor topology.

### Initial GUI-style pyramid construction

The GUI schedule issues five requests, one per output-pyramid level. Counts
are observations for these runs, not algorithm constants.

| Focal | Requests | `initResAmp` | `processLevel0` | IRAMP | `src1` | `src2` | contributor | MonoFusion | index-to-depth |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 28mm | 5 | 2 | 298 | 293 | 300 | 300 | 426 | 336 | 6 |
| 35mm | 5 | 2 | 227 | 232 | 234 | 234 | 369 | 277 | 6 |
| 70mm | 5 | 2 | 220 | 220 | 221 | 221 | 341 | 0 | 6 |
| 150mm | 5 | 2 | 60 | 63 | 63 | 63 | 285 | 0 | 6 |

All four focal tiers reach the exact installed surfaces used by the admitted
profile-3 parent topology:

```text
PipelineCache::initResAmp
  -> PipelineCache::processLevel0
  -> IRAMP 0x365960
  -> src1 wrapper 0x3ecc10
  -> src2 wrapper 0x3ecd80
  -> contributor wrapper 0x3eced0
```

Wide invokes MonoFusion and tele does not, exactly matching the admitted
profile-3 route split. This proves topology-level reuse. It does not by itself
prove pixel-identical editor and export output, identical ROI/scale policy, or
that each invocation has identical local operands.

### Post-brush rerender

The 28mm brush run snapshots all counters immediately before the public
`pushBrushDepthEdit` wrapper. The following five-request sweep records:

| Surface | Post-edit hits |
|---|---:|
| renderer request | 5 |
| `initResAmp` | 2 |
| `processLevel0` | 0 |
| IRAMP | 0 |
| `src1` / `src2` / contributor wrappers | 0 / 0 / 0 |
| MonoFusion | 0 |
| min-cost index / index-to-depth | 0 / 0 |
| calibration composition | 0 |

Thus the tested brush edit does not perform a fresh raw calibration, stereo,
MonoFusion, or IRAMP merge. It rerenders from already prepared state after a
small `initResAmp`-level touch. This is a tested 28mm brush result, not a
global assertion for every editor control or every focal tier.

## Admission Consequence

- Initial Lumen editor image construction uses the same profile-3 calibrated
  IRAMP topology surfaces across the canonical four focal tiers.
- The editor is not a separate ten-equal-camera merge engine. The admitted
  role topology remains `src1`, generated/direct `src2`, and five warped
  direct contributors.
- A clean-room implementation should build the calibrated depth-driven
  five-warp profile-3 path before editor depth-edit compatibility.
- The tested post-brush editor rerender reuses prepared state and does not
  rerun the heavy raw merge.

`CLM-COMPAT-001` remains `REFERENCE_ONLY`: profiles `1/2`, exact depth-edit
formulas, other edit controls, editor display packing/color policy, and
editor/export pixel identity remain outside this proof. The later
`bundle_static_runtime_editor_display_packing_28mm.md` closes the tested
default level-4 route from merged `PipelineCache` through the per-level Color
pipeline, type-13 output record, and conditional GUI byte packer. Byte-exact
before/after joins there isolate the editor/export difference to seven named
callbacks; remaining display-specific formulas stay open.
