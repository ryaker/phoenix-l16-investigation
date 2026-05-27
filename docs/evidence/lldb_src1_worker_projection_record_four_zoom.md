# LLDB Evidence: Visible `src1` Worker Projection Record Four-Zoom

## Scope

This note records live runtime packets for the first captured worker and
projection-record path beneath the visible `src1` secondary callable handoff.

It proves only:

- the first captured `0x3e2e90` worker dispatch reaches worker body
  `libcp+0x3e4c50` on `28mm`, true `35mm`, `70mm`, and `150mm`
- the captured worker is tied to the visible `src1` secondary path by the live
  backtrace through `0x3e4b0e`
- the worker callback fields at runtime contain one source image object, one
  output image object, one default-vector pointer, one projection-record
  pointer, and one weight-table pointer
- the first captured worker projection record uses payload-internal index `0`
  to load the callable stored at visible-payload field `+0x170`
- that loaded callable is `payload+0x150`, has vtable/address point
  `base+0x65f188`, and has substantive slot `+0x30 = base+0x3e42e0`

It does not prove:

- the semantic contents of visible `src1`
- that payload-internal projection index `0` is a physical camera id
- the semantic meaning of the projection-record scalar fields
- the exact upstream merge/reduction mechanism behind `src1` / `src2`
- C6 routing
- final merge acceptance / rejection logic
- that the first captured tile or worker range is globally ordered

## Probe Method

The probe used LLDB Python against:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`

Runtime environment:

- `DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `--profile 3 --export-fmt 3`

The probe first armed on the visible `src1` call site at `libcp+0x3e4b09`.
It then captured the first reached worker entry and the first projection
callable load in that worker path, then intentionally killed the process.
These are not render-completion tests.

Breakpoints:

| VA | Meaning |
|---:|---|
| `0x3e4b09` | visible `src1` secondary callable call site into `0x3e2e90` |
| `0x3e3baa` | callback object prepared before executor dispatch |
| `0x3e4c50` | worker entry from callback slot `+0x30` |
| `0x3e4d8e` | projection callable loaded inside the worker |

## Runtime Artifacts

| Zoom | Artifact |
|---|---|
| `28mm` | `/private/tmp/l16_src1_worker_source_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_src1_worker_source_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_src1_worker_source_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_src1_worker_source_probe_150mm.json` |

The temporary probe script was:

`/private/tmp/l16_src1_worker_source_probe.py`

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Capture Counts

| Zoom | `0x3e4b09` hits before kill | `0x3e3baa` hits | `0x3e4c50` captures | `0x3e4d8e` captures | Finish reason |
|---|---:|---:|---:|---:|---|
| `28mm` | `9` | `1` | `1` | `1` | `captured_visible_src1_worker_projection_record` |
| `35mm` | `9` | `1` | `1` | `1` | `captured_visible_src1_worker_projection_record` |
| `70mm` | `8` | `1` | `1` | `1` | `captured_visible_src1_worker_projection_record` |
| `150mm` | `9` | `1` | `1` | `1` | `captured_visible_src1_worker_projection_record` |

The first visible `0x3e4b09` call-site packet in each run had `ecx = 0` and
the already-proven `0x490` visible `src1` payload family:

- payload vtable address point `base+0x65f140`
- payload secondary address point `base+0x65f388`
- payload field `+0x170` points to `payload+0x150`
- `i32+0xf4 = 17`

The captured tile rectangles were scheduler-dependent first packets:

| Zoom | First captured tile rect |
|---|---|
| `28mm` | `[3584,2560,4160,3120]` |
| `35mm` | `[3072,0,3584,512]` |
| `70mm` | `[0,2560,512,3120]` |
| `150mm` | `[1024,1024,1536,1536]` |

These rectangles prove valid first call-site packets were captured. They do
not prove global tile ordering.

## Worker Backtrace Tie To Visible `src1`

All four captured worker packets shared the same first seven libcp-relative
frames:

| Zoom | Worker frames |
|---|---|
| `28mm` | `0x3e4c50 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3e3bce <- 0x3e4b0e <- 0x3d4842` |
| `35mm` | `0x3e4c50 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3e3bce <- 0x3e4b0e <- 0x3d4842` |
| `70mm` | `0x3e4c50 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3e3bce <- 0x3e4b0e <- 0x3d4842` |
| `150mm` | `0x3e4c50 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3e3bce <- 0x3e4b0e <- 0x3d4842` |

All four captured projection-callable packets shared the same first seven
libcp-relative frames with `0x3e4d8e` at the top:

`0x3e4d8e <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3e3bce <- 0x3e4b0e <- 0x3d4842`

This is the live bridge between the already-proven visible `src1` secondary
callable handoff and the deeper `0x3e4c50` worker packet captured here.

## Worker Callback Facts

For the first captured `0x3e4c50` worker entry in each run:

