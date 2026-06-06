# LLDB Evidence: `0x299c70` Source-Index Worker Formula, Four Zoom

## Scope

This note extends the immediate source-index producer proof in
[lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md).

It proves a narrow internal worker boundary:

- the `0x299c70` dispatch callback address point observed as `0x6680f0`
  resolves through generic executor `0x5440` slot `+0x30` to worker body
  `0x29a670`;
- static extraction bounds `0x29a670` as a tiled `uint16` descriptor writer
  driven by the callback source object at `+0x10`;
- runtime probes under `--no-auto-lris` validate sampled post-write values for
  `28mm`, `35mm`, `70mm`, and `150mm`;
- every accepted focal run reaches six dispatches, one per
  `StereoLayer<false>` index `0..5`, and validates eight pixels from the first
  admitted worker tile per dispatch.

It does not prove public field names, public LRI/protobuf origin, lookup-vector
origin, physical meaning, full-map statistics, final source contribution,
anti-ghosting behavior, or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [worker_formula_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_probe.py)
- Static extractor:
  [static_worker_formula.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/static_worker_formula.lldb)
- Runtime LLDB scripts:
  [worker_formula_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_28mm.lldb),
  [worker_formula_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_35mm.lldb),
  [worker_formula_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_70mm.lldb),
  [worker_formula_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/worker_formula_150mm.lldb)
- Convenience runners:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/run_four_zoom.sh),
  [run_150.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_worker_formula/run_150.sh)
- Raw outputs:
  `runs/codex_299c70_worker_formula/`

The admitted JSON reports and static log have no matches for `Traceback`,
`error:`, `warning:`, `lost connection`, `EXC`, `SIGABRT`, or `SIGSEGV`.

## Static Boundary

Static extraction in
`runs/codex_299c70_worker_formula/static_worker_formula.log` shows the local
callback vtable region:

```text
0x006680f0: 0x000000000029a5e0 0x000000000029a5f0
0x00668100: 0x000000000029a600 0x000000000029a630
0x00668110: 0x000000000029a650 0x000000000029a660
0x00668120: 0x000000000029a670 0x000000000029a800
```

The same static extraction shows generic executor `0x5440` invokes the callable
through slot `+0x30`:

```text
0x54eb  movq -0x78(%rbp), %rax
0x54ef  movq 0x20(%rax), %rdi
0x54fc  movq (%rdi), %rax
0x5506  callq *0x30(%rax)
```

For the `0x299c70` callback address point `0x6680f0`, slot `+0x30` is therefore
the vtable entry at `0x668120`, whose target is `0x29a670`. Runtime packets
below independently read the same slot target from process memory.

## Worker Formula

Static extraction bounds worker `0x29a670` as a tiled `uint16` writer. For each
tile coordinate `(x, y)` in the supplied tile rect:

```text
dest_descriptor = callback + 0x08
source_object   = callback + 0x10

record_base   = *(source_object + 0x10)
source_stride = u32(source_object + 0x38)
offset_table  = *(source_object + 0x40)

record = record_base + u32(offset_table + 4 * (x + y * source_stride))

base  = u16(record + 0x00)
count = u16(record + 0x02)
step  = u16(record + 0x04)
costs = u16[count] at record + 0x08

selected_index = first index with minimum cost, or 0 when count == 0
output_u16 = (base + step * selected_index) & 0xffff
dest[y * dest_stride + x] = output_u16
```

The static store site is:

```text
0x29a7b9  movzwl 0x4(%r15), %eax
0x29a7be  imull %esi, %eax
0x29a7c1  movzwl (%r15), %ecx
0x29a7c5  addl %eax, %ecx
0x29a7c7  movw %cx, (%r14,%r12,2)
```

The runtime probe validates this formula by sampling the first admitted worker
tile for every `0x299c70` dispatch, computing expected `uint16` outputs from
the source records at worker entry, and reading the destination descriptor after
the worker exits.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

| Focal tier | Dispatches | Worker samples | Sampled pixels | Callback AP | Slot target | Formula checks | JSON errors |
|---|---:|---:|---:|---:|---:|---|---:|
| `28mm` | 6 | 6 | 48 | `0x6680f0` | `0x29a670` | pass | 0 |
| `35mm` | 6 | 6 | 48 | `0x6680f0` | `0x29a670` | pass | 0 |
| `70mm` | 6 | 6 | 48 | `0x6680f0` | `0x29a670` | pass | 0 |
| `150mm` | 6 | 6 | 48 | `0x6680f0` | `0x29a670` | pass | 0 |

Total admitted sampled post-write checks: `192 / 192`.

The raw LLDB breakpoint counters can be larger than six for the worker entry
and exit breakpoints because several sibling worker threads may be stopped in a
single process stop. The admitted proof count is the probe's JSON
`worker_sample_count`, which records one formula sample per dispatch.

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet, with same-name LRIS
auto-loading disabled:

```text
StereoLayer<false>+0xf8 source object
  -> 0x299c70 builds a 2-byte descriptor
  -> local callback address point 0x6680f0
  -> generic executor 0x5440 slot +0x30
  -> worker body 0x29a670
  -> per-pixel source-record min-cost selection
  -> uint16 descriptor moved into the 0x267010 source slot
```

This closes the internal callback worker formula for the sampled
`0x299c70` source-index descriptor path. It does not close public semantics or
final merge-quality policy.

## Validation

Validation commands run after the accepted probes:

```text
python3 -m py_compile tools/lldb_probes/codex_299c70_worker_formula/worker_formula_probe.py
python3 <JSON summary validator over the four reports>
file runs/codex_299c70_worker_formula/worker_formula_{28mm,35mm,70mm,150mm}.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' <accepted static log + JSON reports>
```

The JSON summary validator required each focal tier to have exit status `0`,
no step cap, six dispatches, six worker samples, `48` sampled pixels,
callback address point `0x6680f0`, slot target `0x29a670`, no JSON errors, and
all sampled post-write values matching the reconstructed formula.
