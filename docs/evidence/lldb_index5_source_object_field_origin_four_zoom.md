# LLDB Evidence: Index-5 Source-Object Field Origin, Four Zoom

## Scope

This note extends the index-5 source/lookup custody chain:

- [lldb_index5_source_lookup_origin_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_lookup_origin_watch_four_zoom.md)
- [lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md)
- [lldb_source_index_299c70_worker_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_worker_formula_four_zoom.md)

It proves the immediate internal assembly path for the tracked index-5
`StereoLayer<false>+0xf8` source object consumed by `0x299c70`:

- callsite `0x26be50 -> 0x29a140` produces stack locals at `rbp-0xb0`,
  `rbp-0xa8`, and `rbp-0x90`;
- `0x26be5b` writes the low 32-bit source-control value from `rbp-0xb0` into
  `StereoLayer<false>+0xf8`;
- callsite `0x26be73 -> 0x28f420` moves the three-qword header from
  `rbp-0xa8` into `StereoLayer<false>+0x100`;
- callsite `0x26be89 -> 0xf340` moves the descriptor from `rbp-0x90` into
  `StereoLayer<false>+0x118`;
- the assembled same object later reaches `0x26e4c6`, `0x299c70`, and
  `0x267010` with the already proven `this+0xf8` / `this+0xe0` relationships.

It does not prove public field names, public LRI/protobuf origin, public
calibration semantics, physical meaning, full-map statistics, final source
contribution, anti-ghosting behavior, or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [field_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_object_field_origin/field_origin_probe.py)
- Runtime LLDB scripts:
  [source_object_field_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_object_field_origin/source_object_field_28mm.lldb),
  [source_object_field_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_object_field_origin/source_object_field_35mm.lldb),
  [source_object_field_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_object_field_origin/source_object_field_70mm.lldb),
  [source_object_field_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_object_field_origin/source_object_field_150mm.lldb)
- Raw outputs:
  `runs/codex_index5_source_object_field_origin/`

The first attempted run enabled all deep breakpoints before the target index-5
object was known and failed at launch with LLDB `lost connection`. That attempt
is not admitted. The admitted probe defers all deep breakpoints until the
index-5 setter is observed, and all four accepted runs exit cleanly.

The admitted JSON reports have no matches for `Traceback`, `error:`,
`warning:`, `lost connection`, `EXC`, `SIGABRT`, or `SIGSEGV`.

## Static Boundary

Static extraction around `0x26bd90` shows the local source-object assembly
sequence:

```text
0x26be45  leaq -0xb0(%rbp), %rdi
0x26be4c  leaq -0x60(%rbp), %rsi
0x26be50  callq 0x29a140
0x26be55  movl -0xb0(%rbp), %eax
0x26be5b  movl %eax, 0xf8(%r14)
0x26be62  leaq 0x100(%r14), %rdi
0x26be69  leaq -0xa8(%rbp), %r15
0x26be70  movq %r15, %rsi
0x26be73  callq 0x28f420
0x26be78  leaq 0x118(%r14), %rdi
0x26be7f  leaq -0x90(%rbp), %rbx
0x26be86  movq %rbx, %rsi
0x26be89  callq 0xf340
```

Static extraction of `0x28f420` shows it moves three qwords from `rsi` to
`rdi`, then clears the source local:

```text
0x28f457  movq (%r14), %rax
0x28f45a  movq %rax, (%rbx)
0x28f45d  movq 0x10(%r14), %rax
0x28f461  movq %rax, 0x10(%rbx)
0x28f465  movq 0x8(%r14), %rax
0x28f469  movq %rax, (%r15)
0x28f46c  xorps %xmm0, %xmm0
0x28f46f  movups %xmm0, (%r14)
0x28f473  movq $0x0, 0x10(%r14)
```

Static extraction of `0xf340` shows descriptor move/swap mechanics over the
descriptor fields through `+0x28`, including the width/height/stride fields at
descriptor offsets `+0x10`, `+0x14`, and `+0x18`, plus pointer fields at
`+0x20` and `+0x28`.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

