# Bundle + LLDB Global Read-Context Post-Route Family Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet,
first observed representative of each global read-context caller family after
branch sites `0x3d4842` / `0x3d4864`.

This document follows `bundle_lldb_owner_f0_global_route_census.md`, which
proved that complete canonical bridge HDR renders hit exactly three caller
families after parent `0x3d01b0` at the read-context branch sites:

- `0x3d0732`
- `0x3d084d`
- `0x3ecc5a`

This probe captures one runtime representative per caller family on each
canonical zoom and records the immediate post-route behavior. Static caller
disassembly is part of the proof because the post-route instruction stream is
determined by the caller return PC, not by whether the branch packet was
`0x3d4842` or `0x3d4864`.

It proves:

- all four canonical zooms captured all three caller families
- all captured handoff packets preserved the same parent/context destination
  equality checks proven by the global branch census
- caller `0x3d0732` is the exact-size path: after `0x3d01b0` returns, it jumps
  directly to `0x3d08dc` cleanup and does not call `0x36f800`
- caller `0x3d084d` is the owner-cache rescale path: it reaches
  `0x3d08ce -> 0x36f800`, with `rsi` equal to the captured temporary descriptor
  and `rdx` / `rcx` holding the offset / scale double pairs
- caller `0x3ecc5a` is the visible-`src1` post-route path: it reaches
  `0x3ecc74 -> 0x3edb80`, passes the requested output descriptor in `rdi`, and
  passes a wrapper in `rsi` whose wrapped descriptor is the captured
  `context+0x10` intermediate
- the immediate post-route family split is therefore bounded as:
  exact-size no-post-call cleanup, owner-cache `0x36f800` rescale, and
  visible-`src1` `0x3edb80` one-image normalization

It does not prove:

- public semantic names for the caller families
- that every direct-branch packet was separately stopped at its post-route site
- full-render leading/trailing row-cache segment reachability inside `0x36f800`,
  which is covered separately by `bundle_lldb_owner_f0_global_rowcache_segments.md`
- parent-chain ancestry above these caller families, which is covered
  separately by `bundle_lldb_owner_f0_global_route_ancestry.md`
- final file/display output semantics
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
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_post_family_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_post_family_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_post_family_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_post_family_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`:

- `owner_f0_global_post_family_28mm.json`
- `owner_f0_global_post_family_35mm.json`
- `owner_f0_global_post_family_70mm.json`
- `owner_f0_global_post_family_150mm.json`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Caller Boundary

The caller return PCs observed by the global census land in two static caller
bodies:

- `0x3d0732` and `0x3d084d` are both inside the `0x3d0650` owner-cache read /
  optional-rescale body.
- `0x3ecc5a` is inside the visible-`src1` wrapper body `0x3ecc10`.

The relevant post-call instruction streams are:

- `0x3d072d -> 0x3d01b0`; return at `0x3d0732`; immediate `jmp 0x3d08dc`
  cleanup.
- `0x3d0848 -> 0x3d01b0`; return at `0x3d084d`; compute offset / scale pairs;
  call `0x36f800` at `0x3d08ce`.
- `0x3ecc55 -> 0x3d01b0`; return at `0x3ecc5a`; build wrapper over
  `rbp-0x50`; call `0x3edb80` at `0x3ecc74`.

Because the post-route stream is keyed by the caller return PC, the static
classification applies to active and direct branch packets that share the same
caller PC. The runtime packets below capture one representative per caller
family per zoom.

## Runtime Summary

| Zoom | All families captured | Branch hits before stop | Post breakpoint hits |
|---|---|---:|---:|
| `28mm` | yes | `235` | `8` |
| `35mm` | yes | `184` | `11` |
| `70mm` | yes | `183` | `4` |
| `150mm` | yes | `59` | `6` |

The probe intentionally stops after all three families are captured; these are
not full-render hit counts.

## Captured Families

| Zoom | Family | Representative branch | Slot | Context destination shape | Post route |
|---|---|---|---:|---:|---|
| `28mm` | `0x3d0732` exact-size | `0x3d4842` | `0x3ec960` | `512x656` | no post call; `jmp 0x3d08dc` cleanup |
| `28mm` | `0x3d084d` owner-cache rescale | `0x3d4842` | `0x3ec960` | `464x436` | `0x3d08ce -> 0x36f800` |
| `28mm` | `0x3ecc5a` visible `src1` | `0x3d4842` | `0x3e4a80` | `265x265` | `0x3ecc74 -> 0x3edb80` |
| `35mm` | `0x3d0732` exact-size | `0x3d4842` | `0x3ec960` | `512x512` | no post call; `jmp 0x3d08dc` cleanup |
| `35mm` | `0x3d084d` owner-cache rescale | `0x3d4842` | `0x3ec960` | `463x464` | `0x3d08ce -> 0x36f800` |
| `35mm` | `0x3ecc5a` visible `src1` | `0x3d4842` | `0x3e4a80` | `265x265` | `0x3ecc74 -> 0x3edb80` |
| `70mm` | `0x3d0732` exact-size | `0x3d4842` | `0x3ec960` | `512x512` | no post call; `jmp 0x3d08dc` cleanup |
| `70mm` | `0x3d084d` owner-cache rescale | `0x3d4842` | `0x3ec960` | `543x518` | `0x3d08ce -> 0x36f800` |
| `70mm` | `0x3ecc5a` visible `src1` | `0x3d4842` | `0x3e4a80` | `265x265` | `0x3ecc74 -> 0x3edb80` |
| `150mm` | `0x3d0732` exact-size | `0x3d4842` | `0x3ec960` | `512x512` | no post call; `jmp 0x3d08dc` cleanup |
| `150mm` | `0x3d084d` owner-cache rescale | `0x3d4842` | `0x3ec960` | `543x543` | `0x3d08ce -> 0x36f800` |
| `150mm` | `0x3ecc5a` visible `src1` | `0x3d4842` | `0x3e4a80` | `297x297` | `0x3ecc74 -> 0x3edb80` |

Every captured handoff packet had these checks true:

- `output_context == parent_3d01b0_rbp - 0x108`
- `context_dest == parent_output_descriptor_local_rbp_minus_0x148`
- `parent_context_dest == context_dest`

The `0x3d084d` post packets additionally had:

- `matches_context_dest_descriptor == true`
- `rsi_matches_temp_descriptor == true`

The `0x3ecc5a` post packets additionally had:

- `matches_context_dest_descriptor == true`
- `wrapped_descriptor_matches_intermediate == true`

## Interpretation Boundary

This proof narrows the immediate post-route blocker. The branch-site
caller/slot families are no longer unclassified: the tested quartet shows an
exact-size owner-cache cleanup family, an owner-cache rescale family, and a
visible-`src1` one-image normalization family.

The remaining blocker is downstream and policy-level: public field names, final
output semantics, and the final contributor acceptance / suppression decision.
Parent-chain ancestry for these families is covered separately by
`bundle_lldb_owner_f0_global_route_ancestry.md`.
