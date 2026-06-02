# LLDB Evidence: State Helper `0x23c5f0` Exit Snapshot Across Four Zooms

## Scope

This proof follows:

- [bundle_static_state_family_full_body_call_surface.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_state_family_full_body_call_surface.md)
- [lldb_state_helpers_23c5f0_f33d0_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helpers_23c5f0_f33d0_four_zoom.md)

It instruments the live State helper `0x23c5f0` at three points:

- `0x23c5f0`: helper entry.
- `0x23d392`: immediately after the static direct call
  `0x23d38d -> 0xf33d0`.
- `0x23d5a8`: normal exit path immediately before the local tree destroy call
  to `0x200260`.

This is local helper-field and local-tree custody proof. It does not assign
public State semantics, public `CalibStage` semantics, semantic `src1` /
`src2` contents, image effect, source contribution, reducer closure, or final
acceptance/rejection.

## Artifacts

- Runtime probe:
  [exit_snapshot_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/exit_snapshot_probe.py)
- Runtime LLDB scripts:
  [snapshot_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_28mm.lldb),
  [snapshot_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_35mm.lldb),
  [snapshot_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_70mm.lldb),
  [snapshot_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/snapshot_150mm.lldb)
- Runtime harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23c5f0_exit_snapshot/run_four_zoom.sh)
- Raw runtime outputs:
  `runs/state_helper_23c5f0_exit_snapshot/snapshot_28mm.{log,json,hdr}`,
  `runs/state_helper_23c5f0_exit_snapshot/snapshot_35mm.{log,json,hdr}`,
  `runs/state_helper_23c5f0_exit_snapshot/snapshot_70mm.{log,json,hdr}`,
  `runs/state_helper_23c5f0_exit_snapshot/snapshot_150mm.{log,json,hdr}`

The `.lldb` scripts launch with `--no-auto-lris`.

## Invocation

```bash
bash tools/lldb_probes/state_helper_23c5f0_exit_snapshot/run_four_zoom.sh
```

The harness invokes `arch -x86_64 lldb` against
`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`.

## Runtime Result

All four canonical bridge HDR runs completed, wrote `10432x7824` HDR output,
and exited with process status `0`.

| Zoom | LRI | JSON exit | Events | `0x23c5f0` hits | `0x23d392` hits | `0x23d5a8` hits | JSON errors | Step cap |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `34` | `4` | `26` | `4` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `34` | `4` | `26` | `4` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `34` | `4` | `26` | `4` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `30` | `4` | `22` | `4` | `0` | `false` |

The LLDB breakpoint hit-count fields and the probe's internal count fields
match in every run. No run hit the configured cap of `4096`.

## Invocation Pairing

Each run captured four `0x23c5f0` entries and four normal pre-destroy exits.
Invocation IDs `1`, `2`, `3`, and `4` pair exactly with the corresponding
pre-destroy exit event in every run.

The entry caller / argument pattern matches the earlier
[lldb_state_helpers_23c5f0_f33d0_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helpers_23c5f0_f33d0_four_zoom.md)
proof:

| Caller return VA | Containing State body | Entry invocations per run | Captured `r8d` | Captured `r9d` |
|---|---|---:|---:|---:|
| `0x22b51e` | `0x22af80` | `2` | `0` | `9` |
| `0x22e249` | `0x22e1d0` | `1` | `1` | `11` |
| `0x22e288` | `0x22e1d0` | `1` | `1` | `11` |

The probe records saved local-stack copies of the entry arguments near
`rbp-0x7a8` / `rbp-0x7a0` at the exit site, but those saved slots are not used
as facts here because the captured exit values are not stable. The entry-event
register captures above are the admitted argument evidence.

## Post-`0xf33d0` Local Integer Coverage

At `0x23d392`, the probe captures the local integer at `rbp-0x4e0` after the
internal `0x23c5f0 -> 0xf33d0` call returns.

| Zoom scope | Caller return VA(s) | Invocation(s) | Captured `rbp-0x4e0` values per invocation |
|---|---|---:|---|
| `28mm`, `35mm` | `0x22b51e` | `1`, `2` | `{1,2,3,4}` |
| `28mm`, `35mm` | `0x22e249`, `0x22e288` | `3`, `4` | `{1,2,3,4,5,6,7,8,9}` |
| `70mm` | `0x22b51e` | `1`, `2` | `{5,6,7,9}` |
| `70mm` | `0x22e249`, `0x22e288` | `3`, `4` | `{5,6,7,9,10,11,12,13,14}` |
| `150mm` | `0x22b51e` | `1`, `2` | `{5,6,9}` |
| `150mm` | `0x22e249`, `0x22e288` | `3`, `4` | `{5,6,9,10,11,12,13,14}` |

