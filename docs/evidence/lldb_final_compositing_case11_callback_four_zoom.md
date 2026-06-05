# LLDB Proof: Final-Compositing Case-11 Callback Gate Across Four Zooms

## Scope

This proof follows the final-compositing switch census by drilling into the live
post-gather case `11` target inside `0x3bca90`.

It proves only tested-path reachability and local gate behavior for:

- case `11` target `0x3bd453`;
- owner `+0x5d0` null-branch test at `0x3bd45d`;
- callback callsite `0x3bd47b`;
- callback return site `0x3bd47d`.

It does not prove public record semantics, final sink, byte-level copy-vs-blend
behavior, anti-ghosting policy, final output semantics, or final merge
acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_case11_callback/case11_callback_probe.py`
- `tools/lldb_probes/codex_final_compositing_case11_callback/case11_callback_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case11_callback/case11_callback_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case11_callback/case11_callback_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case11_callback/case11_callback_150mm.lldb`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_case11_callback/case11_callback_28mm.json`
- `runs/codex_final_compositing_case11_callback/case11_callback_35mm.json`
- `runs/codex_final_compositing_case11_callback/case11_callback_70mm.json`
- `runs/codex_final_compositing_case11_callback/case11_callback_150mm.json`
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

The installed-bundle disassembly for case `11` is:

```asm
0x3bd453  movq 0x5d0(%r15), %rdi
0x3bd45a  testq %rdi, %rdi
0x3bd45d  je 0x3be640
0x3bd463  movl 0x10(%r13), %eax
0x3bd467  movl %eax, -0x3a4(%rbp)
0x3bd46d  movq (%rdi), %rax
0x3bd470  movq 0x30(%rax), %rax
0x3bd474  leaq -0x3a4(%rbp), %rsi
0x3bd47b  callq *%rax
0x3bd47d  jmp 0x3be640
```

The runtime probe was designed to test whether that owner `+0x5d0` callback
path is actually reached under the canonical CLI bridge-HDR quartet.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap.

| Zoom | Case-11 target `0x3bd453` | Null test `0x3bd45d` | Callback call `0x3bd47b` | Callback return `0x3bd47d` |
|---|---:|---:|---:|---:|
| `28mm` | 7 | 7 | 0 | 0 |
| `35mm` | 7 | 7 | 0 | 0 |
| `70mm` | 6 | 6 | 0 | 0 |
| `150mm` | 6 | 6 | 0 | 0 |

For every captured case-`11` null-test sample:

- record `field_i32_0x00 = 11`;
- record `field_i32_0x04 = 4`;
- record `field_i32_0x10` follows the already observed switch-census sequence
  `4, 9, 13, 18, 22, 27, 31` at `28mm` / `35mm`, and
  `4, 9, 13, 18, 22, 27` at `70mm` / `150mm`;
- owner pointer `+0x5d0 = 0`.

The probe captured additional raw record fields, but they are not promoted as
algorithm constants here.

## Proven Facts

- The case-`11` target `0x3bd453` is runtime-live across the canonical
  `28mm`, `35mm`, `70mm`, and `150mm` CLI bridge-HDR quartet.
- Under these admitted runs, the case-`11` path always reaches the owner
  `+0x5d0` null-branch test and observes owner `+0x5d0 = 0`.
- Under these admitted runs, the owner `+0x5d0` callback callsite `0x3bd47b`
  and post-call return site `0x3bd47d` record zero hits.
- Therefore, the case-`11` callback branch is not a runtime-proven final-output
  callback path for the tested canonical CLI bridge-HDR quartet.

## Non-Claims

- The zero callback-call finding is scoped to the tested canonical CLI
  bridge-HDR quartet; it is not a universal "case 11 never calls back" claim.
- This proof does not prove public names or semantics for the case-`11` record
  fields.
- This proof does not prove that the case-`11` records are globally terminal or
  globally irrelevant.
- This proof does not identify final file/display sink, copy-vs-blend behavior,
  final output semantics, anti-ghosting policy, or final merge
  acceptance/rejection.
