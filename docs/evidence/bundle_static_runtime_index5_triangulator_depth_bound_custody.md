# Evidence: Index-5 Lookup / Triangulator Depth-Bound Custody

> Superseding follow-up (2026-06-30):
> `bundle_static_index5_depth_bounds_installed_origin.md` proves the sole
> installed owner call hardcodes mode `0`. The selected `[200,640000]` bounds
> therefore have installed-constant origin, not an LRI/protobuf carrier.

## Scope

This note joins two previously separate installed-binary paths that use the
same selected endpoint pair:

- the index-5 `StereoLayer<false>+0xe0` reciprocal lookup vector generated
  from `[200.0, 640000.0]`; and
- the one-scalar `lt::Internal::ReProjectionCost` problem inside
  `lt::Triangulator::refine3dPoints()`.

The result closes the lookup vector's **internal** physical role: its endpoint
pair is the lower/upper bound pair installed on the Triangulator's ray-depth
scalar, so the reciprocal lookup is an internal ray-depth hypothesis grid.
It does not establish public units, an LRI/protobuf source, a public field
name, source-index semantics, solved values, final source contribution, or
acceptance/rejection.

## Artifacts

- Deterministic verifier:
  [verify_20ca00_depth_bound_custody.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_depth_bound_custody.py)
- Reused complete runtime reports:
  `runs/stereo_candidate_gate/stereo_candidate_gate_{28mm,35mm,70mm,150mm}.json`
- Prior endpoint/count proof:
  [lldb_lookup_endpoint_count_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_lookup_endpoint_count_origin_four_zoom.md)
- Prior lookup-vector generator proof:
  [lldb_index5_lookup_vector_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_lookup_vector_public_origin_four_zoom.md)
- Reprojection-cost identity/formula proof:
  [bundle_static_prefusion_20ca00_reprojection_cost.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_prefusion_20ca00_reprojection_cost.md)

## Mode-Selected Bounds

The installed `0x3f2c40` constructor preserves its third integer argument in
`ebx`. At `0x3f4100`, that mode selects one of two packed float pairs:

| Constructor mode | Selected pair |
|---:|---:|
| `0` | `[200.0, 640000.0]` |
| nonzero | `[70.0, 40000.0]` |

The same four scalar values are stored in the installed binary's endpoint
tables:

```text
0x609428: [200.0, 70.0]
0x609430: [640000.0, 40000.0]
```

The existing index-5 endpoint proof independently traces the selected first
table row `[200.0, 640000.0]` through
`0x3ff43c -> 0x2681b0 -> 0x26ba90`, then into
`StereoLayer<false>+0x298/+0x29c` and the exact reciprocal lookup-vector
generator.

## Bound Custody

The verifier SHA-256 pins and Capstone-decodes the relevant instruction
windows. The selected pair follows this installed-binary path:

```text
0x3f2c40 third argument edx
  -> preserved constructor mode in ebx
  -> 0x3f4100 selects [200,640000] or [70,40000]
  -> 0x3f414a calls 0x225160 with the selected pair
  -> state+0x100/+0x104
  -> 0x2255dd -> 0x20ad60 -> 0x20ac60
  -> Triangulator owner+0x70/+0x74
  -> 0x20ca00 callback reads owner+0x70
  -> ceres::Problem::SetParameterLowerBound(local scalar)
  -> 0x20ca00 callback reads owner+0x74
  -> ceres::Problem::SetParameterUpperBound(the same local scalar)
```

The imported-stub verifier resolves the two calls as
`ceres::Problem::SetParameterLowerBound(double*,int,double)` and
`ceres::Problem::SetParameterUpperBound(double*,int,double)`. Both calls use
the same local scalar at `rbp-0xc8`. The companion reprojection-cost verifier
proves that scalar scales ray `(bx,by,1)` before a 3x4 projection and two
perspective-divided residuals. Together, these facts name it internally as a
ray-depth scalar rather than an opaque optimization parameter.

## Runtime Selection

The verifier reuses the already-complete `stereo_candidate_gate` reports. It
requires, for each report:

- clean process exit status `0`;
- no probe errors or drive-step cap;
- exactly one `0x3f2c40` constructor sample; and
- constructor register `rdx == 0`.

All four canonical Unit-1 focal tiers select mode `0`:

| Focal tier | Constructor mode | Bounds |
|---|---:|---:|
| `28mm` | `0` | `[200.0, 640000.0]` |
| `35mm` | `0` | `[200.0, 640000.0]` |
| `70mm` | `0` | `[200.0, 640000.0]` |
| `150mm` | `0` | `[200.0, 640000.0]` |

This runtime selection is one body across four focal tiers. No cross-unit
universality claim is made. A Unit-2 rerun is not required for the admitted
installed-binary custody or for the scoped statement that the canonical runs
select mode `0`; body-sensitive numeric incidence or solved-value claims would
require separate risk-based validation.

## Admitted Meaning

The following is now admitted:

```text
selected Triangulator ray-depth bounds [200.0, 640000.0]
  == selected index-5 lookup endpoints [200.0, 640000.0]
  -> internally generated reciprocal ray-depth hypothesis grid
  -> source uint16 selects one grid hypothesis
  -> 0x267010 materializes the selected float into the index-5 descriptor
```

This closes the earlier phrase "lookup-vector physical meaning remains open"
only at the internal algorithmic level. The following remain open:

- public physical units;
- public calibration/LRI/protobuf origin and public name for the bounds;
- public semantics of the `0x299c70` source-index descriptor and its source
  records;
- whether every selected source index is used as a Triangulator solve input;
- solved-value distributions and downstream image/source contribution; and
- final acceptance/rejection behavior.

The alternate `[70.0, 40000.0]` pair is statically present and selected by the
nonzero constructor branch. It was not selected by the four canonical runtime
reports, so no focal-tier or public-mode meaning is assigned to it.

## Verification

Command:

```bash
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_depth_bound_custody.py
```

Output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
table_near=[200.0,70.0] table_far=[640000.0,40000.0]
mode0=[200.0,640000.0] mode_nonzero=[70.0,40000.0]
custody=3f2c40.edx -> state+0x100/+0x104 -> owner+0x70/+0x74 -> Ceres scalar lower/upper
runtime_modes=28mm:0,35mm:0,70mm:0,150mm:0
```
