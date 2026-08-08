# Evidence: Prefusion `0x20ca00` Solve Output Discriminators

## Scope

This note extends the earlier Unit-1 `28mm`
`0x20ca00` solve-output proof with two risk-based discriminator runs:

- Unit-1 canonical `70mm`, to test a tele focal tier; and
- Unit-2 exact-focal `35mm`, to test the second physical calibration body.

Both runs use the same lightweight solve-only LLDB harness: callback entry,
pre/post `ceres::Solve`, first post-Solve triple write, second triple write,
and callback return. The hot `AddResidualBlock` breakpoint remains disabled so
the renders complete.

This is runtime solved-value / record-materialization evidence for two
additional discriminators. It is not a four-focal distribution proof, not
all-candidate behavior, not shared-solve terminality for skipped sentinel
pairs, not image/source-contribution proof, not reducer closure, and not final
acceptance/rejection.

## Artifacts

- Runtime callback:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_solve_output_probe.py`
- Reusable verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py`
- New LLDB scripts:
  - `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_solve_output_only_unit1_70mm.lldb`
  - `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_solve_output_only_unit2_35mm.lldb`
- New runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_solve_output_discriminators.sh`
- Raw reports/logs/HDR outputs:
  `runs/prefusion_20ca00_solve_output_only/`

Static custody and formula verifiers reused by this evidence:

- `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py`
- `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py`

## Inputs

| Run | Unit scope | LRI |
|---|---|---|
| Unit-1 `70mm` | canonical Unit-1 tele focal | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| Unit-2 `35mm` | exact-focal second-body representative | `/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri` |

Both runs used profile `3`, export format `3` HDR, and `--no-auto-lris`.
Both wrote complete `10432 x 7824` Radiance HDR outputs and exited with status
`0`.

## Verifier Changes

The verifier still preserves the original strict Unit-1 `28mm` checks for
`prefusion_20ca00_solve_output_only_28mm`.

For other stems, it validates the structural invariants without importing
Unit-1 `28mm` distribution assumptions:

- clean LLDB process completion and Radiance HDR output;
- complete callback frames with no probe errors;
- required stop sites for each solve/write group;
- selected record address identity from `record_begin + 4 * (5 * gate_index) + 8`;
- finite local scalar values;
- post-Solve first write has `record+0x10 == f32(solved_scalar)`; and
- optional post-Solve stops preserve the record triple before the write sites.

It reports, rather than fails on, pre-solve bound differences and second-transform
differences for discriminator runs.

## Results

| Run | Frames | Groups | Post-stop paired | Solve changed | Solve unchanged |
|---|---:|---:|---:|---:|---:|
| Unit-1 `28mm` baseline | `10` | `1,229` | `907` | `279` | `950` |
| Unit-1 `70mm` discriminator | `10` | `3,456` | `2,432` | `317` | `3,139` |
| Unit-2 `35mm` discriminator | `10` | `1,589` | `1,150` | `886` | `703` |

| Run | Pre-solve range | Solved range | Delta range | Max abs delta |
|---|---:|---:|---:|---:|
| Unit-1 `28mm` baseline | `[375.336883545, 4561.289550781]` | `[375.336883545, 4561.289550781]` | `[-83.406289073, 157.786128388]` | `157.786128388` |
| Unit-1 `70mm` discriminator | `[920.944091797, 575332.875000000]` | `[920.944091797, 640000.000000000]` | `[-20228.724055280, 637427.757568359]` | `637427.757568359` |
| Unit-2 `35mm` discriminator | `[2486.733886719, 1525610.500000000]` | `[2486.733886719, 640000.000000000]` | `[-1056325.843621250, 632748.622070312]` | `1056325.843621250` |

The old Unit-1 `28mm` run remains exact:

| Run | Pre `record+0x10 == f32(pre)` | First write `record+0x10 == f32(solved)` | Second transform changed triple | Final `record+0x10 == f32(solved)` |
|---|---:|---:|---:|---:|
| Unit-1 `28mm` baseline | `1229 / 1229` | `1229 / 1229` | `0 / 1229` | `1229 / 1229` |
| Unit-1 `70mm` discriminator | `0 / 3456` | `3456 / 3456` | `3456 / 3456` | `0 / 3456` |
| Unit-2 `35mm` discriminator | `1589 / 1589` | `1589 / 1589` | `0 / 1589` | `1589 / 1589` |

The Unit-1 `70mm` discriminator proves the same first-write materialization
surface is live in a tele focal tier, but it also proves that the Unit-1
`28mm` final-z equality must not be generalized: every captured Unit-1 `70mm`
group changes the selected triple in the second transform, and no final
`record+0x10` exactly equals `f32(solved_scalar)`.

The Unit-2 `35mm` discriminator proves the same first-write materialization
surface on the second physical body. Six pre-solve local scalars exceed the old
Unit-1 mode-0 upper bound of `640000.0`, while all captured solved scalars are
within `[200.0, 640000.0]`. This is reported only as runtime-distribution
evidence; it does not prove constructor mode, public units, or public
calibration names.

## Verification

Commands:

```bash
bash tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_solve_output_discriminators.sh
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_range_custody_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py --stem prefusion_20ca00_solve_output_only_unit1_70mm
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_solve_output_runtime.py --stem prefusion_20ca00_solve_output_only_unit2_35mm
```

Verifier output for the two new runs:

```text
report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_20ca00_solve_output_only/prefusion_20ca00_solve_output_only_unit1_70mm.json
frames=10 completed=10
groups=3456 paired_post=2432 missing_post=1024
solve_changed=317 solve_unchanged=3139
pre_range=[920.944091797,575332.875000000]
solved_range=[920.944091797,640000.000000000]
delta_range=[-20228.724055280,637427.757568359] max_abs=637427.757568359
mode0_bound_outside_pre=0 solved=0
pre_triple_z=f32(pre_scalar) 0/3456
first_triple_z=f32(solved_scalar) 3456/3456
second_transform_changed=3456/3456
final_triple_z=f32(solved_scalar) 0/3456
final_z_range=[920.944213867,640000.062500000]
```

```text
report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_20ca00_solve_output_only/prefusion_20ca00_solve_output_only_unit2_35mm.json
frames=10 completed=10
groups=1589 paired_post=1150 missing_post=439
solve_changed=886 solve_unchanged=703
pre_range=[2486.733886719,1525610.500000000]
solved_range=[2486.733886719,640000.000000000]
delta_range=[-1056325.843621250,632748.622070312] max_abs=1056325.843621250
mode0_bound_outside_pre=6 solved=0
pre_triple_z=f32(pre_scalar) 1589/1589
first_triple_z=f32(solved_scalar) 1589/1589
second_transform_changed=0/1589
final_triple_z=f32(solved_scalar) 1589/1589
final_z_range=[2486.733886719,640000.000000000]
```

## Safe Conclusion

The `0x20ca00` post-Solve first-write materialization surface is not only a
Unit-1 `28mm` artifact. It is now observed in one Unit-1 tele run and one
exact-focal Unit-2 run, with nonzero solve adjustments in both.

The narrower Unit-1 `28mm` fact that the final selected `record+0x10` equals
the solved scalar remains scoped to the runs where the second transform leaves
the triple unchanged. Unit-1 `70mm` refutes generalizing that final-z equality:
the first write stores the solved scalar, then the second transform changes the
final triple in every captured group.

This strengthens the internal solve/output custody path while keeping the
blocker open: public units/LRI names, all-candidate behavior, shared-solve
terminality, downstream image/source contribution, reducer closure, and final
acceptance/rejection are still unproven.
