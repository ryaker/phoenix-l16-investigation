# Bundle + Runtime Proof: Prefusion `0x20ca00` Sentinel-Gate Local Effect

## Scope

This note extends the selected same-address gate-custody proofs by bounding the
instructions omitted when a selected full-sentinel destination takes
`0x20d363 -> 0x20d565`.

It combines:

- machine-checked installed-bundle bytes and imported-symbol resolution,
- the admitted Unit-1 positive packets at pair indices `5394` and `77`, and
- the admitted Unit-2 positive packet at pair index `12`.

The result is local to one candidate iteration inside `0x20ca00`. It is not a
claim that the whole Ceres problem is empty, that the pair is absent from every
other path, or that final image/source contribution is closed.

## Repo-Local Artifacts

- Static verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_gate_skip_effect_static.py`
- Post-solve formula verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py`
- Unit-1 selected runtime verifier:
  `verify_node_dest_20ca00_gate_selected_custody.py`
- Selected cross-unit runtime verifier:
  `verify_node_dest_20ca00_gate_crossunit_selected.py`
- Installed binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

The static verifier reads the Mach-O directly, checks instruction-window bytes
and a SHA-256 guard, decodes relative branch/call targets, and uses `otool -Iv`
to resolve the imported Ceres stubs. It does not trust prose disassembly.

## Deterministic Static Result

The installed bytes prove:

```text
0x20d35e: compare selected x lane with 0.0
0x20d363: jae 0x20d565

0x20d369..0x20d37e: selected y-lane load/comparison and same skip target
0x20d384..0x20d43c: keyed local-node lookup/allocation/insertion
0x20d43c..0x20d543: keyed lookup plus two coordinate-to-double record-write groups
0x20d54e..0x20d560: argument setup and call to imported
  ceres::Problem::AddResidualBlock(CostFunction*, LossFunction*, double*)

0x20d565: temporary copied-vector cleanup
0x20d59a..0x20d5e3: iterator advance / next copied pair
```

The skipped static interval is therefore `0x20d369..0x20d565`. The
`AddResidualBlock` call instruction at `0x20d560` lies inside that interval.

After the per-pair loop, the same function still constructs a
`ceres::Solver::Summary` at `0x20d5f0` and calls `ceres::Solve` at `0x20d611`.
Those post-loop calls are outside the selected pair's skip interval and can
operate on residuals added by other accepted pairs.

An independent Capstone/SHA verifier bounds the immediate post-solve write
shape without assigning public names. The destination triple is at
`[rbp-0x2c8] + 4 * [rbp-0x2d0] + 8`. A first 3x3 float transform from
`context+0x38` consumes two source scalars plus homogeneous `1`, scales all
three results by the solved double at `rbp-0xc8`, and writes the triple at
`0x20d6a8..0x20d6b1`. A second 3x3 transform from `context+0x40` subtracts the
three-float origin at `(context+0x20)+0x24..+0x2c` and overwrites the same
triple at `0x20d729..0x20d732`. `0x20d741` then calls imported
`ceres::Problem::RemoveParameterBlock` for the solved scalar.

This section is static formula and destination-shape proof. The separate
`bundle_static_prefusion_20ca00_record_range_custody.md` byte-pinned proof now
binds the destination to the captured owner's `0x14`-stride record vector and
its `+0x10` field to the immediate parent positive-range consumer. Runtime
liveness/values and later consumers remain separate questions.

## Runtime Join

The existing strict runtime verifiers prove three selected full-sentinel
destination pairs reach `0x20d363` with `CF=0` and step directly to `0x20d565`:

| Unit | Zoom | Pair index | Gate bytes | Step |
|---|---|---:|---|---|
| Unit-1 | `28mm` | `5394` | `000080bf000080bf` | `0x20d363 -> 0x20d565` |
| Unit-1 | `70mm` | `77` | `000080bf000080bf` | `0x20d363 -> 0x20d565` |
| Unit-2 | `35mm` | `12` | `000080bf000080bf` | `0x20d363 -> 0x20d565` |

Joining runtime branch execution to the byte-verified static interval proves
that those selected pair iterations do not execute the local keyed-node
materialization, coordinate record writes, or one-parameter
`ceres::Problem::AddResidualBlock` call in `0x20d369..0x20d560`.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_gate_skip_effect_static.py
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
window=0x20d344..0x20d565 sha256=59eb24308fab2f0598293aca8d394b6f77b36f6ffd6eb469806b7fecadfd3be4
x_gate=0x20d363->0x20d565 y_gate=0x20d37e->0x20d565
skipped_interval=0x20d369..0x20d565
skipped_call=0x20d560->0x555e64 __ZN5ceres7Problem16AddResidualBlockEPNS_12CostFunctionEPNS_12LossFunctionEPd
post_loop=0x20d5f0->0x555e5e,0x20d611->0x555e58
```

The selected Unit-1 and cross-unit runtime verifiers must also pass unchanged.

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_postsolve_formula_static.py
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
window=0x20d603..0x20d746 sha256=0435b52a251a08987e765033a8f561e3f0e81dc839747b80282d650fff24c592
triple_addr=[rbp-0x2c8]+4*[rbp-0x2d0]+8
stage1=mat3(context+0x38)*(source_xy,1)*f32(f64[rbp-0xc8])
stage2=mat3(context+0x40)*(stage1-(context+0x20)[0x24:0x30])
calls=0x20d611->0x555e58,0x20d741->0x555e7c
```

## Proven Facts

1. The `0x20d363` x-lane branch and `0x20d37e` y-lane branch both target
   `0x20d565` in the installed binary.
2. The interval bypassed by the x-lane branch contains local keyed-node
   materialization, two coordinate record-write groups, and the
   one-parameter `ceres::Problem::AddResidualBlock` call at `0x20d560`.
3. Three admitted selected full-sentinel pair iterations across both physical
   units execute that exact skip branch.
4. Those selected iterations therefore add no residual through this local
   `0x20d560` call and perform none of the skipped local record writes.
5. The function can still solve residuals contributed by other accepted pair
   iterations; post-loop `ceres::Solve` remains live code outside this skip.

## Safe Conclusion

For the three admitted selected representatives, full-sentinel rejection has a
concrete local effect: the pair is excluded from the keyed record-write and
`AddResidualBlock` path in this `0x20ca00` iteration.

This closes the direct local Ceres-residual consequence of those branch samples
only. It does not prove all-pairs terminality, absence from other consumers,
downstream image/source contribution, reducer closure, or final
acceptance/rejection.
