# LLDB Proof: Final-Compositing Case-16 Cleanup Path Across Four Zooms

## Scope

This proof follows the final-compositing switch census by drilling into the live
post-gather case `16` target inside `0x3bca90`.

It proves only tested-path branch/callsite reachability and local cleanup
behavior for:

- case `16` target `0x3bd2f7`;
- call edge `0x3bd2fe -> 0x3adad0`;
- helper return edge `0x3bd303`;
- helper-internal cleanup path inside `0x3adad0`.

It does not prove public record semantics, helper body semantics, final file /
display sink, byte-level copy-vs-blend behavior, anti-ghosting policy, final
output semantics, or final merge acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_case16_cleanup/case16_cleanup_probe.py`
- `tools/lldb_probes/codex_final_compositing_case16_cleanup/case16_cleanup_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case16_cleanup/case16_cleanup_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case16_cleanup/case16_cleanup_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case16_cleanup/case16_cleanup_150mm.lldb`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_case16_cleanup/case16_cleanup_28mm.json`
- `runs/codex_final_compositing_case16_cleanup/case16_cleanup_35mm.json`
- `runs/codex_final_compositing_case16_cleanup/case16_cleanup_70mm.json`
- `runs/codex_final_compositing_case16_cleanup/case16_cleanup_150mm.json`
- `runs/codex_final_compositing_case16_cleanup/static_case16_window.txt`
- `runs/codex_final_compositing_case16_cleanup/static_3adad0_window.txt`
- matching `.log` and `.hdr` files in the same directory

## Inputs

All runs used the same installed x86_64 binary/framework set and the canonical
four LRIs:

