# Bundle + LLDB Owner `+0xf0` Direct-Branch Post-Route Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet, first
owner `+0xf0` descriptor captured at `0x3ecac3` in each render.

This document follows `bundle_lldb_owner_f0_route_census.md`. The census proved
that sibling direct branch `0x3d4864` is live for the first captured owner
`+0xf0` descriptor at `28mm`, `70mm`, and `150mm`, but it intentionally did not
stop each direct packet at the later selected-cache `0x3d08ce -> 0x36f800`
call. This proof closes that immediate post-route handoff for the first
owner-matching direct branch on the zooms where such a branch exists.

It proves:

- the first owner-matching direct branch at `28mm`, `70mm`, and `150mm` reaches
  `0x3d08ce`, the selected-cache call site into `0x36f800`
- at that post-route stop, `rsi` equals the same temporary descriptor previously
  captured as the direct branch's `context+0x10` destination
- the direct branch keeps the same selected-cache caller `0x3d084d` and active
  callable slot `0x3ec960`
- `35mm` completed the direct-post probe with no owner-matching direct branch,
  consistent with the first-owner census

It does not prove:

- every direct branch in the render, only the first owner-matching direct branch
  that the probe follows
- every owner instance after the first `0x3ecac3` setup
- worker math inside `0x36f800`
- public names for the offset / scale pairs or pixel format
- final output/display semantics
- final merge acceptance / rejection policy

## Tooling Boundary

The reusable probe code lives in:

- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_probe.py`

The direct-post LLDB entrypoints live in:

- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_direct_post_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_direct_post_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_direct_post_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_direct_post_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`:

- `owner_f0_direct_post_28mm.json`
- `owner_f0_direct_post_35mm.json`
- `owner_f0_direct_post_70mm.json`
- `owner_f0_direct_post_150mm.json`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Runtime Method

The probe first records the exact owner and owner `+0xf0` descriptor at
`0x3ecac3`. It then accepts only the first later branch packet where:

- the stop site is direct branch `0x3d4864`
- the local source pair points back to the exact setup owner

For that accepted direct packet, it installs a post-route breakpoint at
`0x3d08ce` and accepts the post-route stop only on the same thread when
`rbp-0x70` equals the direct branch's captured `context+0x10` destination
descriptor.

## Runtime Summary

| Zoom | Direct handoff accepted | Post `0x3d08ce` reached | Handoff caller | Handoff slot | `rsi == temp == context+0x10` |
|---|---:|---:|---|---|---|
| `28mm` | `1` | yes | `0x3d084d` | `0x3ec960` | true |
| `35mm` | `0` | no direct handoff | n/a | n/a | n/a |
| `70mm` | `1` | yes | `0x3d084d` | `0x3ec960` | true |
| `150mm` | `1` | yes | `0x3d084d` | `0x3ec960` | true |

## Post-Route Packets

| Zoom | Direct ROI | Temp descriptor at handoff | Requested output before `0x36f800` | Offset pair | Scale pair |
|---|---:|---:|---:|---:|---:|
| `28mm` | `[0,380,436,844]` | `436x464`, stride `436` | `543x575`, stride `543` | `[0.0,2.82208251953125]` | `[0.7975460290908813,0.7975460290908813]` |
| `35mm` | n/a | n/a | n/a | n/a | n/a |
| `70mm` | `[0,0,518,518]` | `518x518`, stride `518` | `551x551`, stride `551` | `[0.0,0.0]` | `[0.935251772403717,0.935251772403717]` |
| `150mm` | `[1075,1277,1618,1820]` | `543x543`, stride `543` | `575x575`, stride `575` | `[2.4100341796875,2.4244384765625]` | `[0.935251772403717,0.935251772403717]` |

First-hit offset / scale values are live samples. They must not be promoted to
public semantic names without producer/consumer proof.

## Interpretation Boundary

This proof removes the specific caveat that the direct branch had not been
followed to the selected-cache `0x36f800` call. It does not prove global route
completeness. The safe claim is only that, for the first captured owner
`+0xf0` descriptor, the first direct branch on `28mm`, `70mm`, and `150mm`
continues to the same immediate `0x3d08ce -> 0x36f800` handoff shape already
known from the active-branch route. `35mm` remains a no-direct-branch observation
under this first-owner probe.
