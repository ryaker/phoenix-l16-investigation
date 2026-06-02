# Static Proof: Corrected State-Family Exact Body Call Surface

## Scope

This proof follows the corrected `CalibDataProcessor::State()` family and the
accepted return-order runtime proof:

- [bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md)
- [lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md)
- [lldb_state_machine_return_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_machine_return_runtime_four_zoom.md)

It statically isolates the exact installed-bundle function body for each of the
thirteen corrected State operators and records direct calls, direct-call absence,
and whether each body contains indirect calls.

This is an installed-bundle static call-surface proof. It does not prove helper
transitive behavior, public State semantics, image effect, or final
acceptance/rejection.

## Artifacts

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Raw LLDB extraction script:
  `runs/static_state_family_classification/state_family_static.lldb`
- Raw LLDB disassembly output:
  `runs/static_state_family_classification/state_family_static_disasm.txt`
- Parsed exact-body summary:
  `runs/static_state_family_classification/state_family_function_summary.json`
- Selected helper caller outputs:
  `runs/static_state_family_classification/callers_0x*.txt`

The parser isolates only the function block headed by
`libcp.dylib\`___lldb_unnamed_symbol_<va>` for each State-body VA. It does not
use the broader disassembly range as a body boundary, because those ranges can
include adjacent unnamed helper symbols.

## Extraction Command

```bash
arch -x86_64 lldb -b -s runs/static_state_family_classification/state_family_static.lldb \
  > runs/static_state_family_classification/state_family_static_disasm.txt
```

The `.lldb` script disassembles the thirteen corrected State bodies plus
dispatcher `0x22f0f0` from the installed `libcp.dylib`.

## Exact Body Direct-Call Surface

The table filters out high-address symbol-stub calls (`0x55....` / `0x56....`)
from the displayed callee list, but the `Direct calls` count includes every
direct `callq` parsed from the exact isolated body.

| Body | Instructions | Direct calls | Non-stub direct callees | Parsed immediate State constants | Indirect calls |
|---|---:|---:|---|---|---:|
| `0x229df0` | `6` | `0` | none | `2` | `0` |
| `0x229ec0` | `96` | `7` | `0x224cc0`, `0x226410`, `0x228db0`, `0x231350` | `1`, `3` | `0` |
| `0x22a0e0` | `498` | `48` | `0xdb240`, `0xe6ba0`, `0xe8e70`, `0xf2750`, `0x224e50`, `0x225fb0`, `0x226410`, `0x228db0`, `0x229300`, `0x23faf0`, `0x264440` | `3`, `6` | `0` |
| `0x22a9b0` | `34` | `2` | `0x21af90`, `0x21b2e0` | `6`, `4` | `0` |
| `0x22aaf0` | `188` | `16` | `0xdb240`, `0xe6ba0`, `0xf3360`, `0x216eb0`, `0x216f50`, `0x216f60`, `0x226410` | none parsed | `0` |
| `0x22ae60` | `21` | `4` | `0x20ada0`, `0x20bd60`, `0x239ac0` | `8` | `0` |
| `0x22af80` | `781` | `58` | `0xdb240`, `0xdf8c0`, `0xdf8d0`, `0xdf940`, `0xe6ba0`, `0xe75d0`, `0xf33d0`, `0xf3e10`, `0x22ee10`, `0x230870`, `0x2314d0`, `0x2315d0`, `0x239ac0`, `0x239e00`, `0x23a5c0`, `0x23c5f0`, `0x264440` | `9` | `0` |
| `0x22bdf0` | `6` | `0` | none | `1` | `0` |
| `0x22bee0` | `258` | `17` | `0xdb240`, `0xe6ba0`, `0xf3360`, `0x210c10`, `0x226410` | none parsed | `0` |
| `0x22c350` | `569` | `48` | `0xdb240`, `0xe6ba0`, `0xe8e70`, `0x224d70`, `0x225fb0`, `0x228db0`, `0x229300`, `0x229390`, `0x22e8d0`, `0x23faf0`, `0x264440` | `3`, `6` | `0` |
| `0x22cd00` | `247` | `14` | `0xdb240`, `0xe6ba0`, `0x21af90`, `0x21b2e0`, `0x232340`, `0x239ac0`, `0x23a530`, `0x264440` | `6`, `5`, `5` | `0` |
| `0x22d250` | `872` | `42` | `0xdb240`, `0xe6ba0`, `0xf3360`, `0xf33d0`, `0x216eb0`, `0x216f50`, `0x216f60`, `0x226410`, `0x232340`, `0x239ac0`, `0x23a530`, `0x264440` | none parsed | `0` |
| `0x22e1d0` | `391` | `20` | `0xdb240`, `0xdf8c0`, `0xe6ba0`, `0xf33d0`, `0x232340`, `0x239ac0`, `0x23a530`, `0x23a5c0`, `0x23c5f0` | `9` | `0` |
| `0x22f0f0` dispatcher | `272` | `24` | `0x7820`, `0x2102d0`, `0x210370`, `0x231640`, `0x231780`, `0x2321f0` | none parsed | `3` |

