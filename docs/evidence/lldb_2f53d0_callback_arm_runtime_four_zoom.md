# LLDB Evidence: `0x2f6420` Callback Arm Runtime Under `0x2f53d0`

## Scope

This proof follows the already-bounded visible-`src1` chain:

`0x3e4b09 -> 0x3449f0 -> 0x345920 -> 0x2f53d0 -> 0x2f6420 -> 0x5440`

It asks one narrow question: after the first visible-`src1` secondary-callable
gate (`0x3e4b09`), which `0x2f6420` bilateral-kernel callback arm is selected
at runtime across the canonical four-zoom bridge HDR quartet?

This is a route-selection proof only. It does not identify semantic `src1`
contents and does not close `CLM-PREFUSION-002`.

## Artifacts

- Runtime probe:
  [callback_arm_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_callback_arm_runtime/callback_arm_probe.py)
- Runtime LLDB scripts:
  [callback_arm_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_callback_arm_runtime/callback_arm_28mm.lldb),
  [callback_arm_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_callback_arm_runtime/callback_arm_35mm.lldb),
  [callback_arm_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_callback_arm_runtime/callback_arm_70mm.lldb),
  [callback_arm_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_callback_arm_runtime/callback_arm_150mm.lldb)
- Raw runtime outputs:
  `runs/2f53d0_callback_arm_runtime/callback_arm_28mm.{log,json,hdr}`,
  `runs/2f53d0_callback_arm_runtime/callback_arm_35mm.{log,json,hdr}`,
  `runs/2f53d0_callback_arm_runtime/callback_arm_70mm.{log,json,hdr}`,
  `runs/2f53d0_callback_arm_runtime/callback_arm_150mm.{log,json,hdr}`

## Runtime Result

All four accepted bridge HDR runs exited with process status `0`, each observed
the first visible-`src1` gate once, none hit the drive step cap, and all JSON
`errors` arrays were empty.

The probe installed breakpoints for the eight static `0x2f6420 -> 0x5440`
callback-arm callsites after the first `0x3e4b09` gate. It also installed
breakpoints at the hypothesis-relevant `0x2f78e0` worker entry and at its
normalizer block sites `0x2f8584`, `0x2f859f`, and `0x2f85a5`.

| LRI / focal | Nonzero `0x2f6420 -> 0x5440` arm | Other arm callsites | `0x2f78e0` / normalizer sites |
|---|---:|---:|---:|
| `28mm` / `L16_02130` | `0x2f67e2 -> 0x5440` (`0x2fb320` arm) hit cap `256` | `0` | `0` |
| `35mm` / `L16_03041` | `0x2f67e2 -> 0x5440` (`0x2fb320` arm) hit cap `256` | `0` | `0` |
| `70mm` / `L16_03434` | `0x2f67e2 -> 0x5440` (`0x2fb320` arm) hit cap `256` | `0` | `0` |
| `150mm` / `L16_02285` | `0x2f67e2 -> 0x5440` (`0x2fb320` arm) hit cap `256` | `0` | `0` |

Because the `0x2fb320` arm hit the probe cap, `256` is a lower bound, not a
full-render total. The zero-hit arm and normalizer breakpoints remained enabled
after the gate and recorded zero hits through clean render exit under these
tested conditions.

## Callback Identity Check

Sampled `0x2f67e2` packets read the runtime callback object from the stack slot
selected by the static callsite and resolved it back to module VAs:

- callback vtable address point: `0x65a768`
- callback slot `+0x30`: `0x2fb320`
- vtable/worker expected-match checks: `true`
- parent return sites observed in samples: `0x2f59a6` and `0x2f5ad1`, matching
  the loop/final `0x2f6420` callers inside `0x2f53d0`

The sampled parent chains also pass through the previously bounded
`0x3449f0 -> 0x345920 -> 0x2f53d0` visible-`src1` route.

## Proven Boundary

- Under the first visible-`src1` `0x3e4b09` gate, complete accepted runs at
  `28mm`, `35mm`, `70mm`, and `150mm` select the `0x2fb320` callback arm at
  `0x2f6420 -> 0x5440`.
- Under that same tested scope, the `0x2f78e0` arm has zero callsite hits, and
  the `0x2f78e0` worker entry plus normalize block sites `0x2f8584`,
  `0x2f859f`, and `0x2f85a5` have zero hits.

## Non-Claims

- This does not prove that `0x2fb320` is the `src1` / `src2` merge reducer.
- This does not globally refute `0x2f78e0`; it excludes only this tested
  visible-`src1` post-gate `0x2f53d0 -> 0x2f6420` route as a positive
  runtime route to `0x2f78e0`.
- This does not cover possible `0x2f78e0` uses before the first visible-`src1`
  gate or from unrelated callers.
- This does not assign public names to `0x2f6420` fields, descriptor roles, or
  callback families.
- This does not close `CLM-PREFUSION-002`, C6 routing, or final merge
  acceptance/rejection.

## Next Proof

The next useful Lane A step is to inspect and/or instrument the now-live
`0x2fb320` worker family enough to decide whether it is still local
descriptor filtering, or whether it exposes multi-input merge/reduction inputs
that matter to `src1` / `src2` parity.
