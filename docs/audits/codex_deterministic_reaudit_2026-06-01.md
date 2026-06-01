# Codex Deterministic Re-Audit — 2026-06-01

## Scope

This audit independently checked the post-C6 commit range `3559b65..aa9904c` without promoting any
hypothesis to fact. It reran the nine local Python verifier scripts under `runs/`, re-read the corrected
static VAs from the real `libcp.dylib`, swept for hypothesis contamination, and reviewed the ten commit
diffs in that range against the current committed docs.

Target binary:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

LRI corpus root:
`/Volumes/Base Photos/Light`

## Verifier Results

| Verifier | Result | Reproduced facts |
|---|---|---|
| `runs/prefusion_reducer_static/hann_window_closedform_check.py` | PASS | Periodic Hann residual `1.133e-07`; classic symmetric Hann residual `5.696e-02`; tap sum `7.999999940395355`. |
| `runs/prefusion_reducer_static/lut_first_tap_byte_check.py` | FAIL / stale local script | Script decodes hardcoded bytes `40 77 1d 3c` as `0.009610950946807861`, not expected `0.009607374668`. Independent `xxd` proves real bytes at `0x5fdb50` start `40 68 1d 3c`; do not use this script as evidence until fixed. |
| `runs/prefusion_reducer_static/verify_lut_in_binary.py` | PASS | Binary size `6935696`; exactly one 64-byte LUT match at file offset `0x5fdb50`; `decoded[0]=0.009607374668`, `decoded[7]=0.990392684937`, roundtrip exact. |
| `runs/lri_calibration_origin/verify_libcp_const.py` | PASS | `1.0` count `5627`; `0.5` count `258`; `1/3` count `14`; `1/288` count `0`. |
| `runs/lri_calibration_origin/verify_laneB_independent.py` | PASS | Canonical four LRIs have identical calibration hashes: intrinsics `722a6e721636c9c4`, distortion `f0c34433f9cf9b07`, depthcfg `6a0d52b6a4d1b4de`; 16 intrinsics records are pairwise distinct; proto field values present are `[780, 3120, 4160]`, while `2080, 1560, 10432, 7824, 8896, 6672, 4096, 1040, 520, 390` are absent. |
| `runs/two_unit_corpus/per_file_unit_partition.py` | PASS after approved `/Volumes/Dev` write | `DONE n=9390 units=2 mixed_folders=13 none=182`; signatures `223961c6bce6153e: 3484`, `722a6e721636c9c4: 5724`; report written to `/Volumes/Dev/lumen-phoenix-scratch/per_file_unit_partition_report.txt`. |
| `runs/two_unit_corpus/unit_sequence_monotonicity.py` | PASS | Unit `223961c6bce6153e`: `3484` files, monotonic fraction `0.9983` (`3477` inc, `6` dec). Unit `722a6e721636c9c4`: `5724` files, monotonic fraction `0.9991` (`5718` inc, `5` dec). Mixed-date ranges show independent counters. |
| `runs/two_unit_corpus/crossunit_v2.py` | PASS after approved `/Volumes/Dev` write | All eight U1/U2 focal twin seeds pass: 16/16 distinct intrinsics records, ROI `True`, U1 intrinsics size `32832`, U2 size `32833`, expected signatures. Report written to `/Volumes/Dev/lumen-phoenix-scratch/crossunit_v2_report.txt`. |
| `runs/two_unit_corpus/twin_compare.py` | PASS | Same-name U1/U2 twins for 28/35/70/150 all have different unit signatures; every pair reports `SAME=False`. |

Custody finding: `runs/` is gitignored and `git ls-files runs/...` returns no tracked verifier scripts.
The scripts are locally present and reproduced the facts above, but they are not committed repro
harnesses. The committed evidence docs embed the facts; moving these verifier scripts into a tracked
tool/audit harness path is still needed for stronger custody.

## Static VA Re-Disassembly

The corrected VAs were independently re-read with static LLDB against the real dylib.

