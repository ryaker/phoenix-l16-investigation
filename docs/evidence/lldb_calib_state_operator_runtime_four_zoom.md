# LLDB Evidence: Corrected `CalibDataProcessor::State()` Operator Runtime Census

## Scope

This proof follows the `CalibDataProcessor::State ()` function-object family
documented in
[bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md).

It corrects a prior off-by-one / adjacent-vtable error:

- `0x229df0` is the first `runReferenceGroupCams::$_0` `State()` operator body.
- `0x22e1d0` is the terminal `runHigherGroupCams::$_12` `State()` operator body.
- `0x247390` is not a `CalibDataProcessor::State()` operator body. Its vtable
  typeinfo belongs to a separate `SparseLNR::markInliers(..., void(int,int,int))`
  function-object table.

This is an entry-liveness and caller-context census. It does not decode returned
`State` meanings and does not close `CLM-PREFUSION-002`.

## Artifacts

- Runtime probe:
  [state_operator_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/calib_state_operator_runtime/state_operator_probe.py)
- Runtime LLDB scripts:
  [state_operator_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/calib_state_operator_runtime/state_operator_28mm.lldb),
  [state_operator_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/calib_state_operator_runtime/state_operator_35mm.lldb),
  [state_operator_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/calib_state_operator_runtime/state_operator_70mm.lldb),
  [state_operator_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/calib_state_operator_runtime/state_operator_150mm.lldb)
- Raw runtime outputs:
  `runs/calib_state_operator_runtime/state_operator_28mm.{log,json,hdr}`,
  `runs/calib_state_operator_runtime/state_operator_35mm.{log,json,hdr}`,
  `runs/calib_state_operator_runtime/state_operator_70mm.{log,json,hdr}`,
  `runs/calib_state_operator_runtime/state_operator_150mm.{log,json,hdr}`

## Runtime Result

All four accepted bridge HDR runs exited with process status `0`, none hit the
drive step cap, all JSON `errors` arrays were empty, and no operator breakpoint
hit the configured cap of `512`. Therefore the counts below are full-render
breakpoint hit counts under these tested runs, not capped lower bounds.

Every one of the thirteen corrected `CalibDataProcessor::State ()` `operator()`
bodies is live in every canonical focal run.

| Operator body | Family | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---|---:|---:|---:|---:|
| `0x229df0` | `runReferenceGroupCams::$_0` | `1` | `1` | `1` | `1` |
| `0x229ec0` | `runReferenceGroupCams::$_1` | `1` | `1` | `1` | `1` |
| `0x22a0e0` | `runReferenceGroupCams::$_2` | `4` | `4` | `4` | `4` |
| `0x22a9b0` | `runReferenceGroupCams::$_3` | `4` | `4` | `4` | `4` |
| `0x22aaf0` | `runReferenceGroupCams::$_4` | `4` | `4` | `4` | `4` |
| `0x22ae60` | `runReferenceGroupCams::$_5` | `1` | `1` | `1` | `1` |
| `0x22af80` | `runReferenceGroupCams::$_6` | `1` | `1` | `1` | `1` |
| `0x22bdf0` | `runHigherGroupCams::$_7` | `1` | `1` | `1` | `1` |
| `0x22bee0` | `runHigherGroupCams::$_8` | `5` | `5` | `5` | `5` |
| `0x22c350` | `runHigherGroupCams::$_9` | `5` | `5` | `5` | `5` |
| `0x22cd00` | `runHigherGroupCams::$_10` | `5` | `5` | `5` | `5` |
| `0x22d250` | `runHigherGroupCams::$_11` | `5` | `5` | `5` | `5` |
| `0x22e1d0` | `runHigherGroupCams::$_12` | `1` | `1` | `1` | `1` |

`0x247390` is intentionally absent from the corrected probe and JSON `counts`
objects.

## Runtime Object Identity

Every sampled entry decoded the incoming `rdi` object prefix successfully. The
first qword in each sampled object points back into the corrected State vtable
family.

| Operator body | Captured object first qword module VA |
|---|---:|
| `0x229df0` | `0x658350` |
| `0x229ec0` | `0x6583d8` |
| `0x22a0e0` | `0x658458` |
| `0x22a9b0` | `0x6584d8` |
| `0x22aaf0` | `0x658558` |
| `0x22ae60` | `0x6585d8` |
| `0x22af80` | `0x658658` |
| `0x22bdf0` | `0x6586d8` |
| `0x22bee0` | `0x658758` |
| `0x22c350` | `0x6587d8` |
| `0x22cd00` | `0x658858` |
| `0x22d250` | `0x6588d8` |
| `0x22e1d0` | `0x658958` |

## Caller Context

The sampled top four stack VAs are stable across the four canonical runs:

| Operator group | Sampled top stack VAs |
|---|---|
| `0x229df0`, `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80` | `operator -> 0x22f3ff -> 0x227063 -> 0x3fc99d` |
| `0x22bdf0`, `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, `0x22e1d0` | `operator -> 0x22f3ff -> 0x2277b8 -> 0x3fe50a` |

This proves the sampled entry ancestry shape under these runs. It does not by
itself assign public names to the caller fields or prove final reducer policy.

## Proven Boundary

- The corrected thirteen-body `CalibDataProcessor::State ()` `operator()` family
  is runtime-live across `28mm`, `35mm`, `70mm`, and `150mm` complete accepted
  bridge HDR renders.
- The full-render count pattern is identical across the canonical quartet:
  `(1,1,4,4,4,1,1,1,5,5,5,5,1)`.
- Every sampled entry's incoming object prefix points back into the corrected
  State vtable family.
- `0x247390` is excluded from the `State()` census because its vtable typeinfo
  is the separate `SparseLNR::markInliers(..., void(int,int,int))` function
  family.

## Non-Claims

- This does not prove that any `CalibDataProcessor::State ()` body is the exact
  `src1` / `src2` merge/reduction closure.
- This census proof does not decode return values from the operators. Follow-up
  runtime return ordering is covered by
  [lldb_state_machine_return_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_machine_return_runtime_four_zoom.md).
- This does not assign public semantics to the returned `State` values or object
  fields.
- This does not prove that `0x247390` is dead or irrelevant; it only removes it
  from the `CalibDataProcessor::State()` family.
- This does not close C6 routing or final merge acceptance/rejection.
- This does not close `CLM-PREFUSION-002`.

## Next Proof

Use this result to stop treating the State-family address list as unknown, but
do not treat the family as reducer closure. The terminal corrected State body
and dispatcher are bounded by
[bundle_proof_state_machine_terminal_22e1d0_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_state_machine_terminal_22e1d0_static.md),
and the dispatcher return ordering is bounded by
[lldb_state_machine_return_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_machine_return_runtime_four_zoom.md).
The remaining Lane A work is public State semantics and image/merge effect, not
further probing of adjacent `0x247390` SparseLNR as if it were a `State()`
return path.
