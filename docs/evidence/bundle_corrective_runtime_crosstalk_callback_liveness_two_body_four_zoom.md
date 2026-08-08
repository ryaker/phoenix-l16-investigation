# Corrective Cross-Talk Callback Liveness and Demosaic Custody

## Result

The earlier cross-talk exclusion in
`bundle_static_runtime_correction_liveness_public_schema_four_zoom.md` is
refuted. That census described vtable slot `+0x30` but breakpointed the four
slot-`+0x38` functions. Installed bytes prove generic executor `0x2e20`
dispatches slot `+0x30`.

Completed profile-3 renders execute
`RemoveCrossTalkGeneric<float,true>` callback `libcp+0x1054d0` at Unit-1
`28/35/70/150mm` and exact-`70mm` Unit-2. The other three slot-`+0x30`
specializations and all four slot-`+0x38` functions are unobserved under
these runs. A selected A1 lineage capture further joins the stage-5 result to
the scalar input consumed by stage-6 demosaic.

This proves application and custody, but does not yet make the 6064-byte
`0x1054d0` arithmetic formula spec-ready.

## Installed Proof

- binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- SHA-256: `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- verifier:
  `tools/lldb_probes/correction_liveness/verify_crosstalk_callback_slots.py`

The verifier reproduces these vtable slots directly from the installed
Mach-O:

| Specialization | vtable | `+0x30` callback | `+0x38` secondary |
|---|---:|---:|---:|
| `vec4,false` | `0x653070` | `0xfebf0` | `0x100560` |
| `float,false` | `0x6530f8` | `0x100680` | `0x1019a0` |
| `vec4,true` | `0x653178` | `0x103120` | `0x1053b0` |
| `float,true` | `0x6531f8` | `0x1054d0` | `0x106c80` |

At both executor dispatches, `libcp+0x2ed5` and `+0x2f1c`, installed bytes
are `ff 50 30`, or `call qword ptr [rax+0x30]`. The verifier also pins body
hashes for executor `0x2e20`, selected callback `0x1054d0`, stage-5 wrapper
`0x341b30`, and demosaic handoff `0x342ca0`.

## Runtime Proof

Harnesses:

- `tools/lldb_probes/correction_liveness/correction_liveness_probe.py`
- `tools/lldb_probes/correction_liveness/run_four_zoom.sh`
- `tools/lldb_probes/correction_liveness/unit{1,2}_*.lldb`
- `tools/lldb_probes/correction_liveness/verify_crosstalk_liveness_correction.py`
- `tools/lldb_probes/create_stereo_color_public_reconstruction/stage_vector_probe.py`
- `tools/lldb_probes/create_stereo_color_public_reconstruction/run_stage_vector.sh`

The cross-talk callbacks use native one-shot breakpoints. The harness records
all thread PCs in the first stop batch, retires the hot breakpoint, resumes,
and requires completed output. This avoids treating a mid-render hit as a
completed-render census.

| Body / focal | Completed | observed slot-`+0x30` callback | all other cross-talk sites |
|---|---:|---:|---:|
| Unit-1 `28mm` | yes, exit `0` | `0x1054d0` | `0` |
| Unit-1 `35mm` | yes, exit `0` | `0x1054d0` | `0` |
| Unit-1 `70mm` | yes, exit `0` | `0x1054d0` | `0` |
| Unit-1 `150mm` | yes, exit `0` | `0x1054d0` | `0` |
| Unit-2 exact `70mm` | yes, exit `0` | `0x1054d0` | `0` |

Counts above are incidence values because the selected breakpoint is
one-shot. They are not total algorithmic row counts.

## Downstream Custody

Stage wrapper `0x341b30` invokes true factory `0xfb6a0` and installs the
returned scalar descriptor at payload `+0xd0`. At demosaic callsite
`0x342d99`, the selected callback adapter `0x342b80` passes a clipped local
view of payload `+0xd0` to `DemosaickLightV1` entry `0x2eb560`.

The focused Unit-1 `28mm` A1 report records:

- `1,247` hits at selected callback `0x1054d0`;
- `0` hits at former false exclusion target `0x106c80`;
- `240/240` captured demosaic calls where payload `+0xd0` and the local
  demosaic input descriptor have the same allocation owner.

This is direct descriptor custody from applied scalar cross-talk correction
into demosaic, not configuration-only liveness.

## Admission Boundary

- Four-zoom: Unit-1 `28/35/70/150mm`, complete profile-3 renders.
- Cross-unit: exact-`70mm` Unit-2, complete profile-3 render.
- Public schema retained from prior evidence:
  `VignettingCharacterization.crosstalk` is a `17x13` grid of public 4x4
  matrices.
- Corrective consequence: the version-3.0.263 cross-talk exclusion and the
  cross-talk part of version-3.0.265 closure are superseded.
- `CLM-CORRECTION-001` returns to `PARTIAL` / `BLOCKER` until the selected
  scalar callback formula, public matrix/IR-table use, coordinates, and
  boundary arithmetic are independently replayed.
