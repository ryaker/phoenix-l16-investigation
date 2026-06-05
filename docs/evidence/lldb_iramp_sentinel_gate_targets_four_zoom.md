# LLDB IRAMP Sentinel-Gate Target Evidence

**Date:** 2026-06-05
**Status:** Runtime evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local `lri_process`, and the
canonical four-zoom bridge HDR quartet with `--no-auto-lris`.

This document validates the branch-target behavior around the local IRAMP
index sentinel compare at `0x36930f`.

It proves:

- the sentinel skip target `0x36931b` is live with `eax == 0x80000000`
  on all four canonical focal tiers
- the valid target `0x369320` is live with non-sentinel `eax` values on all
  four canonical focal tiers
- at the valid target, the table value at `r12 + rsi * 8` matches the live
  `eax` value in every recorded packet

It does not prove the complete candidate predicate, final score filtering,
public field names, full per-pixel distribution, complete reducer closure, or
final acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harness:

- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_probe.py`
- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_28mm.lldb`
- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_35mm.lldb`
- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_70mm.lldb`
- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/sentinel_gate_150mm.lldb`
- `tools/lldb_probes/codex_iramp_sentinel_gate_validation/run_four_zoom.sh`

Generated raw reports and HDR outputs live under ignored local directory:

- `runs/codex_iramp_sentinel_gate_validation/`

No live `/tmp` or `/private/tmp` artifact is cited by this evidence.

The final accepted run followed two rejected harness attempts:

- first attempt used Python absolute-address breakpoints and recorded zero hits
  because the breakpoints did not bind to `libcp`
- second attempt used shared-library breakpoints but failed to map breakpoint
  IDs before launch, so the 28mm run could not disable the hot stops and was
  terminated as a harness failure

Those attempts are not evidence. The accepted run is the corrected
shared-library-breakpoint pass summarized below.

## Static Gate Window

Fresh installed-bundle disassembly confirms this local branch shape:

```asm
0x369306  movq  0x30(%rdi,%rdx), %r12
0x36930b  movl  (%r12,%rsi,8), %eax
0x36930f  cmpl  $0x80000000, %eax
0x369314  jne   0x369320
0x369316  movl  %ebx, %edx
0x369318  movl  %r15d, %esi
0x36931b  jmp   0x369f0b
0x369320  movq  %r9, -0x4320(%rbp)
```

Therefore:

- `0x369320` is the non-sentinel target reached after `jne`
- `0x36931b` is the sentinel skip target after the sentinel-path register moves

The probe records table-match fields at both sites, but the table-address
fields are accepted only at `0x369320`: on the sentinel path, `0x369318`
overwrites `esi` before `0x36931b`, so `rsi` no longer necessarily names the
linear table index used at `0x36930b`.

## Runtime Summary

Breakpoint targets:

- `libcp+0x36931b` sentinel skip target
- `libcp+0x369320` valid target

Each site was capped at 12 recorded packets per focal tier. Every render
completed with process exit status `0`.

| Zoom | Process exit | Probe errors | Sentinel-target packets | Sentinel packets with `eax == 0x80000000` | Valid-target packets | Valid packets where table low dword matched `eax` | Valid `eax` range | Partner-record count |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | 0 | 12 | 12 | 12 | 12 | `-1..150` | 1 |
| `35mm` | `0` | 0 | 12 | 12 | 12 | 12 | `8..644` | 1 |
| `70mm` | `0` | 0 | 12 | 12 | 12 | 12 | `5..194` | 1 |
| `150mm` | `0` | 0 | 12 | 12 | 12 | 12 | `-1..185` | 4 |

Notes:

- `eax == -1` is a valid non-`0x80000000` value at `0x369320` in the sampled
  `28mm` and `150mm` packets; this proof does not assign its public meaning.
- The `partner-record count` is derived from the live vector span at
  `rbp-0x1800..rbp-0x17f8` divided by `0x280`.
- The `150mm` accepted packet window had four partner records; the other
  accepted packet windows had one partner record. These are sampled runtime
  windows, not global constants.

## Accepted Conclusions

- The sentinel skip path at `0x36931b` is live on the canonical four-zoom
  bridge HDR quartet.
- The valid non-sentinel path at `0x369320` is live on the canonical four-zoom
  bridge HDR quartet.
- For valid-target packets, the low dword read from `r12 + rsi * 8` matches
  the live non-sentinel `eax` value in all 48 recorded packets.
- The runtime evidence supports the static branch interpretation: local
  `0x80000000` values skip toward the loop tail, while non-`0x80000000` values
  fall through into the processing path.

## Non-Claims

- This is not a complete distribution of sentinel vs valid table values.
- This does not prove that every valid-target packet eventually contributes to
  final output.
- This does not prove score-threshold policy downstream of the tuple store.
- This does not prove public semantic names for the index table, tuple fields,
  partner records, or channels.
- This does not close the complete `0x3661b0` reducer algorithm.
