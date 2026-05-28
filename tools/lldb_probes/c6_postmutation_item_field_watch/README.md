# C6 Post-Mutation Item Field Watch

This probe arms hardware read/write watchpoints on selected fields of the same
tracked tele key-15 item after the proven mutation has already cleared
`item+0x30`.

It extends `../c6_postmutation_active_byte_watch/`, which watches only
`item+0x30`.

## Scope

- Canonical tele bridge HDR seeds only:
  - `70mm`: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
  - `150mm`: `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`
- Same-name `.lris` auto-loading disabled.
- Default watched fields:
  - `active_0x30`: `item+0x30`, size `1`
  - `pair_0x58`: `item+0x58`, size `8`
  - `key_0x60`: `item+0x60`, size `8`
  - `type_0x100`: `item+0x100`, size `8`

## Admission Rules

Only cite a run if:

- the process exits cleanly,
- JSON exists under `runs/c6_postmutation_item_field_watch/`,
- at least one watchpoint is armed on key `15`,
- JSON has no `errors`,
- `drive_hit_step_cap` is false unless the claim is explicitly capped.

## Admitted Result: 2026-05-28

Evidence document:

- [lldb_c6_postmutation_item_field_watch_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_c6_postmutation_item_field_watch_tele.md)

Both canonical tele runs completed with exit status `0` and wrote `10432x7824`
HDR output. Each run armed four watchpoints after the immediate inactive
`0x3c90a9` state on the same tracked key-15 item.

Recorded sample counts use JSON `watchpoint_samples`, not raw LLDB hit
counters:

| Watched range | `70mm` samples | `150mm` samples | Pre-output `libcp` stops |
|---|---:|---:|---|
| `item+0x30` | `17` | `18` | yes |
| `item+0x58..0x5f` | `1` | `1` | no |
| `item+0x60..0x67` | `49` | `50` | yes |
| `item+0x100..0x107` | `1` | `1` | no |

Static disassembly resolves the two pre-output `item+0x60..0x67` stop sites:

- `0xf2727` is the return after `movl 0x60(%rdi), %eax`.
- `0xf3327` is the return after `movl 0x64(%rdi), %eax`; this is an adjacent
  field inside the watched 8-byte range, not the 32-bit key itself.

The only recorded stops for `item+0x58..0x5f` and `item+0x100..0x107` are
allocator cleanup after the output `Written:` line. This narrows selected
post-mutation field behavior; it does not prove whole-object terminality,
alias absence, or final C6 image contribution/exclusion.