The `150mm` run omits captured post-`0xf33d0` value `7`, while the pre-destroy
local tree still contains a node whose `i32_0x20` field is `7`. This is a
field-coverage observation only; it does not by itself prove semantic
inclusion, exclusion, or image effect.

## Pre-Destroy Local Tree Snapshot

At `0x23d5a8`, the probe snapshots the local tree header at
`rbp-0x150`, `rbp-0x148`, and `rbp-0x140`, then walks the tree through node
child pointers at offsets `+0x00` and `+0x08`. Every captured tree has
`visited_count == header.size_minus_0x140` and `truncated == false`.

| Zoom scope | Caller return VA(s) | Invocation(s) | Tree size / visited | Node `i32_0x20` values | Node `i32_0xa0` grouping |
|---|---|---:|---:|---|---|
| `28mm`, `35mm` | `0x22b51e` | `1`, `2` | `5 / 5` | `{0,1,2,3,4}` | `0 -> 0`; `1,2,3,4 -> 9` |
| `28mm`, `35mm` | `0x22e249`, `0x22e288` | `3`, `4` | `10 / 10` | `{0,1,2,3,4,5,6,7,8,9}` | `0,1,2,3,4,5 -> 0`; `6,7,8,9 -> 11` |
| `70mm`, `150mm` | `0x22b51e` | `1`, `2` | `5 / 5` | `{0,5,6,7,9}` | `0 -> 0`; `5,6,7,9 -> 9` |
| `70mm`, `150mm` | `0x22e249`, `0x22e288` | `3`, `4` | `10 / 10` | `{0,5,6,7,9,10,11,12,13,14}` | `0,5,6,7,9 -> 0`; `10,11,12,13,14 -> 11` |

The node records also contain captured integer fields at `+0x18`, `+0x1c`,
`+0x24`, double fields at `+0x28..+0x98`, a four-float field at `+0x70`, a
qword field at `+0x80`, and the first `0x40` raw bytes. Those raw values remain
in the JSON artifacts. This proof admits only the local tree size, traversal
completeness, and selected integer-field groupings shown above.

## Proven Boundary

- `0x23c5f0` entry, post-`0xf33d0`, and normal pre-destroy exit are all
  runtime-live in complete accepted no-auto-LRIS bridge HDR renders at `28mm`,
  `35mm`, `70mm`, and `150mm`.
- Every captured `0x23c5f0` entry is paired with a normal pre-destroy exit
  under the tested runs.
- The post-`0xf33d0` local `rbp-0x4e0` integer coverage splits by focal tier:
  `28mm` / `35mm` use `1..4` and `1..9`; `70mm` uses `{5,6,7,9}` and
  `{5,6,7,9,10..14}`; `150mm` uses `{5,6,9}` and `{5,6,9,10..14}`.
- The pre-destroy local tree contains `5` nodes for the `0x22b51e` caller and
  `10` nodes for the `0x22e249` / `0x22e288` callers under every tested focal
  tier, with no traversal truncation.
- The pre-destroy local tree's selected integer fields separate wide and tele
  focal tiers as shown in the table above.

## Non-Claims

- This does not assign public names or semantics to the local integer at
  `rbp-0x4e0`, node field `i32_0x20`, node field `i32_0xa0`, or any other
  captured node field.
- This does not prove that the local tree survives after `0x23c5f0`; the
  snapshot is taken immediately before the local destroy call.
- This does not prove source contribution, C6 contribution/exclusion, final
  image effect, reducer closure, or final acceptance/rejection.
- This does not prove behavior outside the accepted canonical no-auto-LRIS
  bridge HDR quartet.
- This does not close `CLM-PREFUSION-002`.

## Consequence For Blocker Work

The State-helper edge is narrower again: `0x23c5f0` has a reproducible
post-copy local integer coverage pattern and a reproducible pre-destroy local
tree shape across the four canonical focal tiers. The remaining Lane A work is
still downstream effect, helper transitive behavior after the bounded
field-copy edge, semantic `src1` / `src2` contents, reducer closure, and final
acceptance/rejection.
