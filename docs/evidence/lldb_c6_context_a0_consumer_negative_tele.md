# LLDB Evidence: Tele C6 Context `+0xa0` Candidate Consumer Negative

**Date:** 2026-05-27
**Status:** admitted scoped negative evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

The mutation-identity proof showed that the key-list/helper path constructs a
context object at `ctx+0xa0`, then the mutation routine `0x3c8f90` uses that
same context object before clearing tele key `15` / C6 at `0x3c90a5`.

Static inspection found a plausible downstream consumer candidate:

- `0x3c9540` reads `ctx+0xa0`
- if the object and first slot are non-null, it tail-jumps through `0x3c9578`
  into `0xe6c30`
- `0xe6c30` inspects container fields around `+0x284` / `+0x288` and returns a
  byte-like predicate

This probe tests whether that specific candidate route is live under complete
canonical tele bridge HDR renders.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris`.

## Repo-Local Probe

Reusable harness:

- [c6_context_a0_consumer_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_context_a0_consumer/c6_context_a0_consumer_probe.py)

LLDB scripts:

- [c6_context_a0_consumer_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_context_a0_consumer/c6_context_a0_consumer_70mm.lldb)
- [c6_context_a0_consumer_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_context_a0_consumer/c6_context_a0_consumer_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/c6_context_a0_consumer/`.
Both runs produced completed `10432 x 7824` HDR outputs and JSON reports:

- `runs/c6_context_a0_consumer/c6_context_a0_consumer_70mm.json`
- `runs/c6_context_a0_consumer/c6_context_a0_consumer_150mm.json`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_context_a0_consumer/c6_context_a0_consumer_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_context_a0_consumer/c6_context_a0_consumer_150mm.lldb
```

## Instrumented Sites

| Site | Probe name | Why included |
|---:|---|---|
| `0x3b20cd` | `constructor_call_3c9370` | verifies constructor path is reached |
| `0x3c9401` | `constructor_store_after_ctx_a0` | captures context `+0xa0` store |
| `0x3b20d2` | `after_constructor_call` | captures post-constructor context state |
| `0x3c8f90` | `mutation_entry_ctx_a0` | verifies mutation routine consumes the same context object |
| `0x3c9540` | `consumer_entry_3c9540` | candidate downstream context-object consumer |
| `0x3c9558` | `consumer_identity_before` | candidate non-null identity path |
| `0x3c956f` | `consumer_container_load` | candidate container load before tail jump |
| `0x3c9578` | `consumer_tailjmp_e6c30` | candidate tail jump into `0xe6c30` |
| `0xe6c30` | `e6c30_entry` | candidate predicate helper entry |
| `0xe6cd6` | `e6c30_return` | candidate predicate helper return byte |
| `0x3c957d` | `consumer_empty_fallback` | candidate empty-object fallback |

## Runtime Result

Both tele runs completed with process status `0`.

| Site family | `70mm` hits | `150mm` hits |
|---|---:|---:|
| constructor call `0x3b20cd` | `1` | `1` |
| context store `0x3c9401` | `1` | `1` |
| post-constructor `0x3b20d2` | `1` | `1` |
| mutation entry `0x3c8f90` | `1` | `1` |
| candidate consumer `0x3c9540` | `0` | `0` |
| candidate internal sites `0x3c9558` / `0x3c956f` / `0x3c9578` / `0x3c957d` | `0` | `0` |
| candidate helper `0xe6c30` / `0xe6cd6` | `0` | `0` |

The positive constructor/mutation hits show the probe was attached to the live
C6 context path. The zero-hit candidate sites therefore mean only this scoped
fact: the `0x3c9540 -> 0xe6c30` route was not reached in these two complete
canonical tele bridge HDR renders.

The re-captured context object shape matched across the two tele seeds:

| Captured field | `70mm` | `150mm` |
|---|---:|---:|
| context `+0xa0` populated before mutation | yes | yes |
| object slot `+0x0` points to container | yes | yes |
| container item-vector byte span `+0x10..+0x18` | `176` | `176` |
| implied `0x10`-stride entries | `11` | `11` |
| container `+0x44` | `8` | `8` |
| container `+0x284` | `2` | `2` |
| container `+0x288 == +0x290` | yes | yes |

These structural fields are runtime observations for the tested tele seeds, not
public semantic names.

## Proven Facts

- The candidate route `0x3c9540 -> 0xe6c30` has zero hits under complete
  `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled.
- The same runs do hit the constructor and mutation custody sites, including
  context `+0xa0` population and the `0x3c8f90` mutation entry.
- Therefore, `0x3c9540 -> 0xe6c30` is excluded as a live downstream
  context-object consumer under these tested tele conditions.
- The context object's first slot points to a container whose captured
  item-vector span is `176` bytes, consistent with eleven `0x10`-stride entries
  in both tele seeds.

## Non-Conclusions

- This does not prove there are no downstream consumers of the constructed
  context object.
- This does not prove the `0x3c90a5` mutation is terminal.
- This does not prove C6 contributes to final image output.
- This does not prove C6 is globally unused.
- This does not exclude non-focused direct `0xf2720` callsites.
- This does not exclude non-`0xf2720` C6 routes.
- This does not assign public semantic names to `ctx+0xa0`, the container
  fields, or the item-vector entries.
