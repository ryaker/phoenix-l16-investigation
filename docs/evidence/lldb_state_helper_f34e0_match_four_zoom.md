# LLDB Evidence: `0x23c5f0` Destination Objects Reused By `0xf34e0` Inside The State Helper

## Scope

This proof follows:

- [lldb_state_helpers_23c5f0_f33d0_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helpers_23c5f0_f33d0_four_zoom.md)
- [lldb_state_helper_23c5f0_exit_snapshot_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helper_23c5f0_exit_snapshot_four_zoom.md)
- [bundle_proof_iramp_calib_object_accessors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_calib_object_accessors.md)

It tests whether the destination objects populated by the live
`0x23c5f0 -> 0xf33d0` selector-`1` copy path are later passed to the
`0xf34e0` two-bank accessor.

This is internal helper-custody proof. The matched `0xf34e0` calls occur under
the stack `0xf34e0 <- 0x264270 <- 0x23c5f0`, before `0x23c5f0` exits. This is
not proof of post-`0x23c5f0` downstream image effect, reducer closure, or final
acceptance/rejection.

## Artifacts

- Runtime probe:
  [f34e0_match_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_probe.py)
- Runtime LLDB scripts:
  [f34e0_match_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_28mm.lldb),
  [f34e0_match_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_35mm.lldb),
  [f34e0_match_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_70mm.lldb),
  [f34e0_match_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/f34e0_match_150mm.lldb)
- Runtime harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_f34e0_match_runtime/run_four_zoom.sh)
- Raw runtime outputs:
  `runs/state_helper_f34e0_match_runtime/f34e0_match_28mm.{log,json,hdr}`,
  `runs/state_helper_f34e0_match_runtime/f34e0_match_35mm.{log,json,hdr}`,
  `runs/state_helper_f34e0_match_runtime/f34e0_match_70mm.{log,json,hdr}`,
  `runs/state_helper_f34e0_match_runtime/f34e0_match_150mm.{log,json,hdr}`

The `.lldb` scripts launch with `--no-auto-lris`.

## Invocation

```bash
bash tools/lldb_probes/state_helper_f34e0_match_runtime/run_four_zoom.sh
```

The admitted facts below come from the JSON reports listed in the Artifacts
section.

## Static Boundary

Installed-bundle static disassembly shows:

- `0xf34e0(object, selector)` returns `object+0x12c` when `selector == 1`;
  otherwise it returns `object+0x180`.
- `0x264270` calls `0xf34e0` at `0x26428e`, `0x2642ad`, and `0x2642ca`.
  The corresponding return VAs are `0x264293`, `0x2642b2`, and `0x2642cf`.
- `0x264270` copies fields from the selected bank into its destination record
  after each `0xf34e0` return.
- `0x264440` is a thin wrapper that sets `edx = 1` and tail-jumps to
  `0x264270`.
- Inside `0x23c5f0`, the static call at `0x23cba6 -> 0x264440` returns at
  `0x23cbab`.

The runtime proof below tests pointer identity between objects populated at
`0x23d392` and objects later passed to `0xf34e0`.

## Runtime Result

All four canonical bridge HDR runs completed, wrote `10432x7824` HDR output,
and exited with process status `0`.

| Zoom | LRI | JSON exit | `0x23d392` hits | `0xf34e0` hits | Matched `0xf34e0` hits | Matched objects | JSON errors | Step cap |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `26` | `735` | `204` | `9` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `26` | `735` | `204` | `9` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `26` | `762` | `204` | `9` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `26` | `762` | `204` | `9` | `0` | `false` |

The LLDB breakpoint hit-count fields and the probe's internal count fields
match in every admitted JSON. No run hit the configured cap of `8192`.

## `0x23d392` Destination Coverage

The probe records the destination pointer at `rbp-0x778` and the local integer
at `rbp-0x4e0` at every `0x23d392` post-`0xf33d0` stop.

| Zoom scope | Captured `rbp-0x4e0` value counts |
|---|---|
| `28mm`, `35mm` | `{1:4, 2:4, 3:4, 4:4, 5:2, 6:2, 7:2, 8:2, 9:2}` |
| `70mm`, `150mm` | `{5:4, 6:4, 7:4, 9:4, 10:2, 11:2, 12:2, 13:2, 14:2}` |

Each run yields nine unique destination object pointers that are later matched
by `0xf34e0` calls.

## Matched `0xf34e0` Calls

Every matched `0xf34e0` call uses selector `1`. By the static `0xf34e0`
formula, selector `1` selects the `object+0x12c` bank.

| Caller return VA inside `0x264270` | Static callsite | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---|---:|---:|---:|---:|
| `0x264293` | `0x26428e -> 0xf34e0` | `68` | `68` | `68` | `68` |
| `0x2642b2` | `0x2642ad -> 0xf34e0` | `68` | `68` | `68` | `68` |
| `0x2642cf` | `0x2642ca -> 0xf34e0` | `68` | `68` | `68` | `68` |

The matched runtime stack is:

```text
0xf34e0 <- 0x264270 <- 0x23c5f0 <- State body <- dispatcher
```

The `0x23c5f0` frame return VA for these matched samples is `0x23cbab`, the
return site after the static `0x23cba6 -> 0x264440` call. Since `0x264440`
sets `edx = 1` and tail-jumps to `0x264270`, the runtime selector-`1` result
matches the static wrapper.

## Proven Boundary

- Under complete accepted no-auto-LRIS bridge HDR runs at `28mm`, `35mm`,
  `70mm`, and `150mm`, objects populated by `0x23c5f0 -> 0xf33d0` at
  `0x23d392` are later passed to `0xf34e0` inside the same `0x23c5f0`
  invocation family.
- The matched `0xf34e0` calls all use selector `1`, which statically selects
  `object+0x12c`.
- The matched callsites are exactly the three `0x264270 -> 0xf34e0` callsites
  at returns `0x264293`, `0x2642b2`, and `0x2642cf`, reached through
  `0x23c5f0 -> 0x264440 -> 0x264270`.
- This proves a live transitive helper-consumer path for the records copied by
  `0xf33d0`; it does not prove post-`0x23c5f0` downstream image effect.

## Non-Claims

- This does not assign public names or semantics to the `0xf34e0` banks,
  `CalibStage`, `rbp-0x4e0`, source contribution, or State values.
- This does not prove that the matched copied fields are used after `0x23c5f0`
  returns.
- This does not prove image effect, reducer closure, or final
  acceptance/rejection.
- This does not prove behavior outside the accepted canonical no-auto-LRIS
  bridge HDR quartet.
- This does not close `CLM-PREFUSION-002`.

## Consequence For Blocker Work

The `0x23c5f0` helper is no longer just a field-copy boundary: the copied
destination objects are immediately reused by a live `0x264440 -> 0x264270 ->
0xf34e0` transitive helper path inside `0x23c5f0`. The remaining Lane A work is
to follow the resulting helper records and local tree nodes to a proven
post-helper image effect, source contribution effect, reducer closure, or final
acceptance/rejection decision.
