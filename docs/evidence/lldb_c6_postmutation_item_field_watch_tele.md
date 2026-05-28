# LLDB Evidence: C6 Post-Mutation Selected-Field Read/Write Watch

**Date:** 2026-05-28
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

Earlier evidence proves tele key `15` / C6 is constructed active at
`item+0x30 = 1`, cleared to `0` at `libcp+0x3c90a5`, and later observed by a
single-byte watchpoint with `item+0x30 = 0`.

This probe starts at the same post-mutation arming boundary, `libcp+0x3c90a9`,
and arms hardware read/write watchpoints on selected fields of the same
tracked key-15 item:

- `active_0x30`: `item+0x30`, size `1`
- `pair_0x58`: `item+0x58..0x5f`, size `8`
- `key_0x60`: `item+0x60..0x67`, size `8`
- `type_0x100`: `item+0x100..0x107`, size `8`

This is selected-field custody evidence. It is not whole-object terminality
proof and it is not final C6 image contribution/exclusion proof.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness and LLDB scripts:

- [c6_postmutation_item_field_watch_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_probe.py)
- [c6_postmutation_item_field_watch_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_70mm.lldb)
- [c6_postmutation_item_field_watch_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_150mm.lldb)
- [run_item_field_watch.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_item_field_watch/run_item_field_watch.sh)

Raw rerunnable outputs are under ignored
`runs/c6_postmutation_item_field_watch/`.

Admitted JSON reports:

- `runs/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_70mm.json`
- `runs/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_150mm.json`

Command:

```bash
bash tools/lldb_probes/c6_postmutation_item_field_watch/run_item_field_watch.sh
```

LLDB/debugserver needed to run outside the sandbox.

## Admission Checks

Both admitted reports satisfy:

- process exited with status `0`
- HDR output was written as `10432x7824`
- JSON report was written
- four watchpoints were armed after the key-15 `0x3c90a9` packet
- `errors == []`
- `drive_hit_step_cap == false`
- `watch_hit_cap` was not reached

The output-write lines are in the raw logs:

- `runs/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_70mm.log:293`
- `runs/c6_postmutation_item_field_watch/c6_postmutation_item_field_watch_150mm.log:293`

## Arming Point

The arming breakpoint is `libcp+0x3c90a9`.

Both admitted reports have identical arming counts:

| Count | Value |
|---|---:|
| `mutation_after_hits` | `11` |
| `mutation_after_key15_hits` | `1` |
| `watchpoints_armed` | `4` |

At arming time, both reports show the tracked item as:

```text
item+0x30 = 0
item+0x58/+0x5c = (-1, -1)
item+0x60 = 15
item+0x100 = 3
```

Watched bytes at arming:

| Range | `70mm` bytes | `150mm` bytes |
|---|---|---|
| `item+0x30` | `00` | `00` |
| `item+0x58..0x5f` | `ffffffffffffffff` | `ffffffffffffffff` |
| `item+0x60..0x67` | `0f00000000000000` | `0f00000000000000` |
| `item+0x100..0x107` | `0300000013000000` | `030000001e000000` |

## Counting Rule

The sample counts below use JSON `watchpoint_samples`, not raw LLDB
watchpoint hit counters. In the `70mm` run, LLDB's raw per-watchpoint counters
sum to `70`, while the recorded sample list contains `68` samples. No admitted
claim in this document depends on the raw counter-only surplus.

## Watchpoint Samples

| Watched range | `70mm` recorded samples | `150mm` recorded samples | Pre-output `libcp` stops |
|---|---:|---:|---|
| `item+0x30` | `17` | `18` | yes |
| `item+0x58..0x5f` | `1` | `1` | no |
| `item+0x60..0x67` | `49` | `50` | yes |
| `item+0x100..0x107` | `1` | `1` | no |

All pre-output `libcp` samples in both reports show:

```text
item+0x30 = 0
item+0x58/+0x5c = (-1, -1)
item+0x60 = 15
item+0x100 = 3
```

The selected pair range `item+0x58..0x5f` and selected
type/adjoining range `item+0x100..0x107` record no pre-output `libcp`
watchpoint stops. Each has one recorded stop during allocator cleanup after the
output `Written:` line.

## Pre-Output Stop Sites

The `item+0x30` watchpoint hits active-byte gates already compatible with the
single-byte watchpoint proof. This multi-watchpoint run is not the authority
for the prior exact 18-stop same-byte count.

Pre-output `item+0x30` stop buckets:

| Stop VA | `70mm` samples | `150mm` samples |
|---:|---:|---:|
| `0x3f2fbd` | `1` | `1` |
| `0x3f30be` | `1` | `1` |
| `0x22eeb5` | `6` | `6` |
| `0x22f715` | `1` | `2` |
| `0x40d23a` | `4` | `4` |
| `0x1a8df4` | `1` | `1` |
| `0x20b03b` | `1` | `1` |
| `0x3e0406` | `1` | `1` |

Pre-output `item+0x60..0x67` stop buckets:

| Stop VA | `70mm` samples | `150mm` samples | Static read inside watched range |
|---:|---:|---:|---|
| `0xf2727` | `27` | `27` | `0xf2720` reads `movl 0x60(%rdi), %eax` |
| `0xf3327` | `21` | `22` | `0xf3320` reads `movl 0x64(%rdi), %eax` |

The `0xf3327` bucket is inside the watchpoint labeled `key_0x60` because that
watchpoint spans eight bytes. Static disassembly proves it reads `item+0x64`,
not the 32-bit key at `item+0x60`.

## Cleanup Stops

Each admitted run records four final non-`libcp` stops after the output
`Written:` line, one for each armed watchpoint. The shared stack prefix is:

```text
_platform_memset$VARIANT$Rosetta
free_tiny
libcp+0xe4ef6
std::__1::__shared_weak_count::__release_shared()
libcp+0x3c98f3
```

Those stops are allocator cleanup evidence, not image-route consumer evidence.

## Proven Facts

- The same tracked tele key-15 item was watched after `0x3c90a5` cleared its
  active byte and after `0x3c90a9` observed the immediate inactive state.
- Complete canonical `70mm` and `150mm` bridge HDR renders exit cleanly and
  write `10432x7824` HDR output while the selected-field watchpoints are armed.
- During pre-output `libcp` samples, the tracked item remains
  `item+0x30 = 0`, `item+0x58/+0x5c = (-1,-1)`, `item+0x60 = 15`, and
  `item+0x100 = 3`.
- The watched `item+0x60..0x67` range is read before output at `0xf2727` and
  `0xf3327`; static disassembly identifies `0xf2727` as the return after a
  true `item+0x60` 32-bit read, and `0xf3327` as the return after an adjacent
  `item+0x64` 32-bit read.
- The watched `item+0x58..0x5f` range and watched `item+0x100..0x107` range
  have no recorded pre-output `libcp` stops in these runs.
- The only recorded stops for `item+0x58..0x5f` and `item+0x100..0x107` are
  allocator cleanup after output was written.

## Non-Conclusions

- This does not prove final C6 image contribution or exclusion.
- This does not prove whole C6 object terminality.
- This does not prove no untested C6 fields, buffers, aliases, or object
  pointers are later used.
- This does not assign public semantics to `item+0x64`,
  `item+0x100..0x107`, or any other watched field.
- This does not prove that the `item+0x60..0x67` reads have no final
  image/merge effect.
- This does not prove whole-buffer terminality for the zero-filled
  ImagePyramid route.
- This does not generalize beyond the tested canonical bridge HDR tele seeds.
