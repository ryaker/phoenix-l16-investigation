# LLDB Evidence: `0x29a140` Source-Local Producer, Four Zoom

## Scope

This note extends the tracked index-5 `StereoLayer<false>+0xf8` source-object
custody chain proven in:

- [lldb_index5_source_object_field_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_object_field_origin_four_zoom.md)
- [lldb_index5_source_lookup_origin_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_lookup_origin_watch_four_zoom.md)
- [lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md)
- [lldb_source_index_299c70_worker_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_worker_formula_four_zoom.md)

It narrows the immediate body of `0x29a140`, the helper called at
`0x26be50`, for the tracked index-5 source-object local that is later moved
into `StereoLayer<false>+0xf8`.

## Artifacts

- Runtime probe:
  [source_local_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_probe.py)
- Runtime validator:
  [validate_reports.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/validate_reports.py)
- Runtime LLDB scripts:
  [source_local_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_28mm.lldb),
  [source_local_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_35mm.lldb),
  [source_local_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_70mm.lldb),
  [source_local_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_150mm.lldb)
- Runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/run_four_zoom.sh)
- Raw outputs:
  `runs/codex_29a140_source_local_producer/`

## Non-Admitted Attempts

- Non-elevated LLDB launches failed with `lost connection` before useful
  runtime packets. Direct `lri_process` rendering outside LLDB completed, so
  this was not treated as a binary/LRI failure.
- A first dynamic-breakpoint variant installed all deep sites immediately after
  the index-5 setter. It completed `28mm`, `35mm`, and `70mm`, but the `150mm`
  run stopped at the known instrumentation-sensitive `EXC_BAD_ACCESS` surface
  and wrote an empty HDR. That packet is rejected.
- A second delayed-six-setter variant rendered all four tiers but captured no
  target producer sites. Those packets are rejected.
- The admitted probe launches with only the index setter, installs one
  `0x26be50` caller-pre breakpoint after the tracked object is known, and
  installs the deep `0x29a140`/continuity breakpoints only at the verified
  caller-pre hit.

## Static Boundary

Fresh static extraction of `0x29a140..0x29a1c8` was captured under
`runs/codex_29a140_source_local_producer/static_29a140_29a1c8.log`.

The static body:

```text
0x29a14b  movq %rdx, %r15
0x29a14e  movq %rsi, %r12
0x29a151  movq %rdi, %rbx
0x29a154  movl %ecx, (%rbx)
0x29a156  leaq 0x8(%rbx), %r14
0x29a15a..0x29a16d zero output local +0x08..+0x48
0x29a175  movq %r12, %rdi
0x29a178  movq %r15, %rsi
0x29a17b  movl %ecx, %edx
0x29a17d  callq 0x299eb0
0x29a182  movl $0x40, %edx
0x29a187  movq %r14, %rdi
0x29a18a  movq %rax, %rsi
0x29a18d  callq 0x28f490
0x29a192  movq %rbx, %rdi
0x29a195  movq %r12, %rsi
0x29a198  movq %r15, %rdx
0x29a19b  callq 0x299fd0
```

Static fact only: `0x29a140` stores the incoming low `ecx` control value into
the output local, zeroes output-local fields `+0x08..+0x48`, calls `0x299eb0`
with the input descriptor, target `+0x208`, and control value, calls `0x28f490`
with destination `output+0x08`, `rsi = rax`, and `edx = 0x40`, then calls
`0x299fd0` with output local, input descriptor, and target `+0x208`.

Fresh static extraction of `0x299eb0..0x29a140` was captured under
`runs/codex_29a140_source_local_producer/static_299eb0_29a140.log` and
`runs/codex_29a140_source_local_producer/static_299fd0_29a140.log`.

The static `0x299eb0` loop:

- checks that the input descriptor and `target+0x208` descriptor have matching
  width and height;
- iterates over input width and height;
- reads the second `uint16` from each 4-byte input entry;
- rounds that value up to the incoming control value;
- reads the corresponding mask byte from `target+0x208`;
- accumulates `8 + factor * rounded`, where the visible branch uses factor
  `2` for nonzero mask bytes and factor `3` for zero mask bytes;
- returns the accumulated byte span in `rax`.

The static `0x299fd0` loop:

- builds the output descriptor from the input descriptor dimensions;
- iterates over the same width and height;
- writes the current record offset into the output offset table;
- writes record header fields `(input_u16_0, input_u16_2, 1, rounded)` at
  `record_base + offset`;
