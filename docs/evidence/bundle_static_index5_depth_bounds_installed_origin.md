# Evidence: Index-5 Depth Bounds Have Installed, Not LRI, Origin

## Scope

This bundle closes the remaining origin question for the admitted mode-0
Triangulator/index-5 depth bounds:

```text
lower ray-depth bound = 200 mm
upper ray-depth bound = 640000 mm
```

The bounds are installed algorithm constants. They are not read from public
LRI calibration or protobuf fields on the installed production path.

## Artifact

The reusable verifier is:

```text
tools/lldb_probes/prefusion_node_dest_sentinel_custody/
  verify_20ca00_depth_bound_custody.py
```

It reuses complete canonical runtime reports under
`runs/stereo_candidate_gate/` and pins the installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Complete Constructor Census

Capstone extraction over the complete installed `__text` section proves:

- `0x3f2c40`, the constructor that selects the packed bound pair, has exactly
  one code reference: direct call `0x3f46e6`;
- wrapper `0x3f46d0` also has exactly one code reference: direct call
  `0x3b3011`;
- neither function has a RIP-relative address-taking reference or absolute
  64-bit function pointer in the installed bytes.

At the sole owner call:

```text
0x3b3004  xor  edx, edx
0x3b3011  call 0x3f46d0
```

Wrapper `0x3f46d0` does not alter `edx` before:

```text
0x3f46e6  call 0x3f2c40
```

Therefore the installed production call unconditionally supplies constructor
mode `0`. No LRI, calibration object, protobuf field, body identity, focal
tier, or runtime option supplies this selector.

## Installed Constants

Inside `0x3f2c40`, mode `0` selects the immediate packed float pair:

```text
[200.0, 640000.0]
```

The nonzero branch contains `[70.0, 40000.0]`, but the complete caller census
shows no installed production call that supplies a nonzero selector.

The same values are present in binary tables:

```text
0x609428: [200.0, 70.0]
0x609430: [640000.0, 40000.0]
```

Existing custody proof carries the selected mode-0 pair through:

```text
state+0x100/+0x104
  -> Triangulator owner+0x70/+0x74
  -> Ceres lower/upper bounds on the one-scalar ray depth
  -> StereoLayer index-5 reciprocal hypothesis endpoints
  -> record+0x40 depth-map path
```

Existing GDepth custody proves the length unit is millimeters.

## Runtime Agreement

The reused completed Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` reports each
observe one constructor entry with `rdx == 0`, matching the unconditional
static callsite.

No second-body rerun is required for the origin classification: the selector
is a literal at the sole installed caller, before any body-specific
calibration data can participate. Existing second-body GDepth custody already
separately validates the millimeter unit and downstream mechanism.

## Verification

Command:

```bash
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_depth_bound_custody.py
```

Relevant output:

```text
mode0=[200.0,640000.0] mode_nonzero=[70.0,40000.0]
installed_origin=sole 0x3b3011 caller hardcodes edx=0 -> mode0
custody=3f2c40.edx -> state+0x100/+0x104 -> owner+0x70/+0x74 -> Ceres scalar lower/upper
runtime_modes=28mm:0,35mm:0,70mm:0,150mm:0
```

## Admission

Admitted for `CLM-WARP-003`:

- the public/LRI-origin search terminates negatively and deterministically;
- the installed bridge-HDR production path hardcodes mode `0`;
- its ray-depth bounds are installed constants named operationally as the
  Triangulator ray-depth lower and upper bounds;
- their values are `200 mm` and `640000 mm`;
- there is no public LRI/protobuf field name or calibration carrier for them
  on this path.

Claim status remains unchanged.

## Non-Claims

- The statically present nonzero pair is not assigned a public mode name.
- This does not prove that no other product version or uninstalled caller can
  select the nonzero pair.
- This does not close source-image contribution, reducer closure, or final
  acceptance/rejection.
