# LLDB Evidence: State-Machine Return Ordering Across Four Zooms

## Scope

This proof follows the corrected `CalibDataProcessor::State()` family admitted in:

- [bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md)
- [lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md)
- [bundle_proof_state_machine_terminal_22e1d0_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_state_machine_terminal_22e1d0_static.md)

The earlier runtime attempt mentioned in the terminal-State static proof did not
produce accepted JSON and is non-evidence. This follow-up is the accepted runtime
capture of the dispatcher return path.

This proof captures:

- `0x22f3f6`, immediately before the dispatcher indirect call through the State
  function-object vtable slot `+0x30`.
- `0x22f3ff`, immediately after the call and before the returned `eax` is stored
  into the current State slot.

This is runtime return-ordering proof for the tested dispatcher path. It does
not assign public meanings to State numbers and does not close
`CLM-PREFUSION-002`.

## Artifacts

- Runtime probe:
  [state_machine_return_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/state_machine_return_probe.py)
- Runtime LLDB scripts:
  [state_machine_return_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/state_machine_return_28mm.lldb),
  [state_machine_return_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/state_machine_return_35mm.lldb),
  [state_machine_return_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/state_machine_return_70mm.lldb),
  [state_machine_return_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/state_machine_return_150mm.lldb)
- Run harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_machine_return_runtime/run_four_zoom.sh)
- Raw runtime outputs:
  `runs/state_machine_return_runtime/state_machine_return_28mm.{log,json,hdr}`,
  `runs/state_machine_return_runtime/state_machine_return_35mm.{log,json,hdr}`,
  `runs/state_machine_return_runtime/state_machine_return_70mm.{log,json,hdr}`,
  `runs/state_machine_return_runtime/state_machine_return_150mm.{log,json,hdr}`

The `.lldb` scripts launch with `--no-auto-lris`.

## Invocation

```bash
bash tools/lldb_probes/state_machine_return_runtime/run_four_zoom.sh
```

The harness invokes `arch -x86_64 lldb` against
`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`.

## Runtime Result

All four canonical bridge HDR runs completed, wrote `10432x7824` HDR output,
and exited with process status `0`.

| Zoom | LRI | JSON exit | Pre-call hits `0x22f3f6` | Post-call hits `0x22f3ff` | JSON errors | Step cap |
|---|---|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `38` | `38` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `38` | `38` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `38` | `38` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `38` | `38` | `0` | `false` |

The breakpoint hit-count fields and the probe's internal count fields both
report `38` hits at each site for each run. No run hit the configured cap of
`2048`.

## Ordered Return Sequence

The ordered post-call sequence below is identical across
`state_machine_return_28mm.json`, `state_machine_return_35mm.json`,
`state_machine_return_70mm.json`, and `state_machine_return_150mm.json`.

`pre_state` is the signed 32-bit value read from the current State slot at the
paired pre-call stop. `return` is signed 32-bit `eax` at `0x22f3ff`, before the
dispatcher store.