- advances the current record pointer by the same
  `8 + factor * rounded` formula.

## Runtime Result

All accepted runs used:

```text
--profile 3 --export-fmt 3 --no-auto-lris
```

All accepted runs exited with status `0`, avoided the drive step cap, had empty
probe `errors`, and emitted files identified by `file` as `Radiance HDR image
data`.

Each accepted run recorded exactly one target sample at every required
boundary:

- `0x26be50` caller-pre edge;
- `0x29a140` entry;
- `0x29a182` after `0x299eb0`;
- `0x29a192` after the `0x28f490` header helper;
- `0x29a1a0` after `0x299fd0`;
- `0x26be55` caller-post edge;
- `0x26be73` header move into `this+0x100`;
- `0x26be89` descriptor move into `this+0x118`;
- later continuity sites `0x26e4c6`, `0x299c70`, and `0x267010`.

At the caller-pre and `0x29a140` entry boundaries, the tracked runtime
arguments match the static setup:

```text
rdi = caller rbp - 0xb0
rsi = caller rbp - 0x60
rdx = tracked StereoLayer<false> + 0x208
ecx = 8
```

Observed output-local transitions:

- after `0x299eb0`, output control is `8`, and the sampled header qwords at
  output `+0x08..+0x20` are still zero;
- after `0x28f490`, output `+0x08` is populated while the descriptor at
  output `+0x20` is still zero-sized;
- after `0x299fd0`, output control is still `8`, the descriptor at output
  `+0x20` is populated as `2080 x 1560`, stride `2080`, field `0x1c = 1560`,
  and sampled record-base / offset-table data are readable;
- at caller post-`0x29a140`, the output local matches the post-`0x299fd0`
  sample exactly.

Record samples after `0x299fd0`:

| Focal tier | Record-base pointer | Offset-table pointer | First offsets | First sampled record |
|---|---:|---:|---|---|
| `28mm` | nonzero | nonzero | `[0, 56, 96, 136]` | `(205, 9, 1, 16)` |
| `35mm` | nonzero | nonzero | `[0, 32, 56, 80]` | `(25, 4, 1, 8)` |
| `70mm` | nonzero | nonzero | `[0, 32, 56, 80]` | `(9, 8, 1, 8)` |
| `150mm` | nonzero | nonzero | `[0, 32, 56, 80]` | `(19, 5, 1, 8)` |

The sampled record values are admitted only as runtime samples, not as stable
semantic constants.

Formula validation:

The rerun validator now computes the full byte-span formula directly from live
process memory at the `0x299eb0` return boundary. It reads the complete
`2080 x 1560` 4-byte input descriptor and complete `2080 x 1560` byte mask
descriptor at `target+0x208`, computes the formula below for every pixel, and
requires the result to match both the `0x299eb0` return and the final output
header span after `0x299fd0`.

```text
rounded = ceil(input_u16_2 / control) * control
factor = 2 if mask_byte != 0 else 3
record_size = 8 + factor * rounded
```

The same validator also requires the first eight output-table offsets and first
eight record headers to match the reconstructed formula.

| Focal tier | Computed / returned span | Mask zero / nonzero | First mask bytes | First expected records `(offset,u0,u2,one,rounded,factor,size)` |
|---|---:|---:|---|---|
| `28mm` | `89124024` | `811200 / 2433600` | `[0, 255, 255, 255, 255, 255, 255, 255]` | `(0,205,9,1,16,3,56)`, `(56,205,9,1,16,2,40)`, `(96,205,9,1,16,2,40)`, `(136,205,9,1,16,2,40)`, `(176,205,9,1,16,2,40)`, `(216,205,9,1,16,2,40)`, `(256,205,9,1,16,2,40)`, `(296,205,9,1,16,2,40)` |
| `35mm` | `96477512` | `811200 / 2433600` | `[0, 255, 255, 255, 255, 255, 255, 255]` | `(0,25,4,1,8,3,32)`, `(32,25,4,1,8,2,24)`, `(56,25,4,1,8,2,24)`, `(80,25,4,1,8,2,24)`, `(104,25,4,1,8,2,24)`, `(128,25,2,1,8,2,24)`, `(152,25,2,1,8,2,24)`, `(176,25,2,1,8,2,24)` |
| `70mm` | `109755992` | `811200 / 2433600` | `[0, 255, 255, 255, 255, 255, 255, 255]` | `(0,9,8,1,8,3,32)`, `(32,9,8,1,8,2,24)`, `(56,9,8,1,8,2,24)`, `(80,9,8,1,8,2,24)`, `(104,9,8,1,8,2,24)`, `(128,8,9,1,16,2,40)`, `(168,8,9,1,16,2,40)`, `(208,8,9,1,16,2,40)` |
| `150mm` | `86353544` | `811200 / 2433600` | `[0, 255, 255, 255, 255, 255, 255, 255]` | `(0,19,5,1,8,3,32)`, `(32,19,5,1,8,2,24)`, `(56,19,5,1,8,2,24)`, `(80,19,5,1,8,2,24)`, `(104,19,5,1,8,2,24)`, `(128,22,3,1,8,2,24)`, `(152,22,3,1,8,2,24)`, `(176,22,3,1,8,2,24)` |