| Zoom | LRI |
|---|---|
| `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Each launch passed `--profile 3 --export-fmt 3 --no-auto-lris` and completed a
`10432x7824` HDR write under LLDB.

## Static Shape

The installed-bundle disassembly for the case-`16` target is:

```asm
0x3bd2f7  movq -0x840(%rbp), %rdi
0x3bd2fe  callq 0x3adad0
0x3bd303  jmp 0x3be640
```

The installed-bundle disassembly for the tested helper path starts by saving
the incoming context pointer, calls `0x3ae1b0` to populate a local structure,
then branches to cleanup if either `context+0x180` or the local count at
`rbp-0x38` is zero:

```asm
0x3adae1  movq %rdi, %r12
0x3adafb  callq 0x3ae1b0
0x3adb00  movq 0x180(%r12), %rdi
0x3adb08  testq %rdi, %rdi
0x3adb0b  je 0x3adc74
0x3adb11  cmpq $0x0, -0x38(%rbp)
0x3adb16  je 0x3adc74
0x3adb6e  callq *%rax
0x3adb9b  callq 0x556320
0x3adbaa  callq 0x556320
0x3adbb9  callq 0x556320
0x3adc3f  callq 0x5563a4
0x3adc74  leaq -0x60(%rbp), %rdi
0x3adc78  callq 0x3ae490
0x3adcc3  movq -0x60(%rbp), %rdi
0x3adcdf  retq
```

The static excerpts are bounded evidence for this installed binary only.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap. Each run recorded 39 breakpoint stops.

| Site | Name | 28mm | 35mm | 70mm | 150mm |
|---|---|---:|---:|---:|---:|
| `0x3bd2f7` | case-`16` target | 1 | 1 | 1 | 1 |
| `0x3bd2fe` | case-`16` helper call | 1 | 1 | 1 | 1 |
| `0x3bd303` | case-`16` helper return | 1 | 1 | 1 | 1 |
| `0x3adad0` | helper entry | 4 | 4 | 4 | 4 |
| `0x3adafb` | helper populate call | 4 | 4 | 4 | 4 |
| `0x3adb00` | helper reads `context+0x180` | 4 | 4 | 4 | 4 |
| `0x3adb0b` | helper object null-branch site | 4 | 4 | 4 | 4 |
| `0x3adb16` | helper local-count branch site | 4 | 4 | 4 | 4 |
| `0x3adb6e` | helper callback call | 0 | 0 | 0 | 0 |
| `0x3adb9b` | helper release site `+0x40` | 0 | 0 | 0 | 0 |
| `0x3adbaa` | helper release site `+0x30` | 0 | 0 | 0 | 0 |
| `0x3adbb9` | helper release site `+0x08` | 0 | 0 | 0 | 0 |
| `0x3adc3f` | helper bad-function throw path | 0 | 0 | 0 | 0 |
| `0x3adc74` | helper cleanup path | 4 | 4 | 4 | 4 |
| `0x3adc78` | helper cleanup call | 4 | 4 | 4 | 4 |
| `0x3adcc3` | helper delete local base site | 4 | 4 | 4 | 4 |
| `0x3adcdf` | helper return | 4 | 4 | 4 | 4 |

## Case-16 Record And Context Observations

At the case-`16` target, the captured record and local context had the following
shape:

| Zoom | `i32+0x00` | `i32+0x04` | Captured remaining i32 fields | `rbp-0x840 == owner+0xd0` | Context `+0x180` | `+0x180` slot `+0x30` |
|---|---:|---:|---|---|---:|---|
| `28mm` | 16 | 2 | all zero | true | 140358550037552 | `0x3bb1a0` |
| `35mm` | 16 | 2 | all zero | true | 140549088661040 | `0x3bb1a0` |
| `70mm` | 16 | 2 | all zero | true | 140415324073520 | `0x3bb1a0` |
| `150mm` | 16 | 2 | all zero | true | 140470663869488 | `0x3bb1a0` |

The captured remaining i32 fields are offsets `+0x10`, `+0x14`, `+0x20`,
`+0x24`, `+0x28`, `+0x30`, `+0x34`, `+0x38`, and `+0x3c`. The table records raw
field shape only; it does not assign public semantic names.

At the case-`16` helper return site, all four admitted runs observed
`helper_return_rax = 0`.

## Helper Caller And Local Observations

The helper `0x3adad0` was entered four times per admitted render. The observed
caller stacks were the same across all four zooms:

| Helper caller chain from stack frame 1 | Interpretation |
|---|---|
| `0x3ba0e8 -> 0x3bf387 -> 0x3bd313` | additional observed caller route |
| `0x3ba0e8 -> 0x41b893 -> 0x41a614` | additional observed caller route |
| `0x41bdec -> 0x41a614 -> 0x41e3d4` | additional observed caller route |
| `0x3bd303 -> 0x280e -> non-libcp` | case-`16` helper return stack |

Every captured helper invocation reached the local-count branch site
`0x3adb16` with raw `rbp-0x38 = 0`. The auxiliary local pointer-span view
`ptr_array_count_8` varied by caller, but the raw branch operand stayed zero:

| Zoom | Observed `ptr_array_count_8` values at `0x3adb16` |
|---|---|
| `28mm` | `0`, `2`, `2`, `0` |
| `35mm` | `0`, `1`, `2`, `0` |
| `70mm` | `0`, `1`, `2`, `0` |
| `150mm` | `0`, `1`, `1`, `0` |

The `ptr_array_count_8` values are retained as raw local-shape observations
only. They are not promoted as public algorithm semantics.

## Proven Facts

- The case-`16` target `0x3bd2f7`, helper callsite `0x3bd2fe`, and helper
  return site `0x3bd303` are runtime-live once per canonical CLI bridge-HDR
  render at `28mm`, `35mm`, `70mm`, and `150mm`.
- Static disassembly shows case `16` passes `rbp-0x840` to helper `0x3adad0`;
  runtime packets show `rbp-0x840 == owner+0xd0` in all four admitted runs.
- The case-`16` record has `field_i32_0x00 = 16`, `field_i32_0x04 = 2`, and
  captured remaining i32 fields zero in all four admitted runs.
- Helper `0x3adad0` is entered four times per admitted render, and one entry
  is the case-`16` call returning to `0x3bd303`.
- Under these admitted runs, every helper invocation reaches `0x3adb16` with
  raw `rbp-0x38 = 0`, then reaches cleanup path `0x3adc74 -> 0x3ae490`,
  local-base cleanup site `0x3adcc3`, and return `0x3adcdf`.
- Under these admitted runs, helper callback site `0x3adb6e`, release sites
  `0x3adb9b`, `0x3adbaa`, `0x3adbb9`, and bad-function throw path `0x3adc3f`
  record zero hits.

## Non-Claims

- Zero-hit findings are scoped to the tested canonical CLI bridge-HDR quartet;
  they are not universal "never fires" claims for every Lumen path.
- This proof does not identify public names or semantics for case-`16` record
  fields, helper locals, local vector-like storage, or the context object.
- This proof does not classify the full helper body or prove global
  terminality for case `16` or helper `0x3adad0`.
- This proof does not cover live switch cases `1` or `3`.
- This proof does not identify final file/display sink, copy-vs-blend behavior,
  final output semantics, anti-ghosting policy, or final merge
  acceptance/rejection.

## Operational Note

These admitted LLDB runs were executed outside the Codex sandbox because
sandboxed `debugserver` was denied the task port for `lri_process` on this
machine. That environment note is not evidence about `libcp` behavior.
