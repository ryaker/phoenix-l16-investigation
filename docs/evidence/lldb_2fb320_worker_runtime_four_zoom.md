# LLDB Evidence: `0x2fb320` Worker Runtime Under `0x2f53d0`

## Scope

This proof follows the already-bounded visible-`src1` route:

`0x3e4b09 -> 0x3449f0 -> 0x345920 -> 0x2f53d0 -> 0x2f6420 -> 0x5440 -> 0x2fb320`

The preceding arm-selection proof shows that complete accepted bridge HDR runs
at `28mm`, `35mm`, `70mm`, and `150mm` select the `0x2fb320` callback arm under
this route. This follow-up asks what the live `0x2fb320` worker fields and final
store mechanics look like under the same first visible-`src1` gate.

This is a worker-mechanics proof only. It does not identify semantic `src1`
contents and does not close `CLM-PREFUSION-002`.

## Artifacts

- Runtime probe:
  [worker_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2fb320_worker_runtime/worker_probe.py)
- Runtime LLDB scripts:
  [worker_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2fb320_worker_runtime/worker_28mm.lldb),
  [worker_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2fb320_worker_runtime/worker_35mm.lldb),
  [worker_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2fb320_worker_runtime/worker_70mm.lldb),
  [worker_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2fb320_worker_runtime/worker_150mm.lldb)
- Raw runtime outputs:
  `runs/2fb320_worker_runtime/worker_28mm.{log,json,hdr}`,
  `runs/2fb320_worker_runtime/worker_35mm.{log,json,hdr}`,
  `runs/2fb320_worker_runtime/worker_70mm.{log,json,hdr}`,
  `runs/2fb320_worker_runtime/worker_150mm.{log,json,hdr}`
- Static reference:
  [lldb_2f53d0_callback_bodies_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_2f53d0_callback_bodies_static.md),
  with raw static output in
  `runs/2f53d0_downstream_helpers/static_2f53d0_callback_vtables.log`

## Runtime Result

All four accepted bridge HDR runs exited with process status `0`, each observed
the first visible-`src1` gate once, none hit the drive step cap, and all JSON
`errors` arrays were empty.

The probe installed `0x2fb320` entry and `0x2fbf05` post-store breakpoints only
after the first `0x3e4b09` gate. Each run hit the configured cap of `64` at both
breakpoints, so the counts below are lower bounds and sampled windows, not
full-render totals.

| LRI / focal | Gate hits | `0x2fb320` entries | `0x2fbf05` post-stores | Errors |
|---|---:|---:|---:|---:|
| `28mm` / `L16_02130` | `1` | `64` | `64` | `0` |
| `35mm` / `L16_03041` | `1` | `64` | `64` | `0` |
| `70mm` / `L16_03434` | `1` | `64` | `64` | `0` |
| `150mm` / `L16_02285` | `1` | `64` | `64` | `0` |

## Callback Identity

Every captured entry sample resolves the callback object to the same runtime
address-point and worker slot:

| LRI / focal | Vtable address point | Slot `+0x30` | Match |
|---|---:|---:|---:|
| `28mm` / `L16_02130` | `0x65a768` | `0x2fb320` | `true` |
| `35mm` / `L16_03041` | `0x65a768` | `0x2fb320` | `true` |
| `70mm` / `L16_03434` | `0x65a768` | `0x2fb320` | `true` |
| `150mm` / `L16_02285` | `0x65a768` | `0x2fb320` | `true` |

The top four store-sample stack VAs are identical across all sampled stores in
all four runs:

`0x2fbf05 -> 0x5509 -> 0x2f67e7 -> 0x2f59a6`

This is the post-store site inside `0x2fb320`, the generic executor return
inside `0x5440`, the selected `0x2f6420` arm return, and the parent `0x2f53d0`
loop/final caller context.

## Entry Field Shape

At entry, the callback object fields `+0x08`, `+0x10`, and `+0x18` all decode
as readable descriptor-like records in every captured sample. In every captured
sample, those three descriptor records have matching `(width, height, stride)`
tuples within the sample.

The first captured entry sample per focal length had these shapes:

