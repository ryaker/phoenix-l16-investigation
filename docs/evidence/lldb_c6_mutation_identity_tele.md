# LLDB Evidence: Tele C6 Mutation Identity Chain

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

Earlier evidence proved three related facts:

- tele key `15` / C6 is constructed active at `item+0x30 = 1`
- the active byte is cleared at `libcp+0x3c90a5`
- selected later candidate loops see C6 inactive and filter it

The focused `0xf2720` route census then found active C6 key-list-helper hits at
`0x1bdbab` / `0x1bdbdd`, but that census did not itself prove the exact
identity chain across constructor, mutation, immediate post-store state, and
later context walks.

This probe answers that narrower identity question.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris`.

## Repo-Local Probe

Reusable harness:

- [c6_mutation_identity_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_mutation_identity/c6_mutation_identity_probe.py)

LLDB scripts:

- [c6_mutation_identity_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_mutation_identity/c6_mutation_identity_70mm.lldb)
- [c6_mutation_identity_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_mutation_identity/c6_mutation_identity_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/c6_mutation_identity/`.
Both runs produced completed `311M` HDR outputs and JSON reports:

- `runs/c6_mutation_identity/c6_mutation_identity_70mm.json`
- `runs/c6_mutation_identity/c6_mutation_identity_150mm.json`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_mutation_identity/c6_mutation_identity_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_mutation_identity/c6_mutation_identity_150mm.lldb
```

## Instrumented Sites

| Site | Probe name | Why included |
|---:|---|---|
| `0x3b20cd` | `constructor_call_3c9370` | call into the constructor path |
| `0x3b20d2` | `after_constructor_call` | post-constructor context state |
| `0x3c9401` | `constructor_store_after_ctx_a0` | context `+0xa0` store point after `0x1bd270` construction |
| `0x3c8f90` | `mutation_entry_ctx_a0` | mutation routine entry reading context `+0xa0` |
| `0x1bdbab` | `keylist_getter_first` | key-list helper key getter |
| `0x1bdbdd` | `keylist_getter_append` | key-list helper append key getter |
| `0x3c9043` | `mutation_loop_key_first` | mutation-loop key getter |
| `0x3c9098` | `mutation_loop_key_guard` | key-15 guard immediately before clear |
| `0x3c90a5` | `mutation_store_before` | byte-store instruction before execution |
| `0x3c90a9` | `mutation_store_after` | immediate post-store instruction |
| `0x3b2143` | `post_mutation_context_walk` | later context walk key getter |

## Runtime Result

Both tele runs completed with process status `0`.

| Fact | `70mm` result | `150mm` result |
|---|---:|---:|
| tracked key-15 item pointers | one pointer | one pointer |
| `0x1bdbab` total hits / key-15 hits | `88 / 8` | `88 / 8` |
| `0x1bdbdd` total hits / key-15 hits | `88 / 8` | `88 / 8` |
| `0x3c9043` total hits / key-15 hits | `11 / 1` | `11 / 1` |
| `0x3c9098` total hits / key-15 hits | `11 / 1` | `11 / 1` |
| `0x3c90a5` total hits / key-15 hits | `1 / 1` | `1 / 1` |
| `0x3c90a9` total hits / key-15 hits | `11 / 1` | `11 / 1` |
| `0x3b2143` total hits / key-15 hits | `11 / 1` | `11 / 1` |

The same tracked item pointer in each tele run is observed with:

| Stage | Active byte |
|---|---:|
| `0x1bdbab` active helper hit | `1` |
| `0x1bdbdd` active helper hit | `1` |
| `0x3c9043` mutation-loop key read | `1` |
| `0x3c9098` mutation-loop guard read | `1` |
| `0x3c90a5` before store executes | `1` |
| `0x3c90a9` immediately after store executes | `0` |
| `0x3b2143` later context walk | `0` |

Context custody is also consistent:

- `0x3b20cd` sees context `+0xa0 = 0` before the constructor call.
- `0x3c9401` stores the constructed `0x1bd270` object into context `+0xa0`.
- `0x3b20d2` sees the same context `+0xa0` value after constructor return.
- `0x3c8f90` enters the mutation routine with the same context `+0xa0` value.

## Static Context

Static inspection of helper `0x1bdb60` shows `0x1bdbab` / `0x1bdbdd` are
key-vector membership / append key reads. The helper iterates item records,
reads `item+0x60` through `0xf2720`, scans an output integer vector for that
key, and appends missing keys. The helper itself does not inspect pixels,
image descriptors, or active byte `item+0x30`.

Static inspection of `0x3c9370` shows it allocates and constructs a `0x90`
object through `0x1bdc70` / `0x1bd270`, then stores that object into context
`+0xa0`. The immediately following caller path invokes `0x3c8f90`, whose body
contains the `0x3c9043` / `0x3c9098` key reads and the `0x3c90a5` active-byte
clear.

## Proven Facts

- The active key-list-helper C6 observations at `0x1bdbab` / `0x1bdbdd`, the
  mutation-loop observations at `0x3c9043` / `0x3c9098`, the store at
  `0x3c90a5`, the immediate post-store observation at `0x3c90a9`, and the later
  `0x3b2143` context-walk observation are all the same tracked key-15 item
  pointer within each tele run.
- The same key-15 item pointer is active (`item+0x30 = 1`) before the
  `0x3c90a5` store and inactive (`item+0x30 = 0`) immediately afterward.
- The `0x1bdb60` helper containing `0x1bdbab` / `0x1bdbdd` is a key-list
  construction helper. That helper body is bookkeeping, not an image-buffer
  operation.
- The key-list helper's output is attached to a constructed context object at
  context `+0xa0`, and the mutation routine later runs from that same context
  path.

## Non-Conclusions

- This does not prove C6 contributes to final image output.
- This does not prove C6 is globally unused.
- This does not prove the `0x3c90a5` mutation is terminal for all canonical
  bridge HDR C6 routes.
- This does not exclude non-focused direct `0xf2720` callsites.
- This does not exclude non-`0xf2720` C6 routes.
- This does not identify public semantic names for `item+0x30`, `item+0x60`,
  `item+0x58/+0x5c`, or the context `+0xa0` object.
