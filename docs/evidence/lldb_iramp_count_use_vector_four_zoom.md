# LLDB IRAMP Count-Use Vector Evidence

**Date:** 2026-06-04
**Status:** Runtime evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local `lri_process`, and the
canonical four-zoom bridge HDR quartet with `--no-auto-lris`.

This document proves a narrow runtime fact inside the terminal IRAMP body:
the instruction window at `0x366a50..0x366a65` reads a vector header through
`r15+0x18`, computes `(end - begin) / 16`, and reaches `0x366a65` with live
`rbx == 5` on sampled packets for all four canonical focal tiers.

It does not prove public vector semantics, complete contributor distributions,
the full `0x3661b0` reducer, `src1` / `src2` semantics, or final
acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harness:

- `tools/lldb_probes/codex_iramp_count_use_validation/count_use_probe.py`
- `tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_28mm.lldb`
- `tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_35mm.lldb`
- `tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_70mm.lldb`
- `tools/lldb_probes/codex_iramp_count_use_validation/iramp_count_use_150mm.lldb`
- `tools/lldb_probes/codex_iramp_count_use_validation/run_four_zoom.sh`

Generated raw reports and HDR outputs live under ignored local directory:

- `runs/codex_iramp_count_use_validation/`

No live `/tmp` or `/private/tmp` artifact is cited by this evidence.

The run command was:

```bash
bash tools/lldb_probes/codex_iramp_count_use_validation/run_four_zoom.sh
```

Each LLDB script launched:

```text
process launch -- "<LRI>" "<repo>/runs/codex_iramp_count_use_validation/<out>.hdr" --profile 3 --export-fmt 3 --no-auto-lris
```

## Static Instruction Window

Fresh installed-bundle disassembly of
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
shows:

```asm
0x366a50  movq  0x18(%r15), %rcx
0x366a54  movq  (%rcx), %rax
0x366a57  movq  0x8(%rcx), %rcx
0x366a5b  movq  %rcx, %rbx
0x366a5e  subq  %rax, %rbx
0x366a61  sarq  $0x4, %rbx
0x366a65  je    0x366ae1
```

Therefore, at `0x366a65`, `rbx` is the signed `(end - begin) / 16` value
computed from the vector header whose pointer is loaded from `r15+0x18`.

## Runtime Result

Breakpoint target:

- `libcp+0x366a65`, immediately after `sarq $0x4,%rbx`.

The corrected probe recorded exactly 16 capped packets per focal tier and then
disabled the breakpoint. Every render completed with process exit status `0`.

| Zoom | Process exit | JSON events | Breakpoint hits | Probe errors | Breakpoint disabled after cap | `(end-begin)` bytes | Computed count | Live `rbx` |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| `28mm` | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| `35mm` | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| `70mm` | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| `150mm` | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |

Invariant checks over all 64 recorded packets:

- `vector_begin_from_header == rax_begin_register`
- `vector_end_from_header == rcx_end_register`
- `computed_count_0x10 == rbx_after_sar_signed`
- `computed_count_0x10 == 5`
- `vector_diff == 80`

## Accepted Conclusions

- The static vector-count window at `0x366a50..0x366a65` is live under the
  canonical four-zoom bridge HDR quartet.
- In the sampled packets, the vector header reached through `r15+0x18` has
  byte span `80`, which corresponds to five 16-byte elements.
- At `0x366a65`, the live `rbx` register equals that computed count in every
  recorded packet.

## Non-Claims

- This does not prove that all later uses of the five elements are accepted as
  image contributors.
- This does not prove public semantic names for the vector elements.
- This does not prove the complete `0x3661b0` reducer algorithm.
- This does not prove Lumen-quality merge parity or final anti-ghosting policy.
