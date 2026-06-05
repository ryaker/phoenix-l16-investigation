# LLDB Proof: Final-Compositing Case-1 / Case-3 Boundary Across Four Zooms

## Scope

This proof follows the final-compositing switch census by drilling into the
remaining live post-gather cases `1` and `3` inside `0x3bca90`.

It proves only tested-path branch/callsite reachability and raw operand custody
for:

- case `1` target `0x3bce77`;
- case `1` mutex / flag / condition-broadcast boundary;
- case `3` target `0x3bcee3`;
- case `3` call edge `0x3bcf16 -> 0x4182a0`;
- selected callsites and normal/error branch bounds inside helper `0x4182a0`.

It does not prove public record semantics, helper body semantics, final file /
display sink, byte-level copy-vs-blend behavior, anti-ghosting policy, final
output semantics, or final merge acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_boundary_probe.py`
- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_150mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/run_four_zoom.sh`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_28mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_35mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_70mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_150mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/static_case1_case3_4182a0_windows.txt`
- `runs/codex_final_compositing_case1_case3_boundary/static_4182a0_error_sites.txt`
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

The installed-bundle disassembly for the case-`1` target is:

```asm
0x3bce77  movq -0x800(%rbp), %rdi
0x3bce7e  callq pthread_mutex_lock
0x3bce83  cmpl $0x1, (%r13)
0x3bce88  jne 0x3bea7b
0x3bce8e  movq 0x10(%r13), %rax
0x3bce92  movb $0x1, (%rax)
0x3bce95  movq -0x820(%rbp), %rdi
0x3bce9c  callq pthread_cond_broadcast
0x3bcea1  movq -0x800(%rbp), %rdi
0x3bcea8  callq pthread_mutex_unlock
0x3bcead  jmp 0x3be640
```

The installed-bundle disassembly for the case-`3` target is:

```asm
0x3bcee3  movl $0x1, %esi
0x3bcee8  movq %r15, %rdi
0x3bceeb  callq 0x3b07c0
0x3bcef0  cmpl $0x3, (%r13)
0x3bcef5  jne 0x3beacd
0x3bcefb  leaq 0x10(%r13), %rsi
0x3bceff  leaq 0x60(%r13), %rdx
0x3bcf03  leaq 0x50(%r13), %rcx
0x3bcf07  movl 0x68(%r13), %r8d
0x3bcf0b  leaq 0x20(%r13), %r9
0x3bcf0f  movq -0x7f0(%rbp), %rdi
0x3bcf16  callq 0x4182a0
0x3bcf1b  jmp 0x3be640
```

Selected installed-bundle disassembly inside helper `0x4182a0` shows it saves
the case-`3` arguments, reaches callsites `0x41e170`, `0x292070`, `0x419080`,
`0x3b6070`, `0x3b07c0`, and `0x41e180`, then has a normal return at
`0x418bfd..0x418c0e`. The same static excerpt locates error labels
`0x418d38` and `0x418e27`. These static excerpts are bounded evidence for this
installed binary only.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap. Each run recorded 24 breakpoint stops.

| Zoom | Exit | State | Errors | Step cap | Drive steps |
|---|---:|---|---:|---|---:|
| `28mm` | 0 | `exited` | 0 | `False` | 24 |
| `35mm` | 0 | `exited` | 0 | `False` | 24 |
| `70mm` | 0 | `exited` | 0 | `False` | 24 |
| `150mm` | 0 | `exited` | 0 | `False` | 24 |

| Site | Name | 28mm | 35mm | 70mm | 150mm |
|---|---|---:|---:|---:|---:|
| `0x3bce77` | case-`1` target | 1 | 1 | 1 | 1 |
| `0x3bce7e` | case-`1` mutex lock call | 1 | 1 | 1 | 1 |
| `0x3bce83` | case-`1` type check | 1 | 1 | 1 | 1 |
| `0x3bce8e` | case-`1` flag pointer load | 1 | 1 | 1 | 1 |
| `0x3bce92` | case-`1` flag write | 1 | 1 | 1 | 1 |
| `0x3bce95` | case-`1` after flag write | 1 | 1 | 1 | 1 |
| `0x3bce9c` | case-`1` condition broadcast call | 1 | 1 | 1 | 1 |
| `0x3bcea8` | case-`1` mutex unlock call | 1 | 1 | 1 | 1 |
| `0x3bcead` | case-`1` return jump | 1 | 1 | 1 | 1 |
| `0x3bea7b` | case-`1` mismatch target | 0 | 0 | 0 | 0 |
| `0x3bcee3` | case-`3` target | 1 | 1 | 1 | 1 |
| `0x3bceeb` | case-`3` pre-helper call `0x3b07c0` | 1 | 1 | 1 | 1 |
| `0x3bcef0` | case-`3` type check | 1 | 1 | 1 | 1 |
| `0x3bcf16` | case-`3` helper call `0x4182a0` | 1 | 1 | 1 | 1 |
| `0x3bcf1b` | case-`3` return jump | 1 | 1 | 1 | 1 |
| `0x3beacd` | case-`3` mismatch target | 0 | 0 | 0 | 0 |
| `0x4182a0` | helper entry | 1 | 1 | 1 | 1 |
| `0x418380` | helper call `0x41e170` | 1 | 1 | 1 | 1 |
| `0x41847d` | helper call `0x292070` | 1 | 1 | 1 | 1 |
| `0x4184b0` | helper call `0x419080` | 1 | 1 | 1 | 1 |
| `0x41850b` | helper call `0x3b6070` | 1 | 1 | 1 | 1 |
| `0x418518` | helper call `0x3b07c0` | 1 | 1 | 1 | 1 |
| `0x4186a3` | helper color-space guard | 1 | 1 | 1 | 1 |
| `0x4188df` | helper `0x41e180` setup | 1 | 1 | 1 | 1 |
| `0x418908` | helper call `0x41e180` | 1 | 1 | 1 | 1 |
| `0x418bfd` | helper normal return | 1 | 1 | 1 | 1 |
| `0x418d38` | helper unexpected-color-space error | 0 | 0 | 0 | 0 |
| `0x418e27` | helper unexpected-compression error | 0 | 0 | 0 | 0 |

## Case-1 Record And Synchronization Observations

At the case-`1` target, the captured record type field was `1` in all four
admitted runs. The runtime packets prove that the static flag write changes the
pointed byte from `0` to `1` before the condition broadcast call, and that the
same mutex pointer is used at the lock and unlock callsites.

| Zoom | Record type at case `1` | Flag byte before `0x3bce92` | Flag byte after `0x3bce92` | Mutex ptr matches lock/unlock source | Cond ptr passed to broadcast |
|---|---:|---:|---:|---|---|
| `28mm` | 1 | 0 | 1 | `True` | `True` |
| `35mm` | 1 | 0 | 1 | `True` | `True` |
| `70mm` | 1 | 0 | 1 | `True` | `True` |
| `150mm` | 1 | 0 | 1 | `True` | `True` |

The table records raw synchronization/flag behavior only. It does not assign a
public semantic name to the case-`1` record or to the pointed flag byte.

## Case-3 Helper Argument Custody

At the case-`3` helper callsite, the captured record type field was `3` in all
four admitted runs. The runtime packets prove that `0x3bcf16` passes the
expected record substructures into helper `0x4182a0`:

| Zoom | Record type at case `3` | `rsi == record+0x10` | `r9 == record+0x20` | `rcx == record+0x50` | `rdx == record+0x60` | `r8d` | dims from `record+0x60` |
|---|---:|---|---|---|---|---:|---|
| `28mm` | 3 | `True` | `True` | `True` | `True` | 3 | `10432 x 7824`, tag `3` |
| `35mm` | 3 | `True` | `True` | `True` | `True` | 3 | `10432 x 7824`, tag `3` |
| `70mm` | 3 | `True` | `True` | `True` | `True` | 3 | `10432 x 7824`, tag `3` |
| `150mm` | 3 | `True` | `True` | `True` | `True` | 3 | `10432 x 7824`, tag `3` |

The helper entry packets preserve the same `r8d = 3` and the same
`record+0x60` first-three-int shape (`10432`, `7824`, `3`) in all four admitted
runs.

## Proven Facts

- The case-`1` target `0x3bce77` and its tested mutex / flag /
  condition-broadcast path are runtime-live once per canonical CLI bridge-HDR
  render at `28mm`, `35mm`, `70mm`, and `150mm`.
- Under those admitted runs, case `1` observes `field_i32_0x00 = 1`, writes
  byte value `1` through the pointer stored at `record+0x10`, changes the
  captured pointed byte from `0` to `1`, calls `pthread_cond_broadcast` with
  the local condition pointer, and unlocks the same local mutex pointer that it
  locked.
- Under those admitted runs, the case-`1` mismatch target `0x3bea7b` records
  zero hits.
- The case-`3` target `0x3bcee3`, pre-helper callsite `0x3bceeb -> 0x3b07c0`,
  helper callsite `0x3bcf16 -> 0x4182a0`, and return jump `0x3bcf1b` are
  runtime-live once per canonical CLI bridge-HDR render at `28mm`, `35mm`,
  `70mm`, and `150mm`.
- Under those admitted runs, case `3` observes `field_i32_0x00 = 3` and passes
  `record+0x10`, `record+0x60`, `record+0x50`, `record+0x20`, and
  `record+0x68` into helper `0x4182a0` exactly as shown by the static call
  shape.
- Under those admitted runs, the case-`3` mismatch target `0x3beacd` records
  zero hits.
- Under those admitted runs, helper `0x4182a0` is entered once per render from
  the case-`3` path, reaches selected callsites `0x418380`, `0x41847d`,
  `0x4184b0`, `0x41850b`, `0x418518`, `0x418908`, reaches normal-return site
  `0x418bfd`, and records zero hits at error labels `0x418d38` and
  `0x418e27`.

## Non-Claims

- Zero-hit findings are scoped to the tested canonical CLI bridge-HDR quartet;
  they are not universal "never fires" claims for every Lumen path.
- This proof does not identify public names or semantics for case-`1` or
  case-`3` record fields, helper locals, helper arguments, or context objects.
- This proof does not classify the full helper body or prove global
  terminality for case `1`, case `3`, or helper `0x4182a0`.
- This proof does not identify final file/display sink, copy-vs-blend behavior,
  final output semantics, anti-ghosting policy, or final merge
  acceptance/rejection.

## Operational Note

These admitted LLDB runs were executed outside the Codex sandbox because
sandboxed `debugserver` was denied the task port for `lri_process` on this
machine. That environment note is not evidence about `libcp` behavior.
