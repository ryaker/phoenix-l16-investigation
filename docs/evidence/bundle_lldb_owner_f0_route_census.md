# Bundle + LLDB Owner `+0xf0` Route-Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet, first
owner `+0xf0` descriptor captured at `0x3ecac3` in each render.

This document is a follow-up to
`bundle_lldb_owner_f0_read_context_route.md`. That earlier proof intentionally
captured only the first accepted owner `+0xf0` route. This probe keeps both
branch breakpoints active for the first captured owner descriptor and censes all
owner-matching branch packets that occur during the render.

It proves:

- the sibling direct branch at `0x3d4864` is live for the first captured owner
  `+0xf0` descriptor at `28mm`, `70mm`, and `150mm`
- `35mm` produced only the active-callable branch in this first-owner census
- every accepted owner-matching packet in this census, across all four zooms,
  used active callable slot `0x3ec960`
- every accepted owner-matching packet in this census returned from parent
  `0x3d01b0` to caller `0x3d084d`, inside the selected-cache read/rescale body
- every accepted packet preserved the context relationships previously proven
  for the first route: closure context equals parent `rbp-0x108`, `context+0x10`
  equals the parent output descriptor saved at `rbp-0x148`, and parent context
  destination equals the accepted context destination
- the previous "first captured route uses `0x3d4842`" statement remains true
  but must not be generalized into "all owner `+0xf0` routes use `0x3d4842`"

By itself, this census did not prove:

- every owner `+0xf0` route for the whole render lifetime
- every later owner instance after the first `0x3ecac3` setup
- a separate post-route stop at `0x3d08ce` for every direct-branch packet
- public semantic names for the offset / scale pairs or pixel format
- final output/display semantics
- final merge acceptance / rejection policy

Follow-up evidence `bundle_lldb_owner_f0_direct_branch_post_route.md` proves
the first owner-matching direct branch at `28mm`, `70mm`, and `150mm` reaches
the selected-cache `0x3d08ce -> 0x36f800` call with `rsi` equal to the same
temporary descriptor captured as `context+0x10`; `35mm` still has no
owner-matching direct branch under the first-owner probe.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harnesses live in the repo:

- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_probe.py`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_census_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`:

- `owner_f0_route_census_28mm.json`
- `owner_f0_route_census_35mm.json`
- `owner_f0_route_census_70mm.json`
- `owner_f0_route_census_150mm.json`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Runtime Method

The probe first stops at `0x3ecac3` and records the exact owner pointer and
owner `+0xf0` descriptor. It then keeps breakpoints active at both branch sites:

- `0x3d4842` = active-callable branch before `0x3d4e10`
- `0x3d4864` = direct branch before `0x3d4e10`

For each branch hit, the packet is accepted only if the local source pair points
back to the exact owner captured at setup. Accepted packets record the parent
`0x3d01b0` frame, the caller after `0x3d01b0`, the active callable slot, the
context destination descriptor, and the context equality checks.

All four renders completed normally with process status `0`. The census cap was
not reached in any run.

## Runtime Summary

| Zoom | Total branch hits | Owner-matching accepted | Active branch `0x3d4842` | Direct branch `0x3d4864` | Caller(s) | Slot(s) |
|---|---:|---:|---:|---:|---|---|
| `28mm` | `1163` | `4` | `1` | `3` | `0x3d084d` | `0x3ec960` |
| `35mm` | `1469` | `1` | `1` | `0` | `0x3d084d` | `0x3ec960` |
| `70mm` | `1364` | `6` | `1` | `5` | `0x3d084d` | `0x3ec960` |
| `150mm` | `331` | `2` | `1` | `1` | `0x3d084d` | `0x3ec960` |

The rejected hits were branch hits whose local source pair did not point back to
the first captured owner. They are not evidence for or against later owner
instances.

## Accepted First-Owner Packets

| Zoom | Branch | Context destination shape | Parent ROI passed to `0x3d01b0` | Context equality checks |
|---|---|---:|---:|---|
| `28mm` | `active_callable_then_3d4e10` | `464x464`, stride `464` | `[380,1197,844,1661]` | all true |
| `28mm` | `direct_3d4e10` | `463x464`, stride `463` | `[789,1197,1252,1661]` | all true |
| `28mm` | `direct_3d4e10` | `464x463`, stride `464` | `[380,789,844,1252]` | all true |
| `28mm` | `direct_3d4e10` | `463x463`, stride `463` | `[789,789,1252,1252]` | all true |
| `35mm` | `active_callable_then_3d4e10` | `463x464`, stride `463` | `[368,297,831,761]` | all true |
| `70mm` | `active_callable_then_3d4e10` | `543x518`, stride `543` | `[454,0,997,518]` | all true |
| `70mm` | `direct_3d4e10` | `518x518`, stride `518` | `[0,0,518,518]` | all true |
| `70mm` | `direct_3d4e10` | `518x543`, stride `518` | `[0,454,518,997]` | all true |
| `70mm` | `direct_3d4e10` | `543x518`, stride `543` | `[933,0,1476,518]` | all true |
| `70mm` | `direct_3d4e10` | `543x543`, stride `543` | `[454,454,997,997]` | all true |
| `70mm` | `direct_3d4e10` | `543x543`, stride `543` | `[933,454,1476,997]` | all true |
| `150mm` | `active_callable_then_3d4e10` | `543x543`, stride `543` | `[1075,1277,1618,1820]` | all true |
| `150mm` | `direct_3d4e10` | `543x543`, stride `543` | `[1075,798,1618,1341]` | all true |

The repeated `all true` checks are:

- `output_context == parent_3d01b0_rbp - 0x108`
- `context_dest == parent_output_descriptor_local_rbp_minus_0x148`
- `parent_context_dest == context_dest`

## Interpretation Boundary

This proof narrows the open route question. It shows that the sibling direct
branch is real under the first-owner census, but the accepted packets still
share the same selected-cache caller and active callable slot family. The
evidence therefore refutes any wording that upgrades the first route to "only
`0x3d4842` fires for owner `+0xf0`", while also refuting a broader leap that the
direct branch is a separate proven downstream merge policy.

Follow-up evidence `bundle_lldb_owner_f0_global_route_census.md` removes the
first-owner gate and bounds the complete-render branch-site caller/slot
families for `0x3d4842` / `0x3d4864` under the canonical quartet. Later
follow-ups classify the post-route families and full-render row-cache segment
reachability. Remaining blockers are public offset/scale/pixel-format
semantics, downstream row-image/final policy, and final acceptance/rejection.
