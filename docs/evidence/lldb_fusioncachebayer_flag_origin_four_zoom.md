# LLDB Evidence: `FusionCacheBayer+0x18` Flag Origin Across Four Zooms

## Scope

This proof extends the static
`FusionCacheBayer+0x18` constructor-origin boundary into four-zoom runtime
evidence. It proves that the canonical bridge HDR quartet reaches:

`PipelineCache ctor -> 0x406960 -> 0x4064c0 -> 0x402d20 -> object+0x18 write -> 0x4066fc constructor branch -> PipelineCache+0x1d8 store`

It also proves the runtime split:

- `28mm` / `35mm`: `0x402e78` writes flag `1`; constructor branch reads flag
  `1`; field `+0x20` is constructed.
- `70mm` / `150mm`: `0x402e78` writes flag `0`; constructor branch reads
  flag `0`; field `+0x20` construction store has zero hits.

This is constructor / flag-origin custody evidence. It does not name the public
semantics of the flag, the upstream collection, the optional `+0x20` object, or
the final merge/reducer / acceptance policy.

## Artifacts

- Static companion proof:
  [bundle_proof_fusioncachebayer_flag_origin_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_fusioncachebayer_flag_origin_static.md)
- Runtime helper:
  [fusioncachebayer_flag_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_probe.py)
- Runtime scripts:
  [fusioncachebayer_flag_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_28mm.lldb),
  [fusioncachebayer_flag_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_35mm.lldb),
  [fusioncachebayer_flag_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_70mm.lldb),
  [fusioncachebayer_flag_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_150mm.lldb)
- Runtime JSON reports:
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_28mm.json`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_35mm.json`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_70mm.json`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_150mm.json`
- Runtime HDR outputs:
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_28mm.hdr`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_35mm.hdr`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_70mm.hdr`,
  `runs/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_150mm.hdr`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_28mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_35mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_flag_origin/fusioncachebayer_flag_origin_150mm.lldb
```

All four reruns completed successfully after `/Volumes/Base Photos` was
mounted again on 2026-05-26. Each run exited `0` and wrote a
`10432x7824` HDR output.

## Probe Method

The runtime helper installs breakpoints at:

- `0x3eab4c`: `PipelineCache` constructor call to `0x406960`.
- `0x402d89`: direct-zero branch inside base initializer.
- `0x402d90`: scan-path entry inside base initializer.
- `0x402e6e`: sentinel comparison before `setne al`.
- `0x402e78`: write of `al` to object byte `+0x18`.
- `0x402e7c`: immediately after the flag write.
- `0x4066fc`: later constructor branch on object byte `+0x18`.
- `0x406774`: nonzero-flag path store to object field `+0x20`.
- `0x3eab58`: store-before site for the `PipelineCache+0x1d8` holder.
- `0x3eab5e`: store-after site for the `PipelineCache+0x1d8` holder.

The callbacks filter base-initializer samples to frames returning to
`0x4064ed`, and constructor-branch samples to frames returning to `0x3eab51`.
This keeps the proof scoped to the `PipelineCache`-constructed
`FusionCacheBayer` object.

The helper now refuses to overwrite the main JSON evidence report when no
constructor call is captured; failed launches write a separate `*.failed`
report instead.

## Runtime Summary

`472 decimal == 0x1d8`.

