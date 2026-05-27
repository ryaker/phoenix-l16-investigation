# Bundle + LLDB Global Read-Context Branch Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet,
complete render hit census at read-context branch sites `0x3d4842` and
`0x3d4864`.

This document follows:

- `bundle_lldb_owner_f0_read_context_route.md`
- `bundle_lldb_owner_f0_route_census.md`
- `bundle_lldb_owner_f0_direct_branch_post_route.md`

Those earlier probes were intentionally gated to the first captured owner
`+0xf0` descriptor. This probe removes that first-owner gate and records every
hit at the two read-context branch sites during complete bridge HDR renders.

It proves:

- all four canonical renders completed with exit status `0`
- every hit at `0x3d4842` / `0x3d4864` preserved the same three context
  relationships: closure `context` equals parent `0x3d01b0` `rbp-0x108`,
  `context+0x10` equals the parent output descriptor saved at `rbp-0x148`, and
  the parent context destination equals that same descriptor
- globally, these branch sites are not limited to the first-owner selected-cache
  route
- across the four canonical bridge HDR seeds, the branch-site census observed
  exactly three caller VAs after parent `0x3d01b0`: `0x3d0732`, `0x3d084d`, and
  `0x3ecc5a`
- across the four canonical bridge HDR seeds, the active callable packet slot
  observed at these branch sites was either `0x3ec960` or `0x3e4a80`
- the first-owner selected-cache route remains real, but it is only one member
  of the broader branch-site family

It does not prove:

- public semantic names for `0x3d0732`, `0x3d084d`, `0x3ecc5a`, `0x3ec960`, or
  `0x3e4a80`
- immediate post-route family classification; this is covered by follow-up
  `bundle_lldb_owner_f0_global_post_route_families.md`
- parent-chain ancestry above those caller families; this is covered by
  follow-up `bundle_lldb_owner_f0_global_route_ancestry.md`
- downstream row-cache segment reachability after the `0x3d084d -> 0x36f800`
  owner-cache rescale route; this is covered by follow-up
  `bundle_lldb_owner_f0_global_rowcache_segments.md`
- public offset/scale/pixel-format semantics
- final output/display semantics
- final merge acceptance / rejection policy

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
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_census_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_census_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_census_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_census_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`:

- `owner_f0_global_route_census_28mm.json`
- `owner_f0_global_route_census_35mm.json`
- `owner_f0_global_route_census_70mm.json`
- `owner_f0_global_route_census_150mm.json`

The HDR outputs from these validation runs also live under ignored
`runs/owner_f0_read_context_route/`.

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Runtime Method

The LLDB scripts create pending `libcp.dylib` breakpoints before launch:

- `0x3d4842` = active-callable branch before `0x3d4e10`
- `0x3d4864` = direct branch before `0x3d4e10`

The callback records every hit without filtering to the first owner pointer. It
groups hits by branch, caller after parent `0x3d01b0`, active callable slot,
context destination shape, source-owner pointer, and the three parent/context
equality checks.

Stored packet samples are capped at `256`, but hit counts and unique-key counts
continue for the full render. The sample cap was reached at all four zooms. The
unique packet cap was reached at `28mm`, `35mm`, and `70mm`, but not at
`150mm`.

## Runtime Summary

| Zoom | Exit | Total hits | Active branch `0x3d4842` | Direct branch `0x3d4864` | Callers | Slots | Context checks |
|---|---:|---:|---:|---:|---|---|---|
| `28mm` | `0` | `1169` | `396` | `773` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1169/1169` all true |
| `35mm` | `0` | `1466` | `330` | `1136` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1466/1466` all true |
| `70mm` | `0` | `1348` | `317` | `1031` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1348/1348` all true |
| `150mm` | `0` | `332` | `107` | `225` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `332/332` all true |

The repeated `all true` checks are:

- `output_context == parent_3d01b0_rbp - 0x108`
- `context_dest == parent_output_descriptor_local_rbp_minus_0x148`
- `parent_context_dest == context_dest`

## Branch / Caller / Slot Groups

| Zoom | Branch | Caller after `0x3d01b0` | Active callable slot | Hits |
|---|---|---:|---:|---:|
| `28mm` | `active_callable_then_3d4e10` | `0x3d0732` | `0x3ec960` | `300` |
| `28mm` | `active_callable_then_3d4e10` | `0x3d084d` | `0x3ec960` | `48` |
| `28mm` | `active_callable_then_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `48` |
| `28mm` | `direct_3d4e10` | `0x3d084d` | `0x3ec960` | `168` |
| `28mm` | `direct_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `605` |
| `35mm` | `active_callable_then_3d4e10` | `0x3d0732` | `0x3ec960` | `234` |
| `35mm` | `active_callable_then_3d4e10` | `0x3d084d` | `0x3ec960` | `48` |
| `35mm` | `active_callable_then_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `48` |
| `35mm` | `direct_3d4e10` | `0x3d0732` | `0x3ec960` | `511` |
| `35mm` | `direct_3d4e10` | `0x3d084d` | `0x3ec960` | `119` |
| `35mm` | `direct_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `506` |
| `70mm` | `active_callable_then_3d4e10` | `0x3d0732` | `0x3ec960` | `221` |
| `70mm` | `active_callable_then_3d4e10` | `0x3d084d` | `0x3ec960` | `48` |
| `70mm` | `active_callable_then_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `48` |
| `70mm` | `direct_3d4e10` | `0x3d0732` | `0x3ec960` | `512` |
| `70mm` | `direct_3d4e10` | `0x3d084d` | `0x3ec960` | `123` |
| `70mm` | `direct_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `396` |
| `150mm` | `active_callable_then_3d4e10` | `0x3d0732` | `0x3ec960` | `63` |
| `150mm` | `active_callable_then_3d4e10` | `0x3d084d` | `0x3ec960` | `20` |
| `150mm` | `active_callable_then_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `24` |
| `150mm` | `direct_3d4e10` | `0x3d0732` | `0x3ec960` | `92` |
| `150mm` | `direct_3d4e10` | `0x3d084d` | `0x3ec960` | `21` |
| `150mm` | `direct_3d4e10` | `0x3ecc5a` | `0x3e4a80` | `112` |

`28mm` is the only canonical seed in this census where direct branch
`0x3d4864` did not appear with caller `0x3d0732`.

## Interpretation Boundary

This proof replaces the older first-owner/direct-post boundary for these two
branch sites. The branch-site caller/slot families are now bounded under the
four canonical bridge HDR seeds.

The remaining blocker is not "do these branch sites have other caller/slot
families under the tested quartet." Follow-up
`bundle_lldb_owner_f0_global_post_route_families.md` classifies the immediate
post-route behavior for those caller families. Follow-up
`bundle_lldb_owner_f0_global_route_ancestry.md` bounds their parent-chain
ancestry and records that exact hot direct-branch counts are evidence-run
counts, not algorithm constants. Later follow-up
`bundle_lldb_owner_f0_global_rowcache_segments.md` covers full-render row-cache
segment reachability. The remaining blockers are public semantics, downstream
row-image/final policy, and the final acceptance/rejection policy that
determines whether contributor influence is accepted or suppressed.
