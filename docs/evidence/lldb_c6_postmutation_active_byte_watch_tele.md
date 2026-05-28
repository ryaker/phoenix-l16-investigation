# LLDB Evidence: C6 Post-Mutation Active-Byte Read/Write Watch

**Date:** 2026-05-28
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

Earlier evidence proves tele key `15` / C6 is constructed active at
`item+0x30 = 1` and later cleared to `0` at `libcp+0x3c90a5`. The prior
mutation watchpoint stops at that write.

This probe starts after the mutation. It breaks at `libcp+0x3c90a9`, verifies
the tracked item is key `15`, and arms a hardware read/write watchpoint on the
same item's `+0x30` byte. The goal is to enumerate later consumers of the
post-mutation active byte, including consumers that do not appear as direct
`call 0xf2720` key-getter sites.

This is single-byte custody evidence. It is not whole-object terminality proof
and it is not final image contribution/exclusion proof.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness and LLDB scripts:

- [c6_postmutation_active_byte_watch_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_probe.py)
- [c6_postmutation_active_byte_watch_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_70mm.lldb)
- [c6_postmutation_active_byte_watch_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_150mm.lldb)
- [run_postmutation_active_byte_watch.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_active_byte_watch/run_postmutation_active_byte_watch.sh)

Raw rerunnable outputs are under ignored
`runs/c6_postmutation_active_byte_watch/`.

Admitted JSON reports:

- `runs/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_70mm.json`
- `runs/c6_postmutation_active_byte_watch/c6_postmutation_active_byte_watch_150mm.json`

Command:

```bash
bash tools/lldb_probes/c6_postmutation_active_byte_watch/run_postmutation_active_byte_watch.sh
```

LLDB/debugserver needed to run outside the sandbox.

## Admission Checks

Both admitted reports satisfy:

- process exited with status `0`
- HDR output was written as `10432x7824`
- JSON report was written
- one watchpoint was armed after the key-15 `0x3c90a9` packet
- `errors == []`
- `drive_hit_step_cap == false`
- `watch_hit_cap` was not reached

## Arming Point

The arming breakpoint is `libcp+0x3c90a9`.

Both admitted reports have identical arming counts:

| Count | Value |
|---|---:|
| `mutation_after_hits` | `11` |
| `mutation_after_key15_hits` | `1` |
| `watchpoints_armed` | `1` |
| `watchpoint_hits` | `18` |

At arming time, both reports show the tracked item as:

```text
item+0x30 = 0
item+0x58/+0x5c = (-1, -1)
item+0x60 = 15
item+0x100 = 3
stack = 0x3c90a9 -> 0x3b219a -> 0x3b1c65 -> main -> start
```

## Watchpoint Stops

Both tele renders record 18 later hardware watchpoint stops on the tracked
`item+0x30` byte. Every recorded stop has:

```text
active_byte_now = 0
item_now+0x30 = 0
item_now+0x58/+0x5c = (-1, -1)
item_now+0x60 = 15
item_now+0x100 = 3
```

The `70mm` and `150mm` VA buckets are identical:

| Stop VA | Stops per run | Local static trigger / boundary |
|---:|---:|---|
| `0x3f2fbd` | `1` | stop after `cmpb $0x0, 0x30(%rdi)` in the `0x3f2c40` family |
| `0x3f30be` | `1` | stop after `cmpb $0x0, 0x30(%rdi)` in the same `0x3f2c40` family |
| `0x22eeb5` | `6` | stop after `cmpb $0x0, 0x30(%rdi)` in an active-byte gate that also calls `0xf2720` |
| `0x22f715` | `2` | stop after `cmpb $0x0, 0x30(%rdi)` in a related active-byte gate that also calls `0xf2720` |
| `0x40d23a` | `4` | stop after `cmpb $0x0, 0x30(%r13)` in an active-byte gate that also performs key/group counting work |
| `0x1a8df4` | `1` | stop after `cmpb $0x0, 0x30(%rdi)` in an active-byte gate that also calls `0xf2720` |
| `0x20b03b` | `1` | stop after `cmpb $0x0, 0x30(%r13)` in an active-byte gate that also calls `0xf2720` and performs tree lookup work |
| `0x3e0406` | `1` | stop after `movb 0x30(%rax), %bl`, followed by a later test of that loaded byte |
| outside `libcp` | `1` | allocator cleanup: `_platform_memset$VARIANT$Rosetta -> free_tiny -> libcp+0xe4ef6 -> ...` |

The allocator-cleanup stop happens after the log's `Written:` line in both
admitted renders. It is therefore cleanup evidence, not an image-route
consumer.

## Proven Facts

- The same tracked tele key-15 item byte watched after `0x3c90a5` remains
  `0` at every recorded later read/write stop in complete `70mm` and `150mm`
  bridge HDR renders.
- Later active-byte consumers are observed after mutation, including active-byte
  gates outside the already-censused direct `0xf2720` callsite inventory.
- No recorded watchpoint stop observes the tracked byte as nonzero.
- The final recorded non-`libcp` stop is allocator cleanup after output was
  written.

## Non-Conclusions

- This does not prove final C6 image contribution or exclusion.
- This does not prove whole C6 object terminality.
- This does not prove no other C6 fields, buffers, aliases, or object pointers
  are later used.
- This does not prove whole-buffer terminality for the zero-filled
  ImagePyramid route.
- This does not prove absence of all non-`0xf2720` C6 routes; it only covers
  later accesses to this one watched active byte.
- This does not generalize beyond the tested canonical bridge HDR tele seeds.
