# Wide-Tier `0x218bc4` Path Divergence

## Question

Why do complete canonical `28mm` and `35mm` runs have zero direct hits at
`0x218bc4`, while sampled tele sentinel pairs reach that guard and branch to
`0x218cb8`?

## Reusable artifacts

- `tools/lldb_probes/prefusion_wide_218bc4_path_census/`
- ignored logs and HDRs under
  `runs/prefusion_wide_218bc4_path_census/`
- prior tele branch proof:
  `bundle_lldb_prefusion_sentinel_score_guard_branch_step_tele.md`
- prior complete wide sentinel/guard census:
  `bundle_lldb_prefusion_sentinel_guard_direct_census_wide.md`

Reproduce:

```bash
sh tools/lldb_probes/prefusion_wide_218bc4_path_census/run_wide.sh
```

## Installed branch topology

Parent body `0x216f60` dispatches on its local
`SparseMirrorAngleOptimizer::CostFunction` value:

```text
0x2178ed  load CostFunction
0x2178f3  test
0x2178f5  je   0x2179b7       # value 0
0x2178fb  cmp  1
0x217916  jne  0x217e8b       # "wrong cost function supplied"
0x21791c  CostFunction 1 arm
```

The two valid arms install distinct RTTI-named callbacks and distinct score
helpers:

| CostFunction | Callback RTTI | Vtable `+0x30` | Direct helper |
|---:|---|---:|---:|
| `0` | `SparseMirrorAngleOptimizer::optimize(...)::$_1` | `0x218e20` | `0x218f7c -> 0x218b30` |
| `1` | `SparseMirrorAngleOptimizer::optimize(...)::$_2` | `0x219210` | `0x219375 -> 0x218940` |

`0x218bc4` is inside helper `0x218b30`, so it exists only on the
CostFunction-`0` callback family. Helper `0x218940` is a separate body ending
at `0x218b2e`; it cannot fall through into `0x218b30`.

The verifier pins the selector bytes, both RTTI records and operator slots, and
both direct-call targets.

## Wide runtime result

Both count-only runs exit `0`, write populated `10432x7824` Radiance HDR, and
show:

| Focal | `0x216f60` | CostFunction-1 construct/dispatch | `$_2` callback | `$_2 -> 0x218940` call | All CostFunction-0 sites | `0x218bc4` |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `4` | `4 / 4` | `544` | `4356` | `0` | `0` |
| `35mm` | `4` | `4 / 4` | `544` | `4356` | `0` | `0` |

The CostFunction-0 zero set includes its construction site `0x2179d9`,
dispatch `0x217a42`, callback `0x218e20`, helper call `0x218f7c`, and helper
entry `0x218b30`.

Thus wide does not reach `0x218bc4` because it selects a different
CostFunction callback/helper family before the guard, not because wide
sentinels encounter an unobserved earlier branch inside `0x218b30`.

## Tele comparison and admission boundary

The prior tele branch-step proof places sampled `70mm` and `150mm` sentinel
pairs in the CostFunction-0 stack
`0x218e20 -> 0x218f7c -> 0x218b30 -> 0x218bc4`, where `(-1,-1)` takes the
nonpositive skip to `0x218cb8`.

Admit to `CLM-PREFUSION-002`:

- canonical wide selects CostFunction `1`, callback `$_2`, helper `0x218940`;
- the `0x218bc4` guard belongs exclusively to sibling CostFunction `0`,
  callback `$_1`, helper `0x218b30`; and
- this upstream callback-family split explains the complete wide zero-hit
  result.

This closes checklist C5's wide-path divergence. It does not name the public
semantic labels of CostFunction values `0` and `1`, and it does not prove that
wide sentinel records are globally terminal outside this optimizer family.
