# LLDB Proof: Final CLI HDR Writer Boundary Across Four Zooms

## Scope

This proof follows the case-`3` helper handoff from
`0x4182a0 -> 0x41e180 -> 0x2326a0` under the canonical CLI bridge-HDR export
path.

It proves only tested-path writer-boundary reachability and raw descriptor /
extension custody for:

- helper `0x41e180`;
- the live `.hdr` branch inside `0x41e180`;
- call edge `0x41e599 -> 0x2326a0`;
- writer helper `0x2326a0`;
- virtual writer callsite `0x232731`;
- selected normal-return and error/alternate-branch bounds.

It does not prove pixel correctness, copy-vs-blend behavior, anti-ghosting
policy, source contribution, final merge acceptance/rejection, or any non-CLI
display/export sink.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_boundary_probe.py`
- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_28mm.lldb`
- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_35mm.lldb`
- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_70mm.lldb`
- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_150mm.lldb`
- `tools/lldb_probes/codex_final_output_hdr_writer_boundary/run_four_zoom.sh`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_28mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_35mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_70mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_150mm.json`
- `runs/codex_final_output_hdr_writer_boundary/static_41e180_hdr_writer_window.txt`
- `runs/codex_final_output_hdr_writer_boundary/static_2326a0_writer_boundary.txt`
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

The installed-bundle disassembly for helper `0x41e180` starts by saving the
case-`3` arguments and checking the export dimensions:

```asm
0x41e194  movq %r9, %r15
0x41e197  movl %r8d, %r14d
0x41e19a  movq %rdx, %r12
0x41e1ae  movl (%r12), %eax
0x41e1b2  testl %eax, %eax
0x41e1b4  jle 0x41fad4
0x41e1ba  movl 0x4(%r12), %edx
0x41e1bf  testl %edx, %edx
0x41e1c1  jle 0x41fad4
```

The live CLI HDR branch initializes literal `.hdr`, passes a descriptor and the
third case-`3` argument to `0x2326a0`, then cleans up and returns through the
normal return path:

```asm
0x41e546  cmpl $0x3, %r14d
0x41e54a  jne 0x41e953
0x41e565  leaq ".hdr", %rsi
0x41e599  callq 0x2326a0
0x41e5aa  jmp 0x41ea07
0x41ea07  leaq -0x780(%rbp), %rdi
0x41f9eb  addq $0x888, %rsp
0x41f9fc  retq
```

The installed-bundle disassembly for `0x2326a0` is writer-shaped: it checks
descriptor data, constructs a writer object from the extension argument, builds
a local descriptor with width, height, row bytes, bytes-per-pixel, and data
pointer, then invokes a virtual call:

```asm
0x2326a0  pushq %rbp
0x2326ad  movq %rdx, %r15
0x2326b0  movq %rsi, %r14
0x2326b3  movq %rdi, %rbx
0x2326b6  cmpq $0x0, 0x20(%rbx)
0x2326ec  leaq -0x58(%rbp), %rdi
0x2326f0  movq %r14, %rsi
0x2326f3  callq 0x1b1d0
0x232703  movl 0x10(%rbx), %ecx
0x232709  movl 0x14(%rbx), %ecx
0x23270f  movslq 0x18(%rbx), %rcx
0x232713  shlq $0x4, %rcx
0x23271b  movl $0x10, -0x68(%rbp)
0x232722  movq 0x20(%rbx), %rcx
0x23272e  movq %r15, %rsi
0x232731  callq *%rax
0x23274a  movq %rbx, %rax
0x232757  retq
```

The static excerpt also locates the no-data error path at `0x232758`, the
unexpected export-format error path at `0x41fa93`, and the invalid-size error
path at `0x41fad4`. These static excerpts are bounded evidence for this
installed binary only.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap. Each output file was also checked with the OS `file` command and
reported as `Radiance HDR image data`.

| Zoom | Exit | State | Errors | Step cap | Drive steps | OS file type |
|---|---:|---|---:|---|---:|---|
| `28mm` | 0 | `exited` | 0 | `False` | 17 | `Radiance HDR image data` |
| `35mm` | 0 | `exited` | 0 | `False` | 17 | `Radiance HDR image data` |
| `70mm` | 0 | `exited` | 0 | `False` | 17 | `Radiance HDR image data` |
| `150mm` | 0 | `exited` | 0 | `False` | 17 | `Radiance HDR image data` |

