# LLDB Evidence: `CalibDataProcessor::State()` Operator Runtime Census

## Scope

This proof follows the already-identified upstream
`CalibDataProcessor::State ()` function-object family documented in
[bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md).

That earlier installed-bundle proof identified thirteen `std::__function`
`operator()` bodies tied to `runReferenceGroupCams` and `runHigherGroupCams`.
This runtime proof asks which of those thirteen bodies are live during complete
accepted bridge HDR renders for the canonical four-zoom quartet.

This is an entry-liveness and caller-context census. It does not classify each
operator body beyond the existing static proofs, and it does not close
`CLM-PREFUSION-002`.

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

Every one of the thirteen verified `CalibDataProcessor::State ()` `operator()`
bodies is live in every canonical focal run.

| Operator body | Family | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---|---:|---:|---:|---:|
| `0x229ec0` | `runReferenceGroupCams::$_0` | `1` | `1` | `1` | `1` |
| `0x22a0e0` | `runReferenceGroupCams::$_1` | `4` | `4` | `4` | `4` |
| `0x22a9b0` | `runReferenceGroupCams::$_2` | `4` | `4` | `4` | `4` |
| `0x22aaf0` | `runReferenceGroupCams::$_3` | `4` | `4` | `4` | `4` |
| `0x22ae60` | `runReferenceGroupCams::$_4` | `1` | `1` | `1` | `1` |
| `0x22af80` | `runReferenceGroupCams::$_5` | `1` | `1` | `1` | `1` |
| `0x22bdf0` | `runReferenceGroupCams::$_6` | `1` | `1` | `1` | `1` |
| `0x22bee0` | `runHigherGroupCams::$_7` | `5` | `5` | `5` | `5` |
| `0x22c350` | `runHigherGroupCams::$_8` | `5` | `5` | `5` | `5` |
| `0x22cd00` | `runHigherGroupCams::$_9` | `5` | `5` | `5` | `5` |
| `0x22d250` | `runHigherGroupCams::$_10` | `5` | `5` | `5` | `5` |
| `0x22e1d0` | `runHigherGroupCams::$_11` | `1` | `1` | `1` | `1` |
| `0x247390` | `runHigherGroupCams::$_12` | `258` | `283` | `337` | `207` |

## Runtime Object Identity

Every sampled entry decoded the incoming `rdi` object prefix successfully. The
first qword in each sampled object points back into the expected vtable family.

| Operator body | Captured object first qword module VA |
|---|---:|
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
| `0x247390` | `0x6589e0` |

The final `0x247390` object uses the same already-bounded
`runHigherGroupCams::$_12` family as
[bundle_proof_prefusion_callback_reuses_known_runner.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_callback_reuses_known_runner.md).

## Caller Context

The sampled top four stack VAs are stable across the four canonical runs:

| Operator group | Sampled top stack VAs |
|---|---|
| `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80` | `operator -> 0x22f3ff -> 0x227063 -> 0x3fc99d` |
| `0x22bdf0`, `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, `0x22e1d0` | `operator -> 0x22f3ff -> 0x2277b8 -> 0x3fe50a` |
| `0x247390` | `0x247390 -> 0x5f5e -> 0x4f83 -> 0x280e` |

This proves the sampled entry ancestry shape under these runs. It does not by
itself assign public names to the caller fields or prove final reducer policy.

## Proven Boundary

- The entire thirteen-body `CalibDataProcessor::State ()` `operator()` family is
  runtime-live across `28mm`, `35mm`, `70mm`, and `150mm` complete accepted
  bridge HDR renders.
- The twelve non-`0x247390` bodies have low, stable counts across the quartet.
- `0x247390` is the hot member of this family under the canonical quartet,
  with counts `258`, `283`, `337`, and `207`.
- Every sampled entry's incoming object prefix points back into the expected
  vtable family.

## Non-Claims

- This does not prove that any `CalibDataProcessor::State ()` body is the exact
  `src1` / `src2` merge/reduction closure.
- This does not decode return values from the operators.
- This does not assign public semantics to the returned `State` values or object
  fields.
- This does not replace the existing static body classifications; it adds
  runtime liveness and counts.
- This does not close C6 routing or final merge acceptance/rejection.
- This does not close `CLM-PREFUSION-002`.

## Next Proof

Use this result to stop treating any of the thirteen operators as merely
static-only. The hot `0x247390` path is the most runtime-dense member of the
family, but existing static proof bounds it as thresholded coordinate/bitset
state. The next useful Lane A proof should follow what the live returned states
feed, or instrument the downstream consumers after the `0x22f3ff` dispatcher
and `0x247390` runner path, looking for real multi-input merge/reduction or
distributed selection/acceptance math rather than re-proving entry liveness.
