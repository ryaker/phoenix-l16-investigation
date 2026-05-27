# Bundle + LLDB Global Read-Context Ancestry Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet,
complete render ancestry census at read-context branch sites `0x3d4842` and
`0x3d4864`.

This document follows:

- `bundle_lldb_owner_f0_global_route_census.md`
- `bundle_lldb_owner_f0_global_post_route_families.md`
- `bundle_lldb_owner_f0_global_rowcache_segments.md`

Static body classification for these parent chains is covered separately by
`bundle_lldb_owner_f0_parent_chain_static_classification.md`.

Those earlier proofs bound the global branch-site caller families, immediate
post-route families, and full-render row-cache segment reachability. This probe
adds full-render caller-parent chain counts for the same branch sites. It is a
structural ancestry proof, not a final-output proof.

It proves:

- all four canonical ancestry runs completed with exit status `0`
- every observed branch hit still preserved the same parent/context destination
  equality checks:
  `output_context == parent_3d01b0_rbp - 0x108`,
  `context+0x10 == parent rbp-0x148 output descriptor`, and
  `parent context+0x10 == context+0x10`
- every observed hit still fell into the same caller set
  `{0x3d0732, 0x3d084d, 0x3ecc5a}` and active callable slot set
  `{0x3ec960, 0x3e4a80}`
- caller `0x3d0732` returned upward through parent chain prefix
  `0x3b07a9 -> 0x41a8d3 -> 0x3adfce -> 0x280e -> external`
- caller `0x3d084d` returned upward through parent chain prefix
  `0x3bb822 -> 0x3adfce -> 0x280e -> external`
- caller `0x3ecc5a` returned upward through parent chain prefix
  `0x374cf3 -> 0x3665da -> 0x365f50 -> 0x3ec7df -> 0x3eca4b -> 0x3d4842`,
  with some packets continuing into another nested read-context stack below
  that `0x3d4842`

It also proves a caution:

- exact branch hit totals at `0x3d4864` are instrumentation/run specific at the
  few-hit level. The earlier global route census and this ancestry census both
  completed and preserve the same caller/slot/equality sets, but their direct
  branch hit totals differ slightly. Do not promote exact hit totals from these
  hot breakpoint runs into universal merge semantics.

It does not prove:

- public semantic names for the parent-chain bodies
- final file or display output semantics
- final contributor acceptance, rejection, or suppression policy
- that the observed parent chains are exhaustive outside the tested canonical
  bridge HDR quartet

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
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_ancestry_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_ancestry_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_ancestry_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_global_route_ancestry_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`:

- `owner_f0_global_route_ancestry_28mm.json`
- `owner_f0_global_route_ancestry_35mm.json`
- `owner_f0_global_route_ancestry_70mm.json`
- `owner_f0_global_route_ancestry_150mm.json`

The HDR outputs from these validation runs also live under ignored
`runs/owner_f0_read_context_route/`.

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Runtime Method

The LLDB scripts create pending `libcp.dylib` breakpoints before launch:

- `0x3d4842` = active-callable branch before `0x3d4e10`
- `0x3d4864` = direct branch before `0x3d4e10`

The callback records the same packet fields as the global route census and adds
two full-render count maps:

- `caller_parent_chain_counts`: branch, caller, active slot, and the libcp
  stack frames above the caller after parent `0x3d01b0`
- `full_stack_prefix_counts`: the first twelve stack-frame VAs, with external
  frames explicitly labeled `external`

Samples are capped at `64`, but count maps continue for the full render.

## Runtime Summary

Exact counts below are this evidence run's counts. They are not promoted as
universal constants because hot breakpoint hit totals drift slightly across
instrumented runs.

| Zoom | Exit | Total branch hits | Active branch hits | Direct branch hits | Caller set | Slot set | Context checks |
|---|---:|---:|---:|---:|---|---|---|
| `28mm` | `0` | `1167` | `396` | `771` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1167/1167` all true |
| `35mm` | `0` | `1469` | `330` | `1139` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1469/1469` all true |
| `70mm` | `0` | `1355` | `317` | `1038` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `1355/1355` all true |
| `150mm` | `0` | `335` | `107` | `228` | `0x3d0732`, `0x3d084d`, `0x3ecc5a` | `0x3ec960`, `0x3e4a80` | `335/335` all true |

## Parent-Chain Families

The caller-parent chain counts expose two broad structural classes.

### Owner-cache / Direct-render Parent Chain

The `0x3d0732` exact-size family returns through:

```text
0x3d0732 -> 0x3b07a9 -> 0x41a8d3 -> 0x3adfce -> 0x280e -> external
```

The `0x3d084d` owner-cache rescale family returns through:

```text
0x3d084d -> 0x3bb822 -> 0x3adfce -> 0x280e -> external
```

Observed counts in this ancestry run:

| Zoom | `0x3d0732` active | `0x3d0732` direct | `0x3d084d` active | `0x3d084d` direct |
|---|---:|---:|---:|---:|
| `28mm` | `300` | `0` | `48` | `164` |
| `35mm` | `234` | `516` | `48` | `118` |
| `70mm` | `221` | `515` | `48` | `126` |
| `150mm` | `63` | `93` | `20` | `24` |

### Visible-`src1` Nested Parent Chain

The visible-`src1` family returns through this common prefix:

```text
0x3ecc5a -> 0x374cf3 -> 0x3665da -> 0x365f50 -> 0x3ec7df -> 0x3eca4b -> 0x3d4842
```

Some packets continue below that nested `0x3d4842` into another read-context
stack. This means the observed visible-`src1` route is layered and can be nested
inside another `0x3d01b0` branch-site path. It is not proven to be final output.

Observed counts in this ancestry run:

| Zoom | Active common prefix | Active nested continuation | Direct common prefix | Direct nested continuation |
|---|---:|---:|---:|---:|
| `28mm` | `44` | `4` | `532` | `75` |
| `35mm` | `46` | `2` | `460` | `45` |
| `70mm` | `44` | `4` | `331` | `66` |
| `150mm` | `21` | `3` | `98` | `13` |

## Count Drift Boundary

This ancestry run and the earlier global route census agree on the durable
structural facts:

- same canonical quartet
- complete render exit status `0`
- same caller set
- same active slot set
- all parent/context equality checks true

They do not agree exactly on all hot direct-branch hit totals. The safe
interpretation is that these LLDB hot-breakpoint counts are evidence-run counts.
They are useful for coverage and family discovery, but they are not a public
algorithmic constant.

## Interpretation Boundary

This proof narrows "downstream row-image/final policy" by showing that the
classified read-context families continue into a small set of parent chains, and
that visible `src1` can be nested inside another read-context route. It does not
close the final policy blocker because it does not prove the final file/display
sink or the final contributor acceptance/rejection decision.