| # | Operator body | Family | `pre_state` | `return` |
|---:|---|---|---:|---:|
| 1 | `0x229df0` | `runReferenceGroupCams::$_0` | `0` | `2` |
| 2 | `0x229ec0` | `runReferenceGroupCams::$_1` | `2` | `3` |
| 3 | `0x22a0e0` | `runReferenceGroupCams::$_2` | `3` | `3` |
| 4 | `0x22a0e0` | `runReferenceGroupCams::$_2` | `3` | `3` |
| 5 | `0x22a0e0` | `runReferenceGroupCams::$_2` | `3` | `3` |
| 6 | `0x22a0e0` | `runReferenceGroupCams::$_2` | `3` | `6` |
| 7 | `0x22a9b0` | `runReferenceGroupCams::$_3` | `6` | `6` |
| 8 | `0x22a9b0` | `runReferenceGroupCams::$_3` | `6` | `6` |
| 9 | `0x22a9b0` | `runReferenceGroupCams::$_3` | `6` | `6` |
| 10 | `0x22a9b0` | `runReferenceGroupCams::$_3` | `6` | `4` |
| 11 | `0x22aaf0` | `runReferenceGroupCams::$_4` | `4` | `4` |
| 12 | `0x22aaf0` | `runReferenceGroupCams::$_4` | `4` | `4` |
| 13 | `0x22aaf0` | `runReferenceGroupCams::$_4` | `4` | `4` |
| 14 | `0x22aaf0` | `runReferenceGroupCams::$_4` | `4` | `7` |
| 15 | `0x22ae60` | `runReferenceGroupCams::$_5` | `7` | `8` |
| 16 | `0x22af80` | `runReferenceGroupCams::$_6` | `8` | `9` |
| 17 | `0x22bdf0` | `runHigherGroupCams::$_7` | `0` | `1` |
| 18 | `0x22bee0` | `runHigherGroupCams::$_8` | `1` | `1` |
| 19 | `0x22bee0` | `runHigherGroupCams::$_8` | `1` | `1` |
| 20 | `0x22bee0` | `runHigherGroupCams::$_8` | `1` | `1` |
| 21 | `0x22bee0` | `runHigherGroupCams::$_8` | `1` | `1` |
| 22 | `0x22bee0` | `runHigherGroupCams::$_8` | `1` | `3` |
| 23 | `0x22c350` | `runHigherGroupCams::$_9` | `3` | `3` |
| 24 | `0x22c350` | `runHigherGroupCams::$_9` | `3` | `3` |
| 25 | `0x22c350` | `runHigherGroupCams::$_9` | `3` | `3` |
| 26 | `0x22c350` | `runHigherGroupCams::$_9` | `3` | `3` |
| 27 | `0x22c350` | `runHigherGroupCams::$_9` | `3` | `6` |
| 28 | `0x22cd00` | `runHigherGroupCams::$_10` | `6` | `6` |
| 29 | `0x22cd00` | `runHigherGroupCams::$_10` | `6` | `6` |
| 30 | `0x22cd00` | `runHigherGroupCams::$_10` | `6` | `6` |
| 31 | `0x22cd00` | `runHigherGroupCams::$_10` | `6` | `6` |
| 32 | `0x22cd00` | `runHigherGroupCams::$_10` | `6` | `5` |
| 33 | `0x22d250` | `runHigherGroupCams::$_11` | `5` | `5` |
| 34 | `0x22d250` | `runHigherGroupCams::$_11` | `5` | `5` |
| 35 | `0x22d250` | `runHigherGroupCams::$_11` | `5` | `5` |
| 36 | `0x22d250` | `runHigherGroupCams::$_11` | `5` | `5` |
| 37 | `0x22d250` | `runHigherGroupCams::$_11` | `5` | `8` |
| 38 | `0x22e1d0` | `runHigherGroupCams::$_12` | `8` | `9` |

## Transition Count Summary

| Operator body | Returned State values observed |
|---|---|
| `0x229df0` | `2` once |
| `0x229ec0` | `3` once |
| `0x22a0e0` | `3` three times, `6` once |
| `0x22a9b0` | `6` three times, `4` once |
| `0x22aaf0` | `4` three times, `7` once |
| `0x22ae60` | `8` once |
| `0x22af80` | `9` once |
| `0x22bdf0` | `1` once |
| `0x22bee0` | `1` four times, `3` once |
| `0x22c350` | `3` four times, `6` once |
| `0x22cd00` | `6` four times, `5` once |
| `0x22d250` | `5` four times, `8` once |
| `0x22e1d0` | `9` once |

## Proven Boundary

- The accepted no-auto-LRIS canonical four-zoom bridge HDR runs all execute the
  same ordered State-return skeleton through dispatcher sites `0x22f3f6` and
  `0x22f3ff`.
- Each run records `38` paired pre/post dispatcher calls and exits cleanly.
- The higher-group sequence begins from a current State slot value of `0` at the
  paired pre-call capture for `0x22bdf0`; this is an observed slot value, not a
  public semantic label.
- The previously static proof that `0x22f0f0` stores returned `eax` into the
  current State slot is now runtime-paired with concrete returned values across
  the canonical quartet.

## Non-Claims

- This does not assign public meanings to State values `0`, `1`, `2`, `3`, `4`,
  `5`, `6`, `7`, `8`, or `9`.
- This does not prove that any State value is an acceptance, rejection, terminal,
  merge, source-contribution, or camera-participation semantic.
- This does not prove that the State-machine skeleton is identical outside the
  tested bridge HDR / no-auto-LRIS canonical quartet.
- This does not identify semantic `src1` or `src2` contents.
- This does not prove a reducer closure, final image effect, or final
  acceptance/rejection policy.

## Consequence For Blocker Work

The State-return ordering is no longer an unknown for the canonical four-zoom
dispatcher path. The remaining blocker is not "which State body returns what"
under this path; it is the public meaning, inputs, outputs, and image/merge
effect of the already-bounded State, candidate, coordinate, and wrapper
surfaces.