| LRI / focal | `+0x08` descriptor | `+0x10` descriptor | `+0x18` descriptor |
|---|---:|---:|---:|
| `28mm` / `L16_02130` | `8 x 8`, stride `8` | `8 x 8`, stride `8` | `8 x 8`, stride `8` |
| `35mm` / `L16_03041` | `8 x 8`, stride `8` | `8 x 8`, stride `8` | `8 x 8`, stride `8` |
| `70mm` / `L16_03434` | `9 x 9`, stride `9` | `9 x 9`, stride `9` | `9 x 9`, stride `9` |
| `150mm` / `L16_02285` | `9 x 9`, stride `9` | `9 x 9`, stride `9` | `9 x 9`, stride `9` |

The callback object field `+0x20` decodes as a readable `vec4` coefficient
pointer. The same five coefficient vectors were observed in the captured entry
windows for every focal length:

| Vector |
|---|
| `(0.04374999925494194, 0.08749999850988388, 0.08749999850988388, 0.04374999925494194)` |
| `(0.08749999850988388, 0.17499999701976776, 0.17499999701976776, 0.08749999850988388)` |
| `(0.17499999701976776, 0.3499999940395355, 0.3499999940395355, 0.17499999701976776)` |
| `(0.3499999940395355, 0.699999988079071, 0.699999988079071, 0.3499999940395355)` |
| `(0.699999988079071, 1.399999976158142, 1.399999976158142, 0.699999988079071)` |

This proves descriptor-like field shape and coefficient-vector custody at the
sampled worker entry boundary. It does not assign public field names or camera
membership to those descriptors.

## Store Mechanics

Static disassembly of `0x2fb320` shows the final store sequence:

`rcpps %xmm3, %xmm0; mulps %xmm4, %xmm0; movaps %xmm0, (%r15,%rdx)`

The post-store breakpoint at `0x2fbf05` captures the state immediately after
that sequence. For all `64` sampled post-stores per focal length:

- destination memory at `r15 + rdx` equals captured `xmm0`
- `xmm3` is the captured normalizer-sum vector
- `xmm4` is the captured weighted-sum vector
- `xmm0` matches approximate reciprocal-normalized `xmm4 / xmm3`, with the
  expected `rcpps` approximation delta rather than exact Python division

| LRI / focal | `dest == xmm0` samples | Max abs delta from direct `xmm4 / xmm3` |
|---|---:|---:|
| `28mm` / `L16_02130` | `64 / 64` | `0.0004618453655682586` |
| `35mm` / `L16_03041` | `64 / 64` | `0.0004794662407232586` |
| `70mm` / `L16_03434` | `64 / 64` | `0.00011874253081245456` |
| `150mm` / `L16_02285` | `64 / 64` | `0.0001872559188192957` |

## Proven Boundary

- Under the first visible-`src1` `0x3e4b09` gate, the selected `0x2fb320`
  worker is live across `28mm`, `35mm`, `70mm`, and `150mm`.
- The live callback object points to address point `0x65a768`, slot `+0x30 =
  0x2fb320`, in every captured entry sample.
- Callback fields `+0x08`, `+0x10`, and `+0x18` are readable same-shaped
  descriptor-like records in every captured entry sample.
- Callback field `+0x20` is a readable `vec4` coefficient pointer in every
  captured entry sample, with five observed coefficient vectors shared by the
  captured windows at all four focal lengths.
- The final sampled store writes the approximate reciprocal-normalized weighted
  result `xmm4 / xmm3` into destination memory.

Together with the prior static body classification, this bounds the tested
`0x2fb320` route as local descriptor filtering / normalized weighted `vec4`
store work, not as the proven `src1` / `src2` merge/reduction closure.

## Non-Claims

- This does not identify semantic `src1` or `src2` contents.
- This does not assign public names to callback fields, descriptor roles, or
  coefficient vectors.
- This does not prove every possible caller of `0x2fb320`; the scope is the
  tested first-visible-`src1` route after the `0x3e4b09` gate.
- This does not globally refute `0x2f78e0`; that exclusion remains scoped to
  the preceding callback-arm proof.
- This does not close C6 routing.
- This does not close final merge acceptance/rejection.
- This does not close `CLM-PREFUSION-002`.

## Next Proof

Do not keep chasing the selected `0x2fb320` worker as the likely reducer
closure under this route. The next useful Lane A step is to move beyond this
bounded helper path toward upstream payload/source contents or downstream
distributed selection/acceptance surfaces that can still expose the actual
multi-input merge/reduction mechanism.
