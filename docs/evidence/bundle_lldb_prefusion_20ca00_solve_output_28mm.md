# Evidence: Prefusion `0x20ca00` Solve Output, Unit-1 28mm

## Scope

This note adds runtime value proof to the installed-binary ownership and cost
formula already admitted for the `0x20ca00` callback inside
`lt::Triangulator::refine3dPoints()`.

One complete canonical Unit-1 `28mm` bridge-HDR render proves that the local
Ceres solve sometimes changes its bounded ray-depth scalar, and that the
post-Solve write path materializes that scalar into selected owner records.
For every captured solve/write group, final `record+0x10` equals the float32
solved scalar. This is one body, one focal tier, and one render; it is not a
cross-unit/four-zoom distribution or final image/source-contribution proof.

## Artifacts

- Runtime callback:
  [prefusion_20ca00_solve_output_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_solve_output_probe.py)
- Solve-only LLDB script:
  [node_dest_20ca00_solve_output_only_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_solve_output_only_28mm.lldb)
- Runner:
  [run_20ca00_solve_output_only_28mm.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_solve_output_only_28mm.sh)
- Runtime verifier:
  [verify_20ca00_solve_output_runtime.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py)
- Static ownership/write verifier:
  [verify_20ca00_record_range_custody_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py)
- Static post-Solve formula verifier:
  [verify_20ca00_postsolve_formula_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py)
- Raw report/log/HDR output:
  `runs/prefusion_20ca00_solve_output_only/`

The callback's module lookup uses `lldb.SBFileSpec("libcp.dylib")`, matching
the current LLDB Python API. An earlier zero-count report produced by passing a
plain string to `SBTarget.FindModule` was rejected and replaced; it is not an
evidence input.

## Clean Completion

The admitted run is:

```text
LRI: /Volumes/Base Photos/Light/2018-07-23/L16_02130.lri
unit: Unit-1
focal tier: 28mm
mode: profile 3, export format 3, --no-auto-lris
output: 10432 x 7824 Radiance HDR
process: exited with status 0
```

The runtime verifier additionally requires:

- no callback traceback or LLDB error in the log;
- JSON `errors == []` and no incomplete frames;
- ten callback entries, ten completed frames, and ten returns; and
- output beginning with the Radiance HDR magic bytes.

## Static Boundary

The SHA-pinned static verifier proves:

```text
owner -> callable+0x08 -> callback owner at rbp-0x2a8
owner record vector -> 0x14-byte records
selected offset = 5 * gate_index
selected triple = record+0x08/+0x0c/+0x10
```

Immediately after `ceres::Solve`, `0x20d616..0x20d6b1` reads the local double
at `rbp-0xc8`, converts it to float32, applies the first captured transform,
and writes the selected triple. The verifier proves the only access to
`rbp-0xc8` between the Solve return and the first triple writes is the read at
`0x20d690`; no intermediate store rewrites the scalar.

`0x20d6b6..0x20d732` then applies a second captured transform and overwrites
the same three fields. The immediate parent later reduces positive
`record+0x10` values into owner `+0x78/+0x7c`.

The dedicated post-Solve formula verifier pins the complete
`0x20d603..0x20d746` window and resolves the imported `ceres::Solve` and
`Problem::RemoveParameterBlock` calls. Its exact formula is:

```text
stage1 = mat3(context+0x38) * (source_x, source_y, 1)
stage1 = stage1 * f32(solved_scalar)
stage2 = mat3(context+0x40) *
         (stage1 - (context+0x20)[+0x24,+0x28,+0x2c])
final record+0x08/+0x0c/+0x10 = stage2
```

## Runtime Packets

The solve-only probe omits the hot `AddResidualBlock` breakpoint so the render
can complete. It records each callback frame at:

- `0x20ca14`: callback entry;
- `0x20d611`: immediately before `ceres::Solve`;
- `0x20d616`: immediately after `ceres::Solve` when that stop is recorded;
- `0x20d6b6`: after the first selected-triple writes;
- `0x20d737`: after the second selected-triple writes; and
- `0x20d8ac`: callback return.

The report contains `1,229` unique solve/write groups. All `1,229` have the
pre-Solve stop and both later triple-write stops. `907` also have a directly
paired post-Solve stop; `322` do not, so those `322` are excluded from claims
that specifically require the post-call breakpoint. They remain valid for
pre-Solve versus first-write comparison because the static window proves the
first-write snapshot reads the unchanged post-Solve scalar.

## Result

Across the `1,229` admitted solve/write groups:

| Observation | Result |
|---|---:|
| Pre-Solve scalar range | `[375.336883545, 4561.289550781]` |
| Solved scalar range | `[375.336883545, 4561.289550781]` |
| Solve changed scalar | `279` groups |
| Solve left scalar bit-identical | `950` groups |
| Delta range | `[-83.406289073, +157.786128388]` |
| Largest absolute delta | `157.786128388` |
| Final `record+0x10 == f32(solved scalar)` | `1229 / 1229` |
| Second transform changed the first triple | `0 / 1229` |

Every captured pre-Solve and solved scalar lies within the admitted mode-0
Triangulator bounds `[200.0, 640000.0]`. In all `907` directly paired
post-Solve packets, the post-call scalar equals the scalar later read by the
first triple-write block, while the record triple is still unchanged at the
post-call stop.

For all `1,229` groups, the first write's `record+0x10` exactly equals
`f32(solved scalar)`. The second transform leaves the complete 12-byte triple
bit-identical to the first transform under this run. The final selected record
therefore carries a concrete solved ray-depth scalar in `record+0x10` on this
path, and the already-admitted parent range scan consumes that field.

## Boundary

This evidence admits:

- live `ceres::Solve` execution in the `0x20ca00` callback;
- nonzero solve adjustments for `279` captured groups;
- bounded runtime solved-value examples;
- post-Solve materialization into owner-record `+0x08/+0x0c/+0x10`; and
- `record+0x10` as the final float32 solved ray-depth scalar for every captured
  group in this run.

It does not admit:

- public physical units or public calibration/LRI/protobuf names;
- stable counts, ranges, or deltas across focal tiers, bodies, or renders;
- that every candidate receives a residual or reaches Solve;
- that selected sentinel skips are terminal for their shared solve/output;
- the semantic public names of `record+0x08/+0x0c`;
- downstream image/source contribution; or
- reducer closure or final acceptance/rejection.

This result does not need an immediate four-focal or second-body matrix: the
mechanism and installed write formula are binary-defined, while the admitted
numeric distribution is explicitly Unit-1 `28mm` only. A risk-based Unit-2 or
tele rerun becomes necessary only before generalizing the distribution or
body/focal invariance.

## Verification

Commands:

```bash
bash tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_solve_output_only_28mm.sh
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py
```

Runtime verifier output:

```text
frames=10 completed=10
groups=1229 paired_post=907 missing_post=322
solve_changed=279 solve_unchanged=950
pre_range=[375.336883545,4561.289550781]
solved_range=[375.336883545,4561.289550781]
delta_range=[-83.406289073,157.786128388] max_abs=157.786128388
final_triple_z=f32(solved_scalar) all_groups
second_transform=exact_no_change all_groups
```
