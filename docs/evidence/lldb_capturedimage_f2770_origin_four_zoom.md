# LLDB Evidence: `0xf2770` Captured-Item Constructor Inputs Across Four Zooms

**Date:** 2026-05-26
**Status:** admitted evidence candidate for `CLM-PREFUSION-001`,
`CLM-PREFUSION-002`, and `CLM-C6-001`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This proof captures the direct runtime callsite that constructs the item records
later scanned by the `FusionCacheBayer` selector and C6 candidate gates. The
tested question is intentionally narrow:

What input record fields enter `0xf2770`, and what item fields are present
immediately after `0xf2770` returns, before later candidate loops observe those
items?

This closes constructor-time custody for the tested item fields. It does not
name public LRI fields or prove final merge acceptance/rejection behavior.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness:

- [f2770_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_probe.py)

LLDB scripts:

- [f2770_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_28mm.lldb)
- [f2770_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_35mm.lldb)
- [f2770_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_70mm.lldb)
- [f2770_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/capturedimage_f2770_origin/`.
Each run produced a `311M` HDR output file, so this probe is output-completion
evidence for the four tested seeds.

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_28mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_35mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_150mm.lldb
```

## Static Anchor

Installed-bundle disassembly identifies the direct constructor callsite inside
`libcp+0xe52c0`:

```asm
0xe5967  movq   0x28(%rbx), %rax
0xe596b  movq   0x8(%rax,%rcx,8), %r14
0xe5970  movl   $0x230, %edi
0xe5975  callq  operator new(unsigned long)
0xe597a  movq   %rax, %r13
0xe5990  movq   %r13, %rbx
0xe5993  addq   $0x20, %rbx
0xe5997  movq   %rbx, %rdi
0xe599a  movq   %r14, %rsi
0xe599d  movq   -0x310(%rbp), %rdx
0xe59a4  callq  0xf2770
0xe59a9  movq   %rbx, -0x258(%rbp)
0xe59b0  movq   %r13, -0x250(%rbp)
0xe59c5  callq  0xe3240
```

The probe captures pre-call input fields at `0xe59a4` and post-return item
fields at `0xe59a9`.

Prior static proof already bounded relevant `0xf2770` assignments:

- `0xf27a1..0xf27ad` reads input `+0x30`, calls `0x137d70`, and stores the
  range-checked camera ID to item `+0x60`.
- `0xf27b0..0xf27b4` copies input byte `+0x60` to item `+0x30`.
- `0xf2d4c..0xf2d71` can read the record at input `+0x28` and decode its
  `+0x18` qword as two int32 fields for item `+0x58/+0x5c`.

## Runtime Counts

| Zoom | JSON report | Pre-call hits | Post-return hits | Captured events |
|---|---|---:|---:|---:|
| `28mm` | `runs/capturedimage_f2770_origin/f2770_origin_28mm.json` | `10` | `10` | `10` |
| `35mm` | `runs/capturedimage_f2770_origin/f2770_origin_35mm.json` | `10` | `10` | `10` |
| `70mm` | `runs/capturedimage_f2770_origin/f2770_origin_70mm.json` | `11` | `11` | `11` |
| `150mm` | `runs/capturedimage_f2770_origin/f2770_origin_150mm.json` | `11` | `11` | `11` |

## Constructor Output Summary

| Zoom | Constructed item keys at output `+0x60` | Initial output `+0x30` active byte | Sign-bit pair key |
|---|---|---|---|
| `28mm` | `0,4,6,8,9,1,2,3,5,7` | all `1` | key `1` has `(-1,-1)` |
| `35mm` | `0,4,6,8,9,1,2,3,5,7` | all `1` | key `1` has `(-1,-1)` |
| `70mm` | `6,8,9,14,5,7,11,10,12,13,15` | all `1` | key `15` has `(-1,-1)` |
| `150mm` | `6,8,9,14,5,7,11,10,12,13,15` | all `1` | key `15` has `(-1,-1)` |

For every captured item in the four runs, input `+0x30` equals output item
`+0x60`. This is runtime confirmation of the static `input+0x30 ->
0x137d70 -> item+0x60` path under the canonical bridge HDR seeds.

For every captured item in the four runs, the record at input `+0x28`, read at
`+0x18` as two int32 fields, already contains the same pair later observed at
item `+0x58/+0x5c`. This confirms runtime custody for those two-int fields
under the tested constructor callsite.

The wide sign-bit item is key `1`; the tele sign-bit item is key `15` / C6.
Both are constructed with output item type field `+0x100 = 3`.

## Per-Key Pair Values

The wide `28mm` and `35mm` constructor outputs are identical in key/pair shape:

| Key | Output `+0x58/+0x5c` | Initial active byte `+0x30` |
|---:|---|---:|
| `0` | `(1,0)` | `1` |
| `4` | `(0,1)` | `1` |
| `6` | `(1,1)` | `1` |
| `8` | `(1,1)` | `1` |
| `9` | `(0,0)` | `1` |
| `1` | `(-1,-1)` | `1` |
| `2` | `(1,0)` | `1` |
| `3` | `(1,0)` | `1` |
| `5` | `(0,0)` | `1` |
| `7` | `(1,1)` | `1` |

The tele `70mm` and `150mm` constructor outputs are identical in key/pair
shape:

| Key | Output `+0x58/+0x5c` | Initial active byte `+0x30` |
|---:|---|---:|
| `6` | `(1,1)` | `1` |
| `8` | `(1,1)` | `1` |
| `9` | `(0,0)` | `1` |
| `14` | `(1,1)` | `1` |
| `5` | `(0,0)` | `1` |
| `7` | `(1,1)` | `1` |
| `11` | `(1,1)` | `1` |
| `10` | `(0,0)` | `1` |
| `12` | `(0,0)` | `1` |
| `13` | `(1,1)` | `1` |
| `15` | `(-1,-1)` | `1` |

## Proven Facts

- The `0xe59a4 -> 0xf2770` constructor callsite is live under all four
  canonical bridge HDR seeds.
- The tested wide seeds construct `10` items; the tested tele seeds construct
  `11` items.
- For every captured item, input `+0x30` equals post-constructor item `+0x60`.
- For every captured item, the two-int value available at input `+0x28/+0x18`
  matches post-constructor item `+0x58/+0x5c`.
- Key `1` is constructed with pair `(-1,-1)` and active byte `1` in both wide
  seeds.
- Key `15` / C6 is constructed with pair `(-1,-1)` and active byte `1` in both
  tele seeds.
- Therefore, later observations of tele key `15` with `object+0x30 = 0` cannot
  be constructor-birth state from this `0xf2770` callsite; they require a later
  mutation or replacement.

## Non-Conclusions

- This does not prove public semantic names for input `+0x30`, input `+0x60`,
  input `+0x28`, item `+0x30`, item `+0x58/+0x5c`, item `+0x60`, or item
  `+0x100`.
- This does not prove the LRI protobuf field numbers for those runtime fields.
- This does not prove C6 is globally unused.
- This does not prove an alternate C6 destination does or does not exist.
- This does not identify semantic `src1` / `src2` contents.
- This does not close final merge acceptance / rejection logic.