Each accepted run recorded one target index-5 sample at each deep boundary and
one later target sample at `0x26e4c6`, `0x299c70`, and `0x267010`.

| Focal tier | `0x29a140` output control | Object control before / after `0x26be5b` | Header move | Descriptor move | Later continuity | Output |
|---|---:|---|---|---|---|---|
| `28mm` | 8 | `2 -> 8` | `rbp-0xa8 -> this+0x100` | `rbp-0x90 -> this+0x118` | pass | Radiance HDR |
| `35mm` | 8 | `2 -> 8` | `rbp-0xa8 -> this+0x100` | `rbp-0x90 -> this+0x118` | pass | Radiance HDR |
| `70mm` | 8 | `2 -> 8` | `rbp-0xa8 -> this+0x100` | `rbp-0x90 -> this+0x118` | pass | Radiance HDR |
| `150mm` | 8 | `2 -> 8` | `rbp-0xa8 -> this+0x100` | `rbp-0x90 -> this+0x118` | pass | Radiance HDR |

At the `0x26be50 -> 0x29a140` callsite, the tracked index-5 runtime arguments
match the static setup:

```text
rdi = rbp - 0xb0
rsi = rbp - 0x60
rdx = this + 0x208
ecx = 8
```

For every accepted focal tier:

- `rbp-0xb0` contains low `u32 = 8` after `0x29a140`;
- the destination object's `+0xf8` low `u32` is `2` before `0x26be5b` and `8`
  after `0x26be5b`;
- `rbp-0xa8` contains a nonzero three-qword header before `0x28f420`;
- after `0x28f420`, that three-qword header is present at
  `StereoLayer<false>+0x100`, and the stack local is zeroed;
- `rbp-0x90` contains a descriptor with width `2080`, height `1560`, stride
  `2080`, field `0x1c = 1560`, and nonzero pointer fields before `0xf340`;
- after `0xf340`, that descriptor is present at `StereoLayer<false>+0x118`,
  and the stack local descriptor is zeroed.

## Proven Field Custody

For the tracked index-5 `StereoLayer<false>` object:

```text
source object base = this + 0xf8

source_object + 0x00
  <- low u32 from rbp-0xb0, produced before 0x26be55 by 0x29a140
  <- observed final value 8

source_object + 0x08..0x18
  <- three-qword header moved from rbp-0xa8 by 0x28f420
  <- source_object + 0x10 is the record-base pointer consumed by 0x299c70

source_object + 0x20..0x48
  <- descriptor moved from rbp-0x90 by 0xf340
  <- descriptor width/height/stride = 2080 / 1560 / 2080
  <- source_object + 0x38 is the stride consumed by 0x299c70
  <- source_object + 0x40 is the offset-table pointer consumed by 0x299c70
```

Later target samples prove continuity into the already admitted consumer chain:

- `0x26e4c6`: `rdx == this+0xf8`;
- `0x299c70`: `rsi == this+0xf8`;
- `0x267010`: `rdx == this+0xe0`.

## Non-Claims

- This proof does not identify public LRI/protobuf field names.
- This proof does not classify the public meaning of control value `8`.
- This proof does not decode the full body or public semantics of `0x29a140`.
- This proof does not prove metric depth, disparity, inverse depth, confidence,
  or any other physical quantity.
- This proof does not prove final source contribution, anti-ghosting behavior,
  or final acceptance/rejection.

## Validation

Validation commands run after the accepted probes:

```text
python3 -m py_compile tools/lldb_probes/codex_index5_source_object_field_origin/field_origin_probe.py
python3 <schema-aware JSON validator over the four accepted reports>
file runs/codex_index5_source_object_field_origin/source_object_field_{28mm,35mm,70mm,150mm}.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' <accepted JSON reports>
git diff --check
```

The JSON validator required each focal tier to have exit status `0`, no step
cap, empty `errors`, one target sample at every deep field-origin boundary,
control value transition `2 -> 8`, valid `rbp-0xa8 -> this+0x100` header move,
valid `rbp-0x90 -> this+0x118` descriptor move, descriptor dimensions
`2080 x 1560` with stride `2080`, and later `0x26e4c6` / `0x299c70` /
`0x267010` continuity.
