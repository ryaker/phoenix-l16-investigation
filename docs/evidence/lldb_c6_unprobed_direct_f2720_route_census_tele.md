# LLDB Evidence: Remaining Direct `0xf2720` C6 Route Census

**Date:** 2026-05-28
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

The earlier focused C6 route census covered 24 selected direct calls to
`0xf2720`, the item-key getter for `item+0x60`. Static inventory identified 58
direct `call 0xf2720` sites in the installed `libcp.dylib`, leaving 34 direct
sites outside admitted runtime coverage.

This probe covers those remaining 34 direct callsites under the canonical
`70mm` and `150mm` bridge HDR renders.

This is route-census evidence. It is not terminality proof and it is not proof
of final image-buffer contribution or exclusion.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable shared harness:

- [c6_route_census_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census/c6_route_census_probe.py)

Chunked LLDB scripts and runner:

- [c6_route_census_unprobed_direct_70mm_a.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_a.lldb)
- [c6_route_census_unprobed_direct_70mm_b.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_b.lldb)
- [c6_route_census_unprobed_direct_150mm_a.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_a.lldb)
- [c6_route_census_unprobed_direct_150mm_b.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_b.lldb)
- [run_unprobed_direct.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census_unprobed_direct/run_unprobed_direct.sh)

Raw rerunnable outputs are under ignored
`runs/c6_route_census_unprobed_direct/`.

Admitted JSON reports:

- `runs/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_a.json`
- `runs/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_70mm_b.json`
- `runs/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_a.json`
- `runs/c6_route_census_unprobed_direct/c6_route_census_unprobed_direct_150mm_b.json`

Command:

```bash
bash tools/lldb_probes/c6_route_census_unprobed_direct/run_unprobed_direct.sh
```

LLDB/debugserver needed to run outside the sandbox. Sandboxed LLDB attempts
lost the debug connection before JSON reports were written; those failed
attempts are not cited as evidence.

## Selected Callsite Set

The focused proof covered 24 selected callsites. This proof covers the 34-site
set difference from the 58 static direct-call inventory.

Chunk A:

```text
0xdf8f3 0xe3273 0xe327e 0xe32f3 0xe4063 0xe5fd9
0xe6020 0xe609a 0xe680f 0xe688f 0xe69df 0xe6be0
0xe745f 0xe75f3 0xe7763 0xfb329 0xfb95f
```

Chunk B:

```text
0xfe5fc 0x144c80 0x145703 0x1459d9 0x1b7e82
0x1b7e8d 0x20b044 0x20b17d 0x227d5e 0x227d77
0x227e30 0x2280de 0x22819c 0x27d7ce 0x27db11
0x31bce0 0x31bd00
```

Coverage check:

```text
all static direct sites: 58
focused prior sites: 24
remaining sites covered here: 34
focused/remaining overlap: 0
missing from focused + remaining: 0
```

## Admission Checks

All four admitted reports satisfy:

- process log shows `exited with status = 0`
- HDR output was written
- JSON report was written
- `install.requested == install.installed == 17`
- `errors == []`
- no selected site had `disabled_at_cap == true`
- no selected site recorded item read errors

Therefore the `4096` site-hit cap did not narrow any admitted result in this
proof.

## Runtime Result

The `70mm` and `150mm` reports are identical for key `15` under the remaining
34-site direct-callsite set.

### Key `15` Observed

| Site | Key-15 observations per tele run | Active byte for key `15` | Key-15 stack shape |
|---:|---:|---:|---|
| `0xe327e` | `10` | all `1` | `0xe327e -> 0xe59ca -> 0x3c93b8 -> 0x3b20d2 -> 0x3b1c65` |
| `0xe32f3` | `1` | `1` | `0xe32f3 -> 0xe59ca -> 0x3c93b8 -> 0x3b20d2 -> 0x3b1c65` |
| `0xe4063` | `1` | `1` | `0xe4063 -> 0xe5f9b -> 0x3c93b8 -> 0x3b20d2 -> 0x3b1c65` |
| `0xe5fd9` | `1` | `1` | `0xe5fd9 -> 0x3c93b8 -> 0x3b20d2 -> 0x3b1c65` |
| `0xe6020` | `1` | `1` | `0xe6020 -> 0x3c93b8 -> 0x3b20d2 -> 0x3b1c65` |
| `0xe6be0` | `7` | all `0` | `0xe6be0 -> 0x1be990 -> 0x3f2fb2 -> 0x3f46eb -> 0x3b3016 -> 0x3b1c65` |

