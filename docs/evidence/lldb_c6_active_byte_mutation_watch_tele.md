# LLDB Evidence: Tele C6 Active-Byte Mutation Watchpoint

**Date:** 2026-05-26
**Status:** admitted evidence candidate for `CLM-C6-001` and
`CLM-PREFUSION-001`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`; tele seeds only

## Purpose

Earlier runtime probes proved two tested C6 filter points where tele key `15`
had `object+0x30 = 0`. The new constructor-origin probe proves the same key is
initially constructed with `+0x30 = 1`.

This proof answers the next narrow question:

Where is the constructed C6/key15 item's `+0x30` active byte first observed
changing from `1` to `0` in the canonical tele bridge HDR runs?

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness:

- [c6_active_byte_watch_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_active_byte_watch/c6_active_byte_watch_probe.py)

LLDB scripts:

- [c6_active_byte_watch_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_active_byte_watch/c6_active_byte_watch_70mm.lldb)
- [c6_active_byte_watch_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_active_byte_watch/c6_active_byte_watch_150mm.lldb)

Raw rerunnable JSON reports are under ignored `runs/c6_active_byte_watch/`.
These watchpoint runs intentionally stop at the mutation. They are mutation
evidence, not output-completion evidence.

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_active_byte_watch/c6_active_byte_watch_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_active_byte_watch/c6_active_byte_watch_150mm.lldb
```

## Watchpoint Method

At the post-`0xf2770` return site `0xe59a9`, the probe inspects the constructed
item pointer in `rbx`. If item `+0x60` is key `15`, the probe records the
initial fields and arms a one-byte hardware write watchpoint on item `+0x30`.

Captured initial fields for both tele seeds:

- item `+0x60 = 15`
- item `+0x30 = 1`
- item `+0x58/+0x5c = (-1,-1)`
- item `+0x100 = 3`

## Runtime Result

| Zoom | JSON report | `0xf2770` returns | Watchpoints armed | Watch hits | Hit VA | Active byte after hit |
|---|---|---:|---:|---:|---:|---:|
| `70mm` | `runs/c6_active_byte_watch/c6_active_byte_watch_70mm.json` | `11` | `1` | `1` | `0x3c90a9` | `0` |
| `150mm` | `runs/c6_active_byte_watch/c6_active_byte_watch_150mm.json` | `11` | `1` | `1` | `0x3c90a9` | `0` |

The watchpoint stop PC is `libcp+0x3c90a9`, which is the instruction after the
write. The actual writer is the immediately preceding instruction at
`libcp+0x3c90a5`:

```asm
0x3c9095  movq   (%rbx), %rdi
0x3c9098  callq  0xf2720
0x3c909d  cmpl   $0xf, %eax
0x3c90a0  jne    0x3c90a9
0x3c90a2  movq   (%rbx), %rax
0x3c90a5  movb   $0x0, 0x30(%rax)
0x3c90a9  movq   (%rbx), %rdi
```

Both tele runs captured the same stack shape at the watchpoint:

| Frame | libcp VA |
|---:|---:|
| `0` | `0x3c90a9` |
| `1` | `0x3b20da` |
| `2` | `0x3b1c65` |

The remaining frames are `main` and `start`.

## Static Gate Shape

Installed-bundle disassembly around the writer body `libcp+0x3c8f90` shows the
local gate that leads to the byte clear:

```asm
0x3c900e  movq   %r15, %rdi
0x3c9011  callq  0xe78d0
0x3c9016  movq   (%rax), %rbx
0x3c9019  movq   0x8(%rax), %r14
0x3c9040  movq   (%rbx), %rdi
0x3c9043  callq  0xf2720
0x3c904d  callq  0xf3bc0
0x3c9055  callq  0xf3360
0x3c905a  cmpq   $0x0, 0xb8(%rax)
0x3c9068  callq  0xf3570
0x3c9070  cmpb   $0x0, 0x40(%rax)
0x3c907a  movq   %r15, %rdi
0x3c907d  callq  0xe6cf0
0x3c9087  callq  0xf6c60
0x3c908c  cmpl   $0x2, -0x118(%rbp)
0x3c9093  je     0x3c90a9
0x3c9095  movq   (%rbx), %rdi
0x3c9098  callq  0xf2720
0x3c909d  cmpl   $0xf, %eax
0x3c90a5  movb   $0x0, 0x30(%rax)
```

Static helper facts already admitted elsewhere:

- `0xf2720(item)` returns item key field `+0x60`.
- `0xe6cf0(context)` returns the dword at context `+0x44`.
- `0xf6c60` maps camera IDs `0..4`, `5..9`, and `10..15` to group ordinals
  `0`, `1`, and `2`.

Within this body, the byte-clear path is taken only when the context field
`+0x44`, after `0xf6c60` grouping, is not group ordinal `2`, and the current
loop item key is `15`.

## Proven Facts

- Tele key `15` / C6 is constructed by the tested `0xf2770` path with active
  byte `+0x30 = 1`.
- In both canonical tele bridge HDR seeds, a hardware write watchpoint on that
  exact constructed item byte captures a later change to `0`.
- The captured write site is `libcp+0x3c90a5`, with stop PC
  `libcp+0x3c90a9`.
- The writer body is reached under stack `0x3c90a9 <- 0x3b20da <- 0x3b1c65`.
- The static local gate clears item `+0x30` for key `15` when the grouped
  context `+0x44` value is not group ordinal `2`.
- The earlier direct-candidate and stereo-candidate C6 filters are therefore
  observing a post-constructor mutated item state, not the initial state
  produced by `0xf2770`.

## Non-Conclusions

- This does not prove C6 is globally unused.
- This does not prove the `0x3c8f90` byte clear is terminal for all possible C6
  routes.
- This does not exclude alternate C6 paths before this mutation or outside the
  tested direct and stereo-side loops.
- This does not prove public semantic names for item `+0x30`, item `+0x60`,
  context `+0x44`, or the body at `0x3c8f90`.
- This does not identify semantic `src1` / `src2` contents.
- This does not close final merge acceptance / rejection logic.
