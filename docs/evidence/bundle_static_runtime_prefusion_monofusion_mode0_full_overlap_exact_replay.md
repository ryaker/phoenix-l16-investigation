# MonoFusion Mode-0 Complete Overlap Exact Replay

**Date:** 2026-08-08  
**Claim:** `CLM-PREFUSION-002` corrective addendum  
**Result:** `PROVEN` at the scope below

## Purpose

This bundle removes the remaining all-patch caveat from the admitted mode-0
MonoFusion scalar path. It regenerates one complete `522x522` pre-combine
overlap image from every contributing patch without using the captured overlap
image or captured overlap taps as inputs, then compares all output words to the
live installed result.

It also closes the patch-noise domain rule exposed only at reducer tile edges:
the auxiliary mean and target harmonic statistic use independently clipped
views because the auxiliary descriptor retains the full `4160x3120` image
domain while the target descriptor has the `522x522` reducer-tile domain.

## Custody and Reproduction

Installed image:

```text
/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
SHA-256 b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Runtime input:

```text
Unit-1 exact 28mm
/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri
```

Reusable harness:

```text
tools/lldb_probes/prefusion_monofusion_mode0_tile/
  mode0_tile_probe.py
  unit1_28mm.lldb
  unit1_28mm_patch_512.lldb
  run_unit1_28mm.sh
  run_unit1_28mm_patch_512.sh
  verify_full_overlap.py
```

The ignored captures are under
`runs/prefusion_monofusion_mode0_tile/`. Reproduce and verify with:

```bash
bash tools/lldb_probes/prefusion_monofusion_mode0_tile/run_unit1_28mm.sh
bash tools/lldb_probes/prefusion_monofusion_mode0_tile/run_unit1_28mm_patch_512.sh
python3 tools/lldb_probes/prefusion_monofusion_mode0_tile/verify_full_overlap.py
```

The verifier SHA-pins the installed image and relevant code/table windows and
hash-checks every runtime capture before use.

## Exact Patch Lattice and Gather Policy

The selected top-left output ROI is `522x522`. Mode 0 visits the Cartesian
patch-origin lattice

```text
x0,y0 in {-8,0,8,...,520}
```

for `67*67 = 4,489` total `16x16` patches. Flow lookup uses

```text
flow_x = clamp(trunc_toward_zero(x0/8), 0, 518)
flow_y = clamp(trunc_toward_zero(y0/8), 0, 388)
source_origin = patch_origin + packed_signed_int16_flow[flow_y,flow_x]
```

Target gathers use nearest-edge clamp to the reducer tile. Of the 4,489 source
rectangles, 3,517 intersect the `4160x3120` source domain and use nearest-edge
source gathers; 972 do not intersect and bypass transform/Wiener processing by
using the spatial target patch directly. Forcing those bypass patches through a
forward/inverse round trip is observably wrong at float32 ULP level.

## Exact Overlap Constants and Arithmetic

Both axes use this installed 16-word table, stated as float32 bits so a
clean-room implementation does not depend on platform `cos` behavior:

```text
3c1d6831 3dac933b 3e638c4d 3ece0e90
3f18f8b9 3f471ced 3f6a6d99 3f7d8a5f
3f7d8a5f 3f6a6d98 3f471cec 3f18f8b7
3ece0e8d 3e638c48 3dac9335 3c1d681e
```

These are the installed binary32 realization of the already admitted
half-sample Hann-16 law. The small left/right ULP asymmetry is real. For a full
patch, helper `0x18ce90` adds

```text
term = f32(f32(pixel * weight_x[patch_x]) * weight_y[patch_y])
```

For a clipped patch it adds

```text
term = f32(f32(weight_y[patch_y] * pixel) * weight_x[patch_x])
```

Each term is then added to the float32 accumulator in patch traversal order.

## Separate-Domain Noise Rule

The first horizontal remainder patch has target origin `(512,-8)`, packed
flow `(177,118)`, and live source domain `[689,110,705,126]`. The clean-room
target gather, target transform, source gather, and source transform each match
all `256/256` live words.

At this patch the auxiliary intersection is `x=512..527, y=0..7` (`16x8`),
because the auxiliary descriptor retains the full-image domain. The target
statistic intersection is `x=512..521, y=0..7` (`10x8`), because the target
descriptor ends at 522. Each scalar reduction uses its own count:

```text
mu = row_major_f32_sum(auxiliary intersection) / auxiliary_count
H  = target reciprocal-square harmonic statistic / target_count
```

Joined to the previously admitted noise model, this independently reproduces:

```text
mu       = 2.6601288318634033
variance = 74.05537414550781
bits     = 0x42941c5a
```

Using the target-tile intersection for both statistics produces
`74.28107452392578` and is refuted. With the corrected variance, all 256 Wiener
coefficients and all 256 inverse spatial words for the remainder patch match
the live buffers exactly.

## Complete Replay Receipt

The verifier generates all target/source patches, domain-specific noise
values, transforms, Wiener blends, inverse patches, invalid-source bypasses,
and overlap additions. The captured pre-combine overlap image is used only as
the final oracle:

```text
remainder_patch=(512,-8) source_domain=[689, 110, 705, 126] variance=74.055374146 exact=OK
{"invalid_source": 972, "patches": 4489, "valid_source": 3517}
exact=272484_of_272484 mismatch=0 max_abs=0 mean_abs=0
prefusion_monofusion_mode0_full_overlap=OK
```

## Scope and Admission

- **Numerical runtime scope:** one complete Unit-1 exact-`28mm` mode-0 overlap
  tile plus a direct live horizontal-remainder patch capture.
- **Installed formula scope:** the SHA-pinned selected mode-0 body and helpers.
- **Four-focal route scope:** prior admitted evidence establishes canonical
  profile-3 `28mm/35mm` mode-0 applicability and `70mm/150mm` MonoFusion bypass
  through direct B4.
- **Body scope:** prior exact-focal two-body flow, operand, vignetting, and
  mode-0 route evidence supplies the body discriminator. This bundle does not
  assert scene-pixel invariance, firmware causation, or a second-body complete
  overlap replay.
- **Not claimed:** compatibility mode 1, other installed builds, or end-to-end
  color/output parity outside this scalar overlap boundary.

Admit the exact lattice, invalid-source spatial bypass, exact overlap constants
and multiply order, separate auxiliary/target edge domains, and complete
all-patch overlap replay as a corrective `CLM-PREFUSION-002` addendum. Claim
status remains `PROVEN` / `SPEC_READY`.
