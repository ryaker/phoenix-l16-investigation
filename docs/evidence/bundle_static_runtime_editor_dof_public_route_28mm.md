# Editor mode-1 DOFCache public activation and pixel effect (Unit-1 28mm)

## Result

Installed-bundle static proof and two complete runtime treatments close the
public activation path for the editor's mode-1 depth-of-field cache at one
Unit-1 28mm profile-3 RenderType-1 five-level request.

The embedded `renderer_state.proto` descriptor names the controls exactly:

- `ltpb.Settings.dof` (field 12)
- `ltpb.Settings.DOF.f_num` (required float, field 1)
- `ltpb.Settings.DOF.focus_depth` (required float, field 2)

Public `RendererBase::setProperty(ParamFloat,float)` indices `0` and `1`
write the first two floats of the Renderer request-state block. The render
worker snapshots those two floats and forwards them as `xmm0=f_num` and
`xmm1=focus_depth` to `DOFCache::setDOF` at `0x3f07d0`. That setter requires
both values to be positive and stores them at `DOFCache+0x98/+0x9c`.

For rendering mode 1, `0x3bb588` first requires `RendererPrivate+0x888 > 0`
(depth ready). It then selects `DOFCache` exactly when:

```text
f_num < (DOFCache+0x88 * DOFCache+0x84 / DOFCache+0x80)
```

Equality and greater values select `PipelineCache`. In the tested cache the
threshold operands are exact binary32 `2.0 * 28.0 / 3.680000066757202 =
15.217391014099121`.

## Runtime treatments

Both treatments first render the complete five-level mode-0 pyramid, then
switch to mode 1. Both set public `ParamFloat(19)`
`MaximumInFocusBlurPixels=9.0` while still in mode 0.

| treatment | mode-0 route | mode-1 route | cache `+0x98` | cache `+0x9c` |
|---|---:|---:|---:|---:|
| no DOF values | Pipeline `388`, DOF `0` | Pipeline `388`, DOF `0` | `15.2173910141` constructor value | `0.0` |
| public `f_num=2.0`, center focus | Pipeline `388`, DOF `0` | Pipeline `0`, DOF `388` | `2.0` | `6020.888671875 mm` |

The focus value comes from public
`DepthEditor::getDepthAtPoint({0.5f,0.5f})` after depth preparation. The
runtime request operand is exactly `15.2173910141` in the control and exactly
`2.0` after setting `f_num`, matching the installed selector predicate.

The final packed level-4 buffers are both `652x489x4 = 1,275,312` bytes:

| treatment | SHA-256 |
|---|---|
| no DOF values | `6e647328940c4a436760b2462677e89439211ebb101ab2bbbe7f0da8d023bcf1` |
| public DOF values | `4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0` |

The DOF treatment changes `659,544` bytes in `264,514` pixels, with maximum
absolute byte delta `95`. This proves a live final editor-buffer effect for
the selected DOFCache route under the stated treatment.

## Maximum-in-focus blur policy

Installed `ParamFloat(19)` validation accepts values in `[0.1,10.0]`, stores
the value at `RendererPrivate+0x8e0`, and rejects setting it after entering
mode 1. The optical helper at `0x2c5710` is stricter: it requires
`0 < max_infocus_blur < 10`, so the public endpoint `10.0` is accepted by the
setter but rejected later by the render helper. Runtime `0.1`, `1.0`, `5.0`,
and `9.0` controls show that this parameter does not itself change the cache
selection threshold; public `f_num/focus_depth` activate the route.

## Reproduction

```bash
bash tools/lldb_probes/editor_render_type_topology/run_editor_cache_route_mode.sh 1 9
bash tools/lldb_probes/editor_render_type_topology/run_editor_cache_route_mode.sh 1 9 sweep 2
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_dof_public_route.py
```

Reusable assets:

- `capture_editor_cache_route_interpose.c`
- `run_editor_cache_route_mode.sh`
- `verify_editor_dof_public_route.py`
- probe-only public controls in `tools/lri_process.cpp`

## Scope and limits

Admitted scope is Unit-1 `28mm`, profile 3, RenderType 1, complete five-level
mode-0 preparation followed by mode-1 rerender, public `f_num=2.0`, public
center-derived `focus_depth=6020.888671875 mm`, and
`MaximumInFocusBlurPixels=9.0`. Static schema, dispatch, validation, and branch
formulas are installed-bundle scope.

This does not prove other bodies, focals, output levels in isolation, modes
`2/3/4`, edit gestures, arbitrary focus depths/f-numbers, or the exact
internal optical blur/depth-compositing formulas inside `0x3f0b90` and its
helpers. Runtime call counts are treatment incidence, not algorithm constants.
