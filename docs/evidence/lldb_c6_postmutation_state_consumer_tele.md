# LLDB Evidence: Tele C6 Post-Mutation State Consumer

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

The prior mutation-identity proof showed that the constructed `ctx+0xa0`
object reaches the `0x3c8f90` mutation routine and that the tracked key-15 /
C6 item is inactive by the later `0x3b2143` context walk. The follow-up
candidate-consumer probe excluded one plausible route, `0x3c9540 -> 0xe6c30`,
but did not test the immediate post-mutation caller path itself.

This probe answers the narrower question: does the immediate caller path after
`0x3c8f90` consume the constructed `ctx+0xa0` object and write derived state
back to the owning context under complete canonical tele bridge HDR renders?

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris`.

## Repo-Local Probe

Reusable harness:

- [c6_postmutation_state_consumer_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_state_consumer/c6_postmutation_state_consumer_probe.py)

LLDB scripts:

- [c6_postmutation_state_consumer_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_state_consumer/c6_postmutation_state_consumer_70mm.lldb)
- [c6_postmutation_state_consumer_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_state_consumer/c6_postmutation_state_consumer_150mm.lldb)

Raw rerunnable outputs are under ignored
`runs/c6_postmutation_state_consumer/`. Both runs produced completed
`10432 x 7824` HDR outputs and JSON reports:

- `runs/c6_postmutation_state_consumer/c6_postmutation_state_consumer_70mm.json`
- `runs/c6_postmutation_state_consumer/c6_postmutation_state_consumer_150mm.json`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_postmutation_state_consumer/c6_postmutation_state_consumer_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_postmutation_state_consumer/c6_postmutation_state_consumer_150mm.lldb
```

## Instrumented Sites

| Site | Probe name | Why included |
|---:|---|---|
| `0x3b20fe` | `post_mutation_ctx_a0_accessor_call` | immediate post-mutation call to the `ctx+0xa0` accessor |
| `0x3b2103` | `post_accessor_object_load` | load from the returned `ctx+0xa0` field address |
| `0x3b2111` | `container_item_vector_accessor_call` | call to the container item-vector accessor |
| `0x3b2143` | `item_vector_key_getter` | key getter during the item-vector walk |
| `0x3b21d9` | `derived_state_write_call` | call that writes scalar/flag into the derived state object |
| `0x3b21ec` | `context_c8_store` | store of the derived state object to context `+0xc8` |
| `0x3b2207` | `derived_state_code_call` | call that reads the derived state object |
| `0x3b2213` | `context_4b0_store` | store of the derived code to context `+0x4b0` |

## Static Context

Static inspection bounds the local helper semantics used by this path:

- `0x3c6ac0` is a direct `owner/context+0xa0` field accessor. See
  [bundle_lldb_owner_f0_helper_surface_static_classification.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_owner_f0_helper_surface_static_classification.md).
- `0xe78d0` returns `container+0x10`, the begin/end pair base used by the
  caller's item-vector walk.
- `0xe6cf0` returns the dword at `container+0x44`.
- `0x40b000` writes `esi` to state `+0x0` and low `dl` to state `+0x4`.
- `0x40b0e0` reads that state object and returns a small code that the caller
  converts into the value stored at context `+0x4b0`.

The relevant caller sequence is:

- call `0x3c6ac0`
- load `ctx+0xa0`
- load the object's first slot as the container
- call `0xe78d0` and walk the `0x10`-stride item vector
- call `0xf2720` per item at `0x3b2143`
- classify item keys through `0xf6c60`
- classify `container+0x44` through `0xe6cf0` / `0xf6c60`
- write derived state through `0x40b000`
- store the state object to context `+0xc8`
- derive and store a code to context `+0x4b0`

## Runtime Result

Both tele runs completed with process status `0`.

| Site | `70mm` hits | `150mm` hits |
|---:|---:|---:|
| `0x3b20fe` | `1` | `1` |
| `0x3b2103` | `1` | `1` |
| `0x3b2111` | `1` | `1` |
| `0x3b2143` | `11` total / `1` key-15 | `11` total / `1` key-15 |
| `0x3b21d9` | `1` | `1` |
| `0x3b21ec` | `1` | `1` |
| `0x3b2207` | `1` | `1` |
| `0x3b2213` | `1` | `1` |

The context object shape matched the prior candidate-consumer probe:

| Captured field | `70mm` | `150mm` |
|---|---:|---:|
| object first slot points to container | yes | yes |
| container item-vector byte span `+0x10..+0x18` | `176` | `176` |
| implied `0x10`-stride entries | `11` | `11` |
| container `+0x44` | `8` | `8` |
| container `+0x284` | `2` | `2` |
| container `+0x288 == +0x290` | yes | yes |

The key-15 / C6 item observation at the live `0x3b2143` walk:

| Field | `70mm` | `150mm` |
|---|---:|---:|
| key | `15` | `15` |
| item `+0x30` active byte | `0` | `0` |
| item `+0x58/+0x5c` pair | `(-1, -1)` | `(-1, -1)` |
| item `+0x100` | `3` | `3` |

The derived-state write path also matched in both tele seeds:

| State observation | `70mm` | `150mm` |
|---|---:|---:|
| `0x3b21d9` input `esi` | `3` | `3` |
| `0x3b21d9` low byte of `edx` | `1` | `1` |
| state object after `0x40b000`, field `+0x0` | `3` | `3` |
| state object after `0x40b000`, field `+0x4` | `1` | `1` |
| `context+0xc8` old value before store | `0` | `0` |
| `context+0x4b0` queued value at `0x3b2213` | `5` | `5` |

## Proven Facts

- The immediate post-mutation caller path consumes the constructed
  `ctx+0xa0` object in both canonical tele bridge HDR runs.
- That path walks the same eleven-entry container item vector shape previously
  captured in the scoped negative `0x3c9540 -> 0xe6c30` probe.
- Key `15` / C6 is observed exactly once in that post-mutation walk in each
  tele run, and it is inactive at item `+0x30 = 0`.
- The path writes derived state object fields `+0x0 = 3` and `+0x4 = 1`, stores
  that state object to context `+0xc8`, and queues context `+0x4b0 = 5` in both
  tele runs.
- Therefore, the constructed `ctx+0xa0` object does have a proven live
  post-mutation state-classification consumer under canonical tele bridge HDR.

## Non-Conclusions

- This does not prove C6 contributes to final image output.
- This does not prove C6 is globally unused.
- This does not prove the `0x3c90a5` mutation is terminal.
- This does not prove that context `+0xc8` or `+0x4b0` affects final merge
  acceptance or rejection.
- This does not exclude alternate C6 routes before the mutation, outside this
  post-mutation state-classification path, or outside the focused/tested
  `0xf2720` callsites.
- This does not assign public semantic names to `ctx+0xa0`, the container
  fields, item `+0x30`, item `+0x60`, context `+0xc8`, or context `+0x4b0`.
