# LLDB Evidence: State Helper `0x23c5f0` And `0xf33d0` Selector Path Across Four Zooms

## Scope

This proof follows the corrected `CalibDataProcessor::State()` family admitted
in:

- [bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md)
- [lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md)
- [lldb_state_machine_return_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_machine_return_runtime_four_zoom.md)
- [bundle_static_state_family_full_body_call_surface.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_state_family_full_body_call_surface.md)

It bounds two helper surfaces exposed by the exact State-body direct-call
surface:

- `0x23c5f0`, called by corrected State bodies `0x22af80` and `0x22e1d0`.
- `0xf33d0`, a selector-gated field-copy helper called by `0x23c5f0` and other
  State/helper surfaces.

This is helper-surface and selector-path proof. It does not assign public State
semantics, public `CalibStage` semantics, source contribution, image effect,
reducer closure, or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [state_helper_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_probe.py)
- Runtime LLDB scripts:
  [state_helper_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_28mm.lldb),
  [state_helper_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_35mm.lldb),
  [state_helper_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_70mm.lldb),
  [state_helper_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_150mm.lldb)
- Runtime harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/run_four_zoom.sh)
- Raw runtime outputs:
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_28mm.{log,json,hdr}`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_35mm.{log,json,hdr}`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_70mm.{log,json,hdr}`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_150mm.{log,json,hdr}`
- Raw static extraction script:
  `runs/static_state_helpers_23c5f0_f33d0/helpers_static.lldb`
- Raw static disassembly:
  `runs/static_state_helpers_23c5f0_f33d0/helpers_static_disasm.txt`
- Parsed static summary:
  `runs/static_state_helpers_23c5f0_f33d0/helpers_summary.json`

The `.lldb` scripts launch with `--no-auto-lris`.

## Invocation

```bash
bash tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/run_four_zoom.sh
```

The harness invokes `arch -x86_64 lldb` against
`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`.

## Static Boundary

Static extraction from the installed bundle shows:

- `0x23c5f0` has no indirect calls in the extracted body.
- `0x23c5f0` directly calls `0xf33d0` at `0x23d38d`; the return address is
  `0x23d392`.
- `0x23c5f0` also directly calls helper surfaces including `0xdb240`,
  `0xdf8d0`, `0xdf940`, `0xe0ae0`, `0xf6c60`, `0x23c0f0`, `0x23faf0`,
  `0x2406a0`, and `0x264440`.
- `0xf33d0` has no indirect calls in the extracted body.
- `0xf33d0` branches on `r8d`. Selector `0` copies two source vector/int
  records and a three-int packet into destination offsets
  `0x180..0x1d0`. Selector `1` copies the same shaped inputs into destination
  offsets `0x12c..0x17c`.
- Any `0xf33d0` selector other than `0` or `1` enters an error path containing
  string `"wrong CalibStage, must be factory or current"`.

The installed-bundle static extraction is a body/branch/call-surface bound. It
does not prove runtime liveness by itself.

## Runtime Result

All four canonical bridge HDR runs completed, wrote `10432x7824` HDR output,
and exited with process status `0`.

| Zoom | LRI | JSON exit | `0x23c5f0` hits | `0xf33d0` hits | JSON errors | Step cap |
|---|---|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `4` | `54` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `4` | `54` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `4` | `55` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `4` | `50` | `0` | `false` |

The breakpoint hit-count fields and the probe's internal count fields match in
every run. No run hit the configured cap of `4096`, and the configured sample
limit of `2048` is larger than every full run's total captured event count.

## `0x23c5f0` Runtime Callers

The `0x23c5f0` caller and argument pattern is identical across
`28mm`, `35mm`, `70mm`, and `150mm`.

| Caller return VA | Containing corrected State body | Hits per run | Captured `r8d` | Captured `r9d` |
|---|---|---:|---:|---:|
| `0x22b51e` | `0x22af80` | `2` | `0` | `9` |
| `0x22e249` | `0x22e1d0` | `1` | `1` | `11` |
| `0x22e288` | `0x22e1d0` | `1` | `1` | `11` |

This proves that `0x23c5f0` is live under both the reference-side terminal State
body `0x22af80` and the higher-side terminal State body `0x22e1d0` in the
accepted canonical quartet.

## `0xf33d0` Runtime Selectors

Every captured `0xf33d0` hit used selector `0` or selector `1`. No captured
runtime hit used the static error selector path.

| Caller return VA | Selector | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---:|---:|---:|---:|---:|
| `0x1f132d` | `0` | `10` | `10` | `10` | `10` |
| `0x1f1350` | `1` | `10` | `10` | `10` | `10` |
| `0x2115a1` | `1` | `4` | `4` | `4` | `4` |
| `0x217bc3` | `1` | `2` | `3` | `3` | `3` |
| `0x22bb28` | `1` | `1` | `0` | `2` | `0` |
| `0x22df4a` | `1` | `1` | `1` | `0` | `0` |
| `0x22e75a` | `1` | `0` | `0` | `0` | `1` |
| `0x23d392` | `1` | `26` | `26` | `26` | `22` |

The `0x23d392` caller return VA is inside the static `0x23c5f0` body, following
the static direct call at `0x23d38d -> 0xf33d0`. This proves the
`0x23c5f0 -> 0xf33d0` selector-`1` path is runtime-live across all four
canonical zoom tiers.

## Proven Boundary

- `0x23c5f0` is a live State-helper surface in complete accepted no-auto-LRIS
  bridge HDR renders at `28mm`, `35mm`, `70mm`, and `150mm`.
- The live `0x23c5f0` calls come from corrected State body `0x22af80` twice per
  run and corrected State body `0x22e1d0` twice per run under this tested path.
- `0xf33d0` is a selector-gated field-copy helper in the installed bundle.
- The accepted canonical quartet exercises only selector `0` and selector `1`
  at `0xf33d0`; the selector error path is not observed in these runs.
- The `0x23c5f0 -> 0xf33d0` callsite at static call `0x23d38d` / return
  `0x23d392` is runtime-live across the accepted canonical quartet and uses
  selector `1` in every captured hit.

## Non-Claims

- This does not assign public meaning to `CalibStage`, selector `0`, selector
  `1`, factory/current naming, State values, or State-body public semantics.
- This does not prove that `0x23c5f0`, `0xf33d0`, or their callers perform final
  source contribution, image acceptance, image rejection, or multi-camera
  reducer closure.
- This does not prove all transitive helper behavior beneath `0x23c5f0`.
- This does not prove behavior outside the accepted canonical no-auto-LRIS
  bridge HDR quartet.
- This does not close `CLM-PREFUSION-002`.

## Consequence For Blocker Work

The State-helper edge is narrower now: `0x23c5f0` and the live
`0x23c5f0 -> 0xf33d0` selector-`1` path should be treated as bounded
helper/field-copy surfaces, not opaque possible direct reducers. The remaining
Lane A work is still helper transitive semantics, downstream image effect,
semantic `src1` / `src2` contents, reducer closure, and final
acceptance/rejection.