## Helper Caller Cross-Checks

Selected repo-local callgraph outputs provide direct-caller sanity checks for
several helper edges:

| Helper | Direct callers reported by callgraph |
|---|---|
| `0x20ada0` | `0x22ae6e` |
| `0x20bd60` | `0x22ae87` |
| `0x21af90` | `0x22a9d2`, `0x22cd3d` |
| `0x21b2e0` | `0x22a9e2`, `0x22cd4d` |
| `0x23c5f0` | eleven callsites in the `0x22b...` range plus `0x22e244`, `0x22e283` |
| `0xf33d0` | includes `0x22bb23`, `0x22df45`, and `0x22e755` among ten direct callers |

These caller outputs are direct-callgraph checks only. They do not classify the
helpers' public semantics.

## Direct Known-Merge-Surface Exclusion

The exact isolated State bodies and dispatcher have zero direct calls to the
following already-known merge/wrapper/owner-route VAs:

- `0x365960`
- `0x3661b0`
- `0x369fa1`
- `0x3ecc10`
- `0x3ecd80`
- `0x3eced0`
- `0x3ec960`
- `0x3e4a80`
- `0x3edb80`
- `0x36f800`

This is only a direct-call exclusion. It does not prove those surfaces are
unreachable transitively through helpers.

## Proven Boundary

- The thirteen corrected State operator bodies contain zero indirect calls in
  their exact installed-bundle bodies.
- The dispatcher `0x22f0f0` contains indirect calls, consistent with the already
  proven State function-object / callback dispatch role.
- The exact State bodies expose direct helper-family surfaces rather than direct
  calls to the listed known IRAMP, wrapper, owner-output, or selected-cache
  route bodies.
- The reference and higher groups reuse several helper families in paired ways:
  `0x21af90` / `0x21b2e0` appear in `0x22a9b0` and `0x22cd00`;
  `0x216f50` / `0x216f60` appear in `0x22aaf0` and `0x22d250`;
  `0x23faf0` appears in `0x22a0e0` and `0x22c350`;
  `0x23c5f0` appears in `0x22af80` and `0x22e1d0`.

## Non-Claims

- This does not prove helper transitive behavior.
- This does not prove public names or meanings for the State values.
- This does not prove that helper-family work has no image effect.
- This does not prove final source contribution, reducer closure, or final
  acceptance/rejection.
- This does not prove direct-call absence outside the exact installed-bundle
  bodies listed here.

## Consequence For Blocker Work

The State operator shells should not be treated as opaque possible direct
reducers. The remaining Lane A work is in the helper-family semantics and
downstream image/merge effect of the already-live candidate, coordinate,
record-state, and wrapper surfaces.