| Seed | `r15d` at `0x402e78` | flag written at `0x402e78` | flag after write | flag at `0x4066fc` | `+0x20` store hits | holder offset |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` / `L16_02130` | `1` | `1` | `1` | `1` | `1` | `472` |
| `35mm` / `L16_03041` | `1` | `1` | `1` | `1` | `1` | `472` |
| `70mm` / `L16_03434` | `16` | `0` | `0` | `0` | `0` | `472` |
| `150mm` / `L16_02285` | `16` | `0` | `0` | `0` | `0` | `472` |

Per-run summaries:

- `28mm`: `accepted_constructor_calls=1`, `accepted_base_init_events=4`,
  `accepted_constructor_branches=1`, `accepted_field20_stores=1`,
  `accepted_pipelinecache_stores=2`, `flags_written_at_0x402e78=[1]`,
  `flags_read_after_0x402e78=[1]`, `flags_at_constructor_branch_0x4066fc=[1]`.
- `35mm`: `accepted_constructor_calls=1`, `accepted_base_init_events=4`,
  `accepted_constructor_branches=1`, `accepted_field20_stores=1`,
  `accepted_pipelinecache_stores=2`, `flags_written_at_0x402e78=[1]`,
  `flags_read_after_0x402e78=[1]`, `flags_at_constructor_branch_0x4066fc=[1]`.
- `70mm`: `accepted_constructor_calls=1`, `accepted_base_init_events=4`,
  `accepted_constructor_branches=1`, `accepted_field20_stores=0`,
  `accepted_pipelinecache_stores=2`, `flags_written_at_0x402e78=[0]`,
  `flags_read_after_0x402e78=[0]`, `flags_at_constructor_branch_0x4066fc=[0]`.
- `150mm`: `accepted_constructor_calls=1`, `accepted_base_init_events=4`,
  `accepted_constructor_branches=1`, `accepted_field20_stores=0`,
  `accepted_pipelinecache_stores=2`, `flags_written_at_0x402e78=[0]`,
  `flags_read_after_0x402e78=[0]`, `flags_at_constructor_branch_0x4066fc=[0]`.

## Proven Facts

- The canonical four-zoom bridge HDR quartet reaches the
  `PipelineCache` constructor call to `0x406960` and the scoped
  `0x402d20` base initializer.
- In all four runs, the `0x402d20` base initializer reaches the scan path,
  not the direct-zero branch.
- At `28mm` and `35mm`, `r15d` is `1` at the flag write, `0x402e78` writes
  `1`, the byte reads back as `1` at `0x402e7c`, and `0x4066fc` later consumes
  flag `1`.
- At `70mm` and `150mm`, `r15d` is sentinel `16` at the flag write,
  `0x402e78` writes `0`, the byte reads back as `0` at `0x402e7c`, and
  `0x4066fc` later consumes flag `0`.
- The `PipelineCache` holder offset observed by the store-before/store-after
  probes is `472` / `0x1d8` in all four runs.
- The object stored through that holder already has the same flag value proven
  by the initializer and constructor-branch samples.
- The optional `FusionCacheBayer+0x20` construction/store site `0x406774`
  fires at `28mm` and `35mm`, and has zero hits at `70mm` and `150mm` under
  these complete bridge HDR runs.

## Safe Conclusion

The visible-`src2` `0x406a10` branch split is now tied to constructor-origin
state rather than an opaque runtime branch:

- `28mm` / `35mm`: constructor base init selects non-sentinel key `1`, writes
  `FusionCacheBayer+0x18 = 1`, constructs `FusionCacheBayer+0x20`, and later
  visible-`src2` `0x406a10` takes the proven flag-`1` branch.
- `70mm` / `150mm`: constructor base init leaves sentinel `16`, writes
  `FusionCacheBayer+0x18 = 0`, does not construct `FusionCacheBayer+0x20` on
  the tested constructor path, and later visible-`src2` `0x406a10` takes the
  proven flag-`0` branch.

This closes the origin/custody of the `+0x18` branch selector. It does not
close the public meaning of the flag, the LRI origin of the upstream collection,
or the merge/reducer / final acceptance policy.

## Remaining Unknowns

- Public semantic meaning of the non-sentinel key `1` versus sentinel `16`.
- Public semantic meaning of fields `+0x58` and `+0x60` on the scanned objects.
- Public semantic name / LRI origin of the upstream collection scanned by
  `0x402d20`.
- Public semantic name of the optional `FusionCacheBayer+0x20` object.
- Whether this constructor-time flag is purely a source-adapter mode selector
  or contributes to later merge-quality policy beyond the already bounded
  visible-`src2` descriptor branch.