- `0x2f8584..0x2f85a5` inside function `0x2f78e0` is the corrected reciprocal-normalize block. The
  slice shows `0x2f8580 maxps`, `0x2f8584 mulps`, `0x2f8587 addps`, `0x2f858a addps`, loop back to
  `0x2f8430`, then `0x2f859f rcpps`, `0x2f85a2 mulps`, `0x2f85a5 movaps`. This confirms the address
  correction only; runtime role on `src1`/`src2` remains unproven.
- `0x369f80..0x369fca` inside function `0x3661b0` shows the separable accumulator loop:
  `movss -0xa0(...)`, `mulss`, `shufps`, `mulps (%rdi)`, `addps (%rdx,%rcx,4)`, `movaps`, inner bound
  `0x40`, outer bound `0x10`.
- `0x3eced0` anchor shows `movss 0x10(%rdi), %xmm0`, `xorps %xmm1,%xmm1`, and repeated
  `mulps -> maxps -> sqrtps` at `0x3ecfe4..0x3ecfea`.
- Independent `xxd -s 0x5fdb50 -l 64` confirms the LUT begins `4068 1d3c`, not the stale
  `4077 1d3c` hardcoded by `lut_first_tap_byte_check.py`.

## Contamination Sweep

Commands searched `docs/TRUTH.md`, `docs/canonical/`, and `docs/evidence/` for explicit `HYP-*`
references and for key phrases from the two hypothesis docs.

Result: no silent hypothesis promotion found.

- Explicit hypothesis references are confined to evidence docs that label them as leads / not fact.
- `CalibStage`, `source_b_product * inverse(source_a_product)`, and `1/288` appear in canonical/evidence
  only as already bounded static/runtime facts or as explicitly open public-semantics work.
- No doc outside `docs/hypotheses/` was found claiming the unresolved per-camera K decode for cams
  `1..15`, the LRI source of the row-composition matrix, or public `CalibStage` bank mapping as fact.

## Commit Diff Review

| Commit | Audit verdict |
|---|---|
| `9319c5c` | Substantially reproduced: Hann closed form and binary LUT offset are confirmed. Exception: extra local `lut_first_tap_byte_check.py` is stale and fails; verifier scripts are local ignored `runs/`, not committed. Scope language keeps reducer unresolved. |
| `17ecb2c` | Policy-only four-zoom hypothesis rule. No unsupported technical fact found. |
| `8a4d3fb` | Reproduced by `verify_laneB_independent.py`; facts are scoped to the canonical four LRIs and static LRI parsing. |
| `7485dce` | Reproduced by `verify_libcp_const.py`; `1/3` and `1/288` counts match. |
| `e34e6d6` | Static address corrections confirmed by LLDB. The 28mm runtime decider remains a scope-bound hypothesis progress note; this audit did not rerun that runtime probe. |
| `08431ca` | Per-file two-unit partition reproduced after approved `/Volumes/Dev` report write; counts match. |
| `2854171` | Filename-sequence corroboration reproduced; counts and monotonic fractions match. |
| `4368090` | Scope cleanup only; removal of owner identity is consistent with bytes-only discipline. |
| `572985d` | Cross-unit LRI-format check reproduced after approved `/Volumes/Dev` report write; all eight seeds pass. |
| `aa9904c` | Hypothesis address-correction sync is mostly correct; one proof-plan line still pointed at refuted `0x2f8040` and was corrected by this audit. |

## Bottom Line

Most claimed facts in `3559b65..aa9904c` reproduce independently. Two custody/staleness issues were found
and are now contained:

- `lut_first_tap_byte_check.py` is stale and fails; the binary truth is still confirmed by
  `verify_lut_in_binary.py` and `xxd`.
- The local `runs/` verifier scripts are not git-tracked. The committed docs embed the verified facts,
  but durable reproducibility should promote these verifier scripts into a tracked harness location.

No parity blocker is closed by this audit. `CLM-PREFUSION-002` remains blocked on runtime/data-flow proof
of the actual `src1`/`src2` pre-fusion mechanism across `28mm`, `35mm`, `70mm`, and `150mm`.
