# C6 Post-Mutation Active-Byte Watch

This probe arms a hardware read/write watchpoint on the tracked tele key-15
item's `+0x30` byte after the proven mutation store at `0x3c90a5`.

It differs from `../c6_active_byte_watch/`, which intentionally stops at the
mutation write. This probe starts after that write, then continues the render to
enumerate later direct or non-`0xf2720` consumers of the same active byte.

## Scope

- Canonical tele bridge HDR seeds only:
  - `70mm`: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
  - `150mm`: `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`
- Same-name `.lris` auto-loading disabled.
- Watches one byte: tracked key-15 item `+0x30`.

## Admission Rules

Only cite a run if:

- the process exits cleanly,
- JSON exists under `runs/c6_postmutation_active_byte_watch/`,
- one watchpoint is armed on key `15`,
- JSON has no `errors`,
- `drive_hit_step_cap` is false unless the claim is explicitly capped.

## Admitted Result

The 2026-05-28 admitted `70mm` and `150mm` runs both completed with process
exit status `0`, wrote `10432x7824` HDR output, armed one watchpoint, and
recorded 18 later watchpoint stops. Every stop observed the watched key-15
`item+0x30` byte as `0`.

Durable write-up:

- [lldb_c6_postmutation_active_byte_watch_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_c6_postmutation_active_byte_watch_tele.md)