Every key-15 record above had `item+0x58/+0x5c = (-1,-1)` and
`item+0x100 = 3`.

### Runtime Hits With No Key `15`

These remaining direct callsites had runtime hits but no key `15` in either
tele run:

```text
0xdf8f3 0xe3273 0xe680f 0xe688f 0xe69df 0xe745f
0xe75f3 0xe7763 0xfb95f
0xfe5fc 0x145703 0x1459d9 0x20b044 0x20b17d
0x27d7ce 0x31bce0 0x31bd00
```

These remaining direct callsites had zero runtime hits in both tele runs:

```text
0xe609a 0xfb329
0x144c80 0x1b7e82 0x1b7e8d 0x227d5e 0x227d77
0x227e30 0x2280de 0x22819c 0x27db11
```

## Static Neighborhoods For Key-15 Sites

Local static context only supports helper-level labels:

- `0xe327e` and `0xe32f3` are inside helper body `0xe3240`. The body iterates a vector-like range, compares `0xf2720` keys from an existing entry and a candidate entry, calls `0xf3320`, and increments `r14+0x28` if the candidate key equals `r14+0x44`. Runtime stack places the key-15 hits immediately after the direct constructor path `0xe59a4 -> 0xf2770` calls `0xe3240` and returns to `0xe59ca`.
- `0xe4063` is inside helper body `0xe4000`. The local body reads an item key with `0xf2720` and searches a tree-like structure rooted at `r14+0x2a8` by comparing node field `+0x20` against that key. Runtime stack places the key-15 hit under the same `0xe52c0` caller family at return `0xe5f9b`.
- `0xe5fd9` and `0xe6020` are inside helper body `0xe52c0`. The local body checks `0xf3320`, reads item keys with `0xf2720`, allocates `0x28`-byte nodes, stores the key into node field `+0x1c`, and builds/searches a local tree. Runtime stack places the key-15 hits under caller return `0x3c93b8`.
- `0xe6be0` is inside helper body `0xe6ba0`, reached through the previously classified `0x1be970 -> 0xe6ba0` shared-object lookup path. The local body scans entries and compares both `0xf3320` and `0xf2720` results. Key `15` is observed here only with active byte `0`.

These labels are local mechanism descriptions. They do not identify public
semantic names or prove final image contribution/exclusion.

## Proven Facts

- The remaining 34 direct `0xf2720` callsites completed admitted runtime
  census runs under both canonical tele bridge HDR seeds.
- Together with the prior focused 24-site proof, all 58 statically enumerated
  direct `call 0xf2720` sites now have admitted tele runtime census coverage.
- The newly covered key-15-positive active sites are local constructor-adjacent
  key/container/tree materialization surfaces: `0xe327e`, `0xe32f3`,
  `0xe4063`, `0xe5fd9`, and `0xe6020`.
- The newly covered key-15-positive inactive site is `0xe6be0`, reached through
  the `0x1be970 -> 0xe6ba0` shared-object lookup path.
- Chunk B contributes no key-15 observations under either tele seed.

## Non-Conclusions

- This does not prove C6 contributes to or is excluded from the final image.
- This does not prove the `0x3c90a5` mutation is terminal.
- This does not exclude non-`0xf2720` routes.
- This does not prove whole-buffer terminality for the zero-filled
  ImagePyramid route.
- This does not identify public semantic names for `item+0x30`, `item+0x60`,
  `item+0x58/+0x5c`, `item+0x100`, or the helper bodies.
- This does not generalize beyond the tested canonical bridge HDR tele seeds.
