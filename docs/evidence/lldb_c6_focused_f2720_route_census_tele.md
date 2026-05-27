# LLDB Evidence: Focused Tele C6 `0xf2720` Callsite Census

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

Earlier probes proved that tele key `15` / C6 is constructed active at
`item+0x30 = 1`, is later cleared at `libcp+0x3c90a5`, and is filtered at two
tested candidate loops with post-mutation `object+0x30 = 0`.

This focused census asks a narrower routing question:

Which selected direct static calls to `0xf2720`, the item-key getter for
`item+0x60`, actually see key `15` during canonical tele bridge HDR renders,
and what is the observed active byte at those sites?

This is route-census evidence. It is not terminality proof and it is not proof
of image-buffer contribution.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness:

- [c6_route_census_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census/c6_route_census_probe.py)

LLDB scripts:

- [c6_route_census_focus_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census/c6_route_census_focus_70mm.lldb)
- [c6_route_census_focus_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_route_census/c6_route_census_focus_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/c6_route_census/`.
Both focused runs produced completed `311M` HDR outputs and JSON reports:

- `runs/c6_route_census/c6_route_census_focus_70mm.json`
- `runs/c6_route_census/c6_route_census_focus_150mm.json`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_route_census/c6_route_census_focus_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_route_census/c6_route_census_focus_150mm.lldb
```

## Selected Callsite Set

The static direct-call inventory found `58` direct `call 0xf2720` sites in the
installed `libcp.dylib`. A broad all-site run was too expensive for first-pass
LLDB instrumentation, so the admitted runtime runs used a focused set of `24`
sites selected from already-known C6-adjacent paths:

```text
0x1a8e00 0x1a8e21 0x1a8e5f 0x1a8eff 0x1a8f1c 0x1a8f5a
0x1bdbab 0x1bdbdd
0x22eeb7 0x22eecf 0x22eeeb
0x22f717 0x22f72f 0x22f74b
0x3b2143
0x3c9043 0x3c9098
0x3f30ca 0x3f3104
0x402df7 0x402e30 0x402e3d
0x40d18d 0x40d219
```

Each breakpoint records:

- the direct callsite VA
- the item pointer passed in `rdi`
- `item+0x60` key
- `item+0x30` active byte
- `item+0x58/+0x5c` pair
- `item+0x100` type field
- a stack sample for key `15` hits

## Runtime Result

The `70mm` and `150mm` reports are identical for key `15` under the focused
site set.

| Site | Static neighborhood | Key `15` active-byte observations per tele run |
|---:|---|---:|
| `0x1bdbab` | key-vector helper; calls `0xf2720`, compares key against an int vector | `1` hit with active `1`, `7` hits with active `0` |
| `0x1bdbdd` | same helper; appends key when absent | `1` hit with active `1`, `7` hits with active `0` |
| `0x3c9043` | mutation body pre-gate key read | `1` hit with active `1` |
| `0x3c9098` | mutation body key-15 clear test immediately before `0x3c90a5` | `1` hit with active `1` |
| `0x3b2143` | grouping scan site | `1` hit with active `0` |
| `0x402df7` | `FusionCacheBayer` selector scan key read | `1` hit with active `0` |
| `0x40d219` | later grouping/count site with active-byte check after key/group reads | `4` hits with active `0` |

The following selected sites had runtime hits but no key `15` in either tele
run:

```text
0x1a8e00 0x1a8e21 0x1a8e5f
0x22eeb7 0x22eecf 0x22eeeb
0x22f717 0x22f72f 0x22f74b
0x3f30ca 0x3f3104
0x40d18d
```

The following selected sites had zero runtime hits in both focused tele runs:

```text
0x1a8eff 0x1a8f1c 0x1a8f5a
0x402e30 0x402e3d
```

No selected site hit its `4096`-hit cap, and both reports had zero item-read
errors.

## Proven Facts

- The focused 24-site `0xf2720` callsite census completed successfully at both
  canonical tele seeds.
- The `70mm` and `150mm` key-15 results are identical under this focused scope.
- Key `15` / C6 is observed at the mutation body with active byte `1`, matching
  the prior mutation-watch proof.
- Key `15` / C6 is also observed at `0x1bdbab` and `0x1bdbdd` once per tele
  run while active byte is still `1`.
- Static context for `0x1bdbab` / `0x1bdbdd` shows a key-vector membership /
  append helper around direct key reads; this proves key-list participation,
  not image-buffer contribution or merge acceptance.
- Later selected key-15 observations at `0x3b2143`, `0x402df7`, and
  `0x40d219` all see active byte `0`.
- The selected stereo-side getter sites `0x3f30ca` and `0x3f3104` had no key-15
  hits, matching the existing stereo-candidate gate proof that key `15` skips
  before those getter callsites under canonical tele bridge HDR.

## Non-Conclusions

- This does not prove the `0x3c90a5` mutation is terminal.
- This does not prove C6 contributes to or is excluded from the final image.
- This does not prove the consumer semantics of the key-vector helper reached
  through `0x1bdbab` / `0x1bdbdd`.
- This does not exclude non-`0xf2720` C6 routes.
- This does not cover all 58 static direct `0xf2720` callsites.
- This does not identify public semantic names for `item+0x30`, `item+0x60`,
  `item+0x58/+0x5c`, or the selected helper bodies.
