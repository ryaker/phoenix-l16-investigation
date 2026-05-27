# Visible `src1` Source-Producer Virtual Target, Four-Zoom Runtime Proof

**Date:** 2026-05-06
**Status:** admitted evidence candidate for `CLM-PREFUSION-001` / `CLM-PREFUSION-002`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3`

## Purpose

This note follows the source-image producer topology beneath the proven visible
`src1` handoff into `0x3e2e90`.

Earlier proof bounded the static path:

- visible `src1` secondary callable callsite: `libcp+0x3e4b09`
- visible `src1` payload/body: `0x3e4a80 -> 0x3e2e90`
- source-image producer branches inside `0x3e2e90`: `0x31af30` and `0x31acf0`
- lower producer/iterator sites: `0x33ede0`, `0x33f480`, `0x33f180`

This runtime probe answers the next bounded question: which tested branch and
which per-source virtual target are reached after the already-proven visible
`src1` gate?

## Probe Method

The lower virtual breakpoints were not enabled at process start. They were gated
behind the already-proven visible `src1` callsite:

1. Break on `libcp+0x3e4b09`, the call from visible `src1` `0x3e4a80` into
   `0x3e2e90`.
2. Enable the three tested `0x3e2e90` producer-branch callsites:
   `0x3e3279`, `0x3e34e2`, and `0x3e3653`.
3. When one of those branch callsites fires, enable the lower per-source virtual
   callsites:
   `0x33f3e8`, `0x33f94f`, and `0x33ffd4`.
4. Capture the first descendant virtual call, dump registers/vtable bytes, print
   the backtrace, then intentionally kill the process.

This is a participation/target probe, not a render-completion test.

## Tested Files

| Zoom | LRI | Path | Probe mode |
|---|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` | start-under-LLDB gated breakpoints |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` | start-under-LLDB gated breakpoints |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` | start-under-LLDB gated breakpoints |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` | attach-mid-render gated breakpoints |

The `150mm` startup breakpoint probe reproduced the known instrumentation race
at `libcp+0x2e945d` before `0x3e4b09` fired. A no-breakpoint LLDB smoke run of
the same `150mm` LRI completed. The admitted `150mm` capture therefore used a
normal render launch followed by LLDB attach after startup, then the same gated
breakpoint method. The failed startup-breakpoint run is not evidence about
pipeline semantics.

## Runtime Artifacts

Temporary scripts used in this session:

- `/private/tmp/l16_src1_visible_gated_virtual_28mm.lldb`
- `/private/tmp/l16_src1_visible_gated_virtual_35mm.lldb`
- `/private/tmp/l16_src1_visible_gated_virtual_70mm.lldb`
- `/private/tmp/l16_src1_visible_gated_virtual_150mm.lldb`
- `/private/tmp/l16_src1_visible_gated_virtual_150mm_attach.lldb`
- `/private/tmp/l16_attach_150mm_visible_virtual.sh`
- `/private/tmp/l16_150mm_lldb_nobp_smoke.lldb`

## Four-Zoom Runtime Result

All four canonical zooms reached the same visible-`src1` descendant path:

```text
0x3e4b09 -> 0x3e3279 -> 0x31af30 -> 0x33ede0 -> 0x33f180 -> slot +0x30
```

The first descendant virtual call captured in every run was:

```text
0x33f3e8: callq *0x30(%rax)
```

The vtable/address point and slot target were identical after normalizing ASLR:

| Zoom | Vtable/address point | Slot `+0x30` target | Reached virtual site |
|---|---:|---:|---:|
| `28mm` | `base+0x65b3c8` | `base+0x341770` | `0x33f3e8` |
| `35mm` | `base+0x65b3c8` | `base+0x341770` | `0x33f3e8` |
| `70mm` | `base+0x65b3c8` | `base+0x341770` | `0x33f3e8` |
| `150mm` | `base+0x65b3c8` | `base+0x341770` | `0x33f3e8` |

The other two armed lower sites had zero hits before the intentional kill in
these captures:

- `0x33f94f`: zero captured hits
- `0x33ffd4`: zero captured hits

The alternate `0x3e2e90` branches also had zero captured hits before the
intentional kill:

- `0x3e34e2`: zero captured hits
- `0x3e3653`: zero captured hits

These are first-capture facts only. They do not prove those sites never fire in
the full render.

## Backtrace Ancestry

The first captured descendant virtual call shared the same normalized ancestry
shape:

```text
0x33f3e8
0x33f042
0x31b06c
0x3e327e
0x3e4b0e
0x3d4842
0x5d97
0x3873 / 0x55a2 scheduler/executor frames
```

This ties the virtual target to the gated visible `src1` callsite. It is not a
generic early `0x33f180` hit.

## Run-Local Pointers

The raw pointers below are run-local. Only the ASLR-normalized addresses above
are stable installed-bundle facts.

| Zoom | Captured object pointer at virtual call | Captured record pointer (`rsi`) | Runtime vtable pointer | Runtime slot target |
|---|---:|---:|---:|---:|
| `28mm` | `0x7fc61baa02e0` | `0x30432b678` | `0x1092d53c8` | `0x108fbb770` |
| `35mm` | `0x7fda7f8092e0` | `0x304537528` | `0x1092d53c8` | `0x108fbb770` |
| `70mm` | `0x7fcfce8786e0` | `0x3042a8528` | `0x1092d53c8` | `0x108fbb770` |
| `150mm` | `0x7fcc7f125ee0` | `0x30c609528` | `0x10d3543c8` | `0x10d03a770` |

The first eight vtable entries at address point `0x65b3c8` are:

```text
0x65b3c8: 0x341700 0x341710
0x65b3d8: 0x341720 0x341740
0x65b3e8: 0x341750 0x341760
0x65b3f8: 0x341770 0x341a30
```

## Static Body Bound For `0x341770`

Installed-bundle disassembly of `libcp+0x341770` shows:

- the body treats `rsi` as the per-source record produced by `0x33f180`
- it clips/intersects integer region fields from the record
- it computes pointer offsets into image-like backing storage using stride and
  element-size arithmetic
- it calls `0xf2750` and `0xf32d0` from the record-associated object
- it calls helper `0x2e8680`, which is bounded separately in
  [bundle_proof_src1_region_adapter_helper_2e8680.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_region_adapter_helper_2e8680.md)
- it writes adjusted region / image-record fields back to the same record,
  including fields around `+0x100..+0x128`
- it returns after record cleanup/destructor helper calls

Safe conclusion: `0x341770` is a live per-source region-adapter / record-update
callback beneath the visible `src1` source-image producer. The body itself is
not the missing multi-source reducer or final blend closure.

The helper `0x2e8680` is now separately bounded as one-source Bayer/RAW
region-helper work with callback slot `0x2e8cc0`. This note still does not
assign it a public name.

## Safe Conclusions

- The first visible `src1` source-producer branch captured across the canonical
  quartet is `0x3e3279 -> 0x31af30`.
- The first lower producer reached from that branch is the `0x33ede0 ->
  0x33f180` path.
- The first per-source virtual target captured beneath visible `src1` is vtable
  address point `0x65b3c8`, slot `+0x30 = 0x341770`.
- Static inspection bounds `0x341770` to per-source region adaptation /
  record-update work.
- This narrows the `src1` source-image producer branch, but it does not close
  semantic `src1` contents, camera membership, C6 routing, or the exact
  `src1` / `src2` merge/reduction mechanism.

## Non-Conclusions

- Do not claim `0x33f94f` or `0x33ffd4` never fire. They had zero hits only
  before the intentional first-capture kill in this probe.
- Do not claim `0x3e34e2` or `0x3e3653` never fire. They had zero hits only
  before the intentional first-capture kill in this probe.
- Do not call `0x341770` a blend, reducer, acceptance, or final merge routine.
- Do not use the failed `150mm` startup-breakpoint crash as evidence about
  shipped Lumen behavior.