| Zoom | Worker range | Source image dimensions | Output image dimensions | Callback `+0x08` | Callback `+0x10` | Callback `+0x18` | Callback `+0x20` | Callback `+0x28` |
|---|---|---|---|---|---|---|---|---|
| `28mm` | `[0,0,128,128]` | `514 x 514` | `512 x 512` | source image | output image | default-vector pointer | projection-record pointer | weight-table pointer |
| `35mm` | `[0,0,128,128]` | `518 x 518` | `512 x 512` | source image | output image | default-vector pointer | projection-record pointer | weight-table pointer |
| `70mm` | `[0,0,128,128]` | `514 x 564` | `512 x 560` | source image | output image | default-vector pointer | projection-record pointer | weight-table pointer |
| `150mm` | `[0,0,128,128]` | `518 x 518` | `512 x 512` | source image | output image | default-vector pointer | projection-record pointer | weight-table pointer |

The source and output image pointers are stack-local image-like objects in the
captured worker packets. This table records the first observed dimensions only;
it does not name the border, halo, or crop semantics.

## Projection Record Facts

For the first captured `0x3e4d8e` packet in each run:

| Zoom | Projection record low i32 `+0x0` | Projection base register `r8` | Callable slot address | Callable slot value | Callable vtable | Callable slot `+0x30` |
|---|---:|---|---|---|---|---|
| `28mm` | `0` | visible `src1` payload | `payload+0x170` | `payload+0x150` | `base+0x65f188` | `base+0x3e42e0` |
| `35mm` | `0` | visible `src1` payload | `payload+0x170` | `payload+0x150` | `base+0x65f188` | `base+0x3e42e0` |
| `70mm` | `0` | visible `src1` payload | `payload+0x170` | `payload+0x150` | `base+0x65f188` | `base+0x3e42e0` |
| `150mm` | `0` | visible `src1` payload | `payload+0x170` | `payload+0x150` | `base+0x65f188` | `base+0x3e42e0` |

This proves a payload-internal projection callable lookup for the first
captured worker packet. It does not prove that projection-record index `0` is
a camera id.

The projection-record `+0x08` qword equaled the visible `src1` payload address
in all four packets.

The following projection-record qwords were captured but are not yet decoded:

| Zoom | Projection record `+0x20` | Projection record `+0x28` |
|---|---:|---:|
| `28mm` | `0x40000000600` | `0x40000000600` |
| `35mm` | `0x7fc00000000` | `0x80000000000` |
| `70mm` | `0x9fc00000000` | `0xa0000000000` |
| `150mm` | `0x3fc000003fc` | `0x40000000400` |

## Threading Caveat

At `70mm` and `150mm`, the `callback_ready_3e3baa` packet and worker packet
used the same callback pointer and thread. At `28mm` and `35mm`, the worker was
captured on a different thread from the first armed visible call-site packet,
so the probe's `expected_callback` field stayed null.

The worker/projection packets are still tied to the visible `src1` path by the
live backtrace through `0x3e4b0e <- 0x3d4842` in all four runs. The equality of
`expected_callback` is not used as evidence for the wide-tier rows.

## Relation To Static Bundle Proof

[bundle_proof_src1_project_roi_worker.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_project_roi_worker.md)
already proved statically that:

- `0x3e2e90` builds a callback with address point `base+0x65f408`
- callback slot `+0x30` is worker `base+0x3e4c50`
- `0x3e4c50` is a range worker over one output region
- the worker projects each sample through one callable
- the worker samples one source image/cache buffer with a 4x4 SIMD
  neighborhood and a 64-entry cubic weight table

This runtime note adds four-zoom proof that the first captured worker and its
projection-record load are live underneath the already-proven visible `src1`
secondary-callable handoff.

## Safe Conclusions

- Proven:
  the first captured worker path under visible `src1` reaches `0x3e4c50` on
  the corrected canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR seeds.
- Proven:
  the captured worker/projection packets are tied to visible `src1` by the
  shared live backtrace through `0x3e4b0e <- 0x3d4842`.
- Proven:
  the runtime callback fields match the static layout: source image, output
  image, default vector, projection record, and weight table.
- Proven:
  the first captured projection-record packet uses internal index `0` to load
  the callable at visible-payload field `+0x170`, whose value is
  `payload+0x150`.
- Proven:
  the loaded callable address point is `base+0x65f188`, with substantive
  `+0x30` slot `base+0x3e42e0`.
- Still unproven:
  the semantic source-camera contents behind visible `src1`.
- Still unproven:
  whether the exact `src1` / `src2` mechanism is one reducer, multiple
  distributed stages, or a different topology.
- Still unproven:
  C6 routing and final merge acceptance / rejection logic.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It converts the previously static `0x3e2e90` / `0x3e4c50` project-ROI worker
topology into four-zoom runtime evidence under the visible `src1` path, and it
identifies `base+0x3e42e0` as the next proven callable body on that path.

It does not close `CLM-PREFUSION-002`.
