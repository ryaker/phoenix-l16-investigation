# LLDB Evidence: `0x2f53d0` Callback Bodies Static Classification

## Scope

This note extends
[lldb_2f53d0_downstream_helper_liveness_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_2f53d0_downstream_helper_liveness_four_zoom.md).

The earlier proof establishes runtime liveness, under the first visible-`src1`
gate, for `0x2f53d0`, `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`,
`0x3066d0`, and postbranch `0xab590` across the canonical four-zoom bridge HDR
quartet. It also establishes zero `0x3048b0` hits under those accepted gated
probes.

This document adds installed-bundle static disassembly of the callback bodies
invoked through the generic executor helpers `0x5440` and `0x5670`. It does not
add new runtime liveness beyond the earlier four-zoom helper proof.

Follow-up runtime arm selection is documented separately in
[lldb_2f53d0_callback_arm_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_2f53d0_callback_arm_runtime_four_zoom.md).
That later proof shows the tested first-visible-`src1` route selects the
`0x2fb320` arm across the canonical quartet; this static document remains the
body-family classification record.

## Artifacts

- Static LLDB script:
  [static_2f53d0_callback_vtables.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/static_2f53d0_callback_vtables.lldb)
- Raw static output:
  `runs/2f53d0_downstream_helpers/static_2f53d0_callback_vtables.log`
- Output size: `11391` lines
- Output scan: no `error:`, `warning:`, `Traceback`, `EXC`, `SIGABRT`, or
  `lost connection` lines were present in the raw output under repo-local scan.
- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

All VAs below are installed `libcp.dylib` module VAs.

## Executor Dispatch Shape

Static disassembly of the generic executor helpers shows:

| Helper | Static bound |
|---|---|
| `0x5440` | Generic region executor. It partitions requested work and invokes callback slot `+0x30`; the empty-callback path throws `bad_function_call`. |
| `0x5670` | Generic row executor variant. It also invokes callback slot `+0x30`; the empty-callback path throws `bad_function_call`. |

The callback address-point memory dumps show the substantive worker entry at
slot `+0x30` for the inspected callback families:

| Address point | Slot `+0x30` worker | Parent surface |
|---|---:|---|
| `0x65a450` | `0x2f5fa0` | `0x2f4470` callback family |
| `0x65a4e0` | `0x2f6ad0` | `0x2f6420` kernel-size callback family |
| `0x65a568` | `0x2f78e0` | `0x2f6420` kernel-size callback family |
| `0x65a5e8` | `0x2f87e0` | `0x2f6420` kernel-size callback family |
| `0x65a668` | `0x2f97e0` | `0x2f6420` kernel-size callback family |
| `0x65a6e8` | `0x2fa5d0` | `0x2f6420` kernel-size callback family |
| `0x65a768` | `0x2fb320` | `0x2f6420` kernel-size callback family |
| `0x65a7e8` | `0x2fc140` | `0x2f6420` kernel-size callback family |
| `0x65a868` | `0x2fd070` | `0x2f6420` kernel-size callback family |
| `0x65ab80` | `0x304b10` | `0x3048b0` alternate callback family |
| `0x665268` | `0x16e30` | `0x135d0` callback family |
| `0x652948` | `0xbfa20` | `0xab590` callback family |
| `0x668920` | `0x3070a0` | `0x3066d0` callback family |
| `0x6689a8` | `0x307d90` | `0x3066d0` final row-executor callback family |

## Body Classification

| Worker body / family | Static classification | Boundary |
|---|---|---|
| `0x2f5fa0` | Clips two descriptor-like records to the requested rectangle, loops over the overlap, squares each source `vec4`, multiplies lanes by coefficient vectors from callback fields, sums, applies `sqrtps`, and stores `max(existing_dest, computed)` into the destination descriptor. | Per-pixel/vector descriptor transform and max-update. No inspected N-to-1 camera reducer is exposed. |
| `0x2f6ad0`, `0x2f78e0`, `0x2f87e0`, `0x2f97e0`, `0x2fa5d0`, `0x2fb320`, `0x2fc140`, `0x2fd070` | Switch-selected callback families used by `0x2f6420` after its bilateral-kernel-size dispatch. The inspected bodies share descriptor clipping, temporary descriptor allocation/zeroing, local neighborhood loads, min/max/range work, reciprocal normalization, weighted `vec4` accumulation, and descriptor stores. | Parent `0x2f6420` is runtime-live across the canonical quartet. This proof statically classifies the selected-family bodies but does not prove which switch arms fire in which runtime packets. |
| `0x304b10` | Alternate `0x3048b0` callback body with descriptor clipping/allocation/zeroing, local neighborhood max/difference filtering, reciprocal normalization, vector adds, and descriptor stores. | Static-only in this proof. The parent `0x3048b0` had zero hits under the accepted gated four-zoom probes. |
| `0x16e30 -> 0x16e70` | `0x16e30` is a thunk into `0x16e70`. `0x16e70` intersects descriptor rectangles, derives halved request coordinates, allocates a temporary buffer, initializes it with sentinel values, obtains neighboring rows through helper `0x128b0`, and performs even/odd local `vec4` interpolation/update loops with coefficient vectors before storing into descriptor-backed rows. | Descriptor-local interpolation/filter/update worker. It is not a camera-membership reducer or final acceptance/rejection body. |
| `0xbfa20` | Per-pixel `vec4` transform. It loads four coefficient rows from callback field `+0x8`, broadcasts source lanes `0..3`, multiplies by the rows, adds the four products, and writes the resulting `vec4` to the destination descriptor. | Local 4x4 vector transform. No inspected N-to-1 camera reducer is exposed. |
| `0x3070a0 -> 0x3070e0` | Callback family wired by live parent `0x3066d0`. The body reads a byte vector from callback field `+0x10`, uses neighborhood windows from callback fields, computes range/weight terms with reciprocal normalization, accumulates many neighboring `vec4` values, adds the accumulated vectors into descriptor-backed destinations, and adds a scalar-like accumulator vector into another descriptor. | Byte-vector-driven local accumulation / smoothing callback inside the `0x3066d0` helper surface. This proof does not assign public field names. |
| `0x307d90` | Row-executor callback wired by live parent `0x3066d0`. It reads source, destination, and weight/normalizer descriptors from callback fields, multiplies source lanes by the reciprocal normalizer, preserves/blends lane `3`, and writes rows back to the destination/source descriptor. | Per-row reciprocal normalization. No inspected N-to-1 camera reducer is exposed. |

## Proven Boundary

- The executor callback bodies under the already-live `0x2f53d0` helper chain are
  statically bounded to local descriptor transform, filtering, interpolation,
  normalization, and accumulation surfaces.
- The inspected callback bodies do not expose the semantic `src1` / `src2`
  pre-fusion merge/reduction closure.
- The inspected callback bodies do not expose final contributor
  acceptance/rejection logic.
- `0x304b10` is static-only here because its parent `0x3048b0` has zero hits
  under the accepted gated four-zoom runtime probes.

## Non-Claims

- This proof does not identify semantic `src1` or `src2` contents.
- This proof does not assign public names to callback fields, coefficient
  vectors, byte vectors, or descriptor roles.
- This proof does not prove per-switch-arm runtime liveness for every
  `0x2f6420` callback family.
- This proof does not close `CLM-PREFUSION-002`.
- This proof does not resolve C6 routing.
- This proof does not resolve final merge acceptance/rejection.