The follow-on moves and continuity also validate:

- `0x26be73 -> 0x28f420`: source is output local `+0x08`, destination is
  `tracked StereoLayer<false>+0x100`;
- `0x26be89 -> 0xf340`: source is output local `+0x20`, destination is
  `tracked StereoLayer<false>+0x118`;
- later `0x299c70` receives `rsi == tracked this+0xf8`;
- later `0x267010` receives `rdx == tracked this+0xe0`.

## Proven Narrow Claim

For the tracked index-5 `StereoLayer<false>` object, `0x29a140` is now bounded
as the immediate source-local producer body behind the previously proven
`0x26be50` field-assembly edge:

```text
caller rbp-0xb0 / source local
  +0x00 control = 8
  +0x08 header region populated by static 0x28f490 call following 0x299eb0
        header span equals the full byte span computed from the live input
        descriptor and target+0x208 mask descriptor
  +0x20 descriptor/record fields populated by 0x299fd0
        descriptor = 2080 x 1560, stride 2080
        first eight offsets/record headers match the reconstructed formula

caller rbp-0xb0 +0x08 -> this+0x100 by 0x28f420
caller rbp-0xb0 +0x20 -> this+0x118 by 0xf340
this+0xf8 / this+0xe0 later continue into the proven 0x299c70 -> 0x267010 path
```

For this tracked path, the admitted mechanics are:

```text
rounded = ceil(input_u16_2 / 8) * 8
factor = 2 if target_plus_0x208_mask_byte != 0 else 3
record_size = 8 + factor * rounded
record_header = (input_u16_0, input_u16_2, 1, rounded)
```

## Non-Claims

- This proof does not decode public LRI/protobuf field origins.
- This proof does not name the public physical quantity represented by the
  produced descriptor or lookup/source object.
- This proof does not prove that the sampled record values are constants.
- This proof does not name public semantics for `0x299eb0`, `0x299fd0`, the
  4-byte input entries, the `target+0x208` mask bytes, or the output records.
- This proof does not prove exact `0x28f490` helper semantics beyond the
  observed header-population boundary.
- This proof does not prove final source contribution, anti-ghosting behavior,
  or final acceptance/rejection.

## Validation

Validation commands:

```text
python3 -m py_compile tools/lldb_probes/codex_29a140_source_local_producer/source_local_probe.py tools/lldb_probes/codex_29a140_source_local_producer/validate_reports.py
python3 tools/lldb_probes/codex_29a140_source_local_producer/validate_reports.py
file runs/codex_29a140_source_local_producer/source_local_28mm.hdr runs/codex_29a140_source_local_producer/source_local_35mm.hdr runs/codex_29a140_source_local_producer/source_local_70mm.hdr runs/codex_29a140_source_local_producer/source_local_150mm.hdr
git diff --check
```

Validator output:

```text
source_local_150mm.json: OK target=0x7f950c70e210 record_base=0x7f9474dac040 offset_table=0x7f94dd364040 first_offsets=[0, 32, 56, 80]
source_local_28mm.json: OK target=0x7fe00f910cf0 record_base=0x7fdf2ef00040 offset_table=0x7fdfd8000040 first_offsets=[0, 56, 96, 136]
source_local_35mm.json: OK target=0x7ff2c07179f0 record_base=0x7ff2155d8040 offset_table=0x7ff291364040 first_offsets=[0, 32, 56, 80]
source_local_70mm.json: OK target=0x7fe45612e470 record_base=0x7fe375700040 offset_table=0x7fe416364040 first_offsets=[0, 32, 56, 80]
```