| Site | Name | 28mm | 35mm | 70mm | 150mm |
|---|---|---:|---:|---:|---:|
| `0x41e180` | helper `0x41e180` entry | 1 | 1 | 1 | 1 |
| `0x41e1ae` | dimension guard width read | 1 | 1 | 1 | 1 |
| `0x41e1de` | export-format branch | 1 | 1 | 1 | 1 |
| `0x41e430` | export jump dispatch | 1 | 1 | 1 | 1 |
| `0x41e4e6` | HDR branch candidate | 1 | 1 | 1 | 1 |
| `0x41e546` | HDR format check | 1 | 1 | 1 | 1 |
| `0x41e565` | `.hdr` string init | 1 | 1 | 1 | 1 |
| `0x41e599` | call `0x2326a0` | 1 | 1 | 1 | 1 |
| `0x41e5aa` | after `0x2326a0` | 1 | 1 | 1 | 1 |
| `0x41e953` | PPM branch target | 0 | 0 | 0 | 0 |
| `0x41e9ea` | PPM writer call | 0 | 0 | 0 | 0 |
| `0x41ea07` | cleanup after HDR/PPM | 1 | 1 | 1 | 1 |
| `0x41f9eb` | helper normal return | 1 | 1 | 1 | 1 |
| `0x41fa93` | unexpected export-format error | 0 | 0 | 0 | 0 |
| `0x41fad4` | invalid export-size error | 0 | 0 | 0 | 0 |
| `0x2326a0` | writer helper entry | 1 | 1 | 1 | 1 |
| `0x2326b6` | descriptor data check | 1 | 1 | 1 | 1 |
| `0x2326ec` | writer factory call | 1 | 1 | 1 | 1 |
| `0x232731` | virtual writer call | 1 | 1 | 1 | 1 |
| `0x232733` | after virtual writer call | 1 | 1 | 1 | 1 |
| `0x23274a` | writer helper normal return | 1 | 1 | 1 | 1 |
| `0x232758` | no-data error path | 0 | 0 | 0 | 0 |

## Descriptor And Extension Observations

At the `0x41e599 -> 0x2326a0` call edge, all four admitted runs pass a decoded
short-string extension `.hdr`, a populated descriptor, and the same opaque third
argument later passed into the virtual writer call. The third argument is kept
opaque because it did not decode as a valid string in this probe.

| Zoom | Entry dims | Format arg | Extension | Descriptor dims | Descriptor stride/count | Data pointer nonzero | Virtual row bytes | Virtual bytes/pixel |
|---|---|---:|---|---|---:|---|---:|---:|
| `28mm` | `10432 x 7824` | 3 | `.hdr` | `10432 x 7824` | 10432 | `True` | 166912 | 16 |
| `35mm` | `10432 x 7824` | 3 | `.hdr` | `10432 x 7824` | 10432 | `True` | 166912 | 16 |
| `70mm` | `10432 x 7824` | 3 | `.hdr` | `10432 x 7824` | 10432 | `True` | 166912 | 16 |
| `150mm` | `10432 x 7824` | 3 | `.hdr` | `10432 x 7824` | 10432 | `True` | 166912 | 16 |

`166912 = 10432 * 16`, matching the static `0x23270f..0x232713` row-byte
construction. The descriptor table records raw descriptor shape only; it does
not prove pixel layout semantics beyond the captured bytes-per-pixel field.

## Proven Facts

- Under the canonical CLI bridge-HDR quartet, case-`3` helper `0x41e180` is
  reached once per render with entry dimensions `10432 x 7824` and export
  format argument `3`.
- Under those admitted runs, `0x41e180` reaches the `.hdr` branch, initializes
  decoded short-string extension `.hdr`, calls `0x2326a0` at `0x41e599`, reaches
  cleanup `0x41ea07`, and reaches normal-return site `0x41f9eb`.
- Under those admitted runs, the PPM branch target `0x41e953`, PPM writer call
  `0x41e9ea`, unexpected export-format path `0x41fa93`, and invalid export-size
  path `0x41fad4` record zero hits.
- Under those admitted runs, writer helper `0x2326a0` receives a populated
  descriptor with width `10432`, height `7824`, stride/count field `10432`, a
  nonzero data pointer, and decoded extension `.hdr`.
- Under those admitted runs, `0x2326a0` reaches descriptor data check
  `0x2326b6`, writer-factory call `0x2326ec`, virtual writer call `0x232731`,
  after-call site `0x232733`, and normal-return site `0x23274a` once per
  render, while no-data error path `0x232758` records zero hits.
- The virtual writer-call descriptor has width `10432`, height `7824`, row
  bytes `166912`, bytes-per-pixel field `16`, and the same nonzero data pointer
  across all four admitted runs.
- The emitted files in `runs/codex_final_output_hdr_writer_boundary/` identify
  as `Radiance HDR image data` under the OS `file` command.

## Non-Claims

- Zero-hit findings are scoped to the tested canonical CLI bridge-HDR quartet;
  they are not universal "never fires" claims for every Lumen path.
- This proof does not identify public names or semantics for the opaque third
  argument passed through `0x41e599 -> 0x2326a0 -> 0x232731`.
- This proof does not classify every body reached by `0x41e180`, `0x2326a0`,
  writer factory `0x1b1d0`, or the virtual writer target.
- This proof does not prove pixel correctness, copy-vs-blend behavior,
  anti-ghosting policy, source contribution, or final merge
  acceptance/rejection.
- This proof is scoped to the tested CLI HDR export path. It does not prove
  other export formats, display sinks, preview sinks, or GUI-only sinks.

## Operational Note

These admitted LLDB runs were executed outside the Codex sandbox because
sandboxed `debugserver` was denied the task port for `lri_process` on this
machine. That environment note is not evidence about `libcp` behavior.
