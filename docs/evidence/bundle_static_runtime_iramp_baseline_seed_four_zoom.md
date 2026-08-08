# Static/Runtime Evidence: IRAMP Baseline Numerator and Denominator Seed

**Date:** 2026-07-16  
**Status:** VERIFIED; admitted as a `CLM-MERGE-005` addendum  
**Scope:** SHA-pinned installed bundle; retained canonical Unit-1 `35mm`
baseline and nonbaseline whole-scratch captures; prior complete canonical
Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` IRAMP liveness

## Question

The denominator entering `0x36e530` was already known to start at `0.2`, and
the inverse reconstruction formula was bit-closed. The remaining
implementation question was the matching numerator baseline: whether the
reference contribution is zero, raw `src2`, or a weighted transform of
`src2`.

## Result

For the already Ohta-domain 16-by-16 `src2` reference patch, let
`C = forward97(src2)` be the spatial CDF 9/7 coefficient tile produced by
`0x36b920`. The installed baseline initialization is:

```text
numerator_coefficient[y,x] = float32(0.2f * C[y,x])
denominator[scale]         = vec4(0.2f), scale = 0..4
```

Surviving candidate coefficient products and their continuous score `t` are
then added through the separately admitted candidate path. Consequently, a
baseline-only packet normalizes `0.2*C` by `0.2` and inverse-transforms back
to the `src2` reference patch.

The exact float32 baseline constant has bits `0x3e4ccccd` and value
`0.20000000298023224`.

## Installed Construction

`0x36b94a..0x36b95d` copies an 80-byte setup table from `0x5e73c0` to
`scratch+0x2580`. The full table is not five copies of `0.2`; only its first
`vec4` is the baseline vector. This distinction is verifier-enforced.

After copying the selected 16-by-16 `src2` patch and completing its forward
spatial CDF 9/7 work, `0x36cc60` loads that first `vec4(0.2f)`. The unrolled
row body `0x36cc83..0x36cd9b` contains exactly 16 multiply/store pairs:

```text
mulps transformed_coefficient, xmm1       # xmm1 = vec4(0.2f)
movaps [scratch + row_offset + column], transformed_coefficient
```

The verified store displacements are every 16-byte slot from `0x1580`
through `0x1670`. The row loop advances by `0x100` and terminates at
`0x1000`, proving coverage of all `16 * 16 = 256` coefficient vectors at
`scratch+0x1580..+0x257f`.

The verifier SHA-pins the complete installed `0x36b920..0x36cdd1` body as:

```text
9996624dc08b8e5a36f026fc4432141d34b6fc697e7d4dbdee14c6e7d1ea1915
```

Installed `libcp.dylib` SHA-256 is:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Retained Runtime Join

The canonical Unit-1 `35mm` baseline capture immediately before `0x36e530`
contains five denominator vectors whose 20 lanes are all exact float32
`0.2`. Direct installed replay of `0x36e530` still matches every captured
output byte. Its inverse output at `scratch+0x1580` was compared against the
raw selected `src2` patch retained at `scratch+0x0000`:

```text
float words compared = 1,024
max absolute error   = 1.9073486328125e-06
mean absolute error  = 1.93338564713e-07
```

That is the expected float32 forward/inverse lifting roundoff and proves the
baseline term is an identity-preserving reference contribution, not a zero
or unrelated prior.

The retained first nonbaseline packet independently has scale denominators:

```text
(1.0625398159, 0.9859229922, 0.6156874895, 0.2, 0.2)
```

The unchanged coarse-scale `0.2` values and increased active fine-scale
values are consistent with the separately proven candidate-score additions;
they are not generalized into stable image-dependent constants.

## Reusable Harness

- `tools/lldb_probes/iramp_baseline_seed/verify_iramp_baseline_seed.py`
- `tools/lldb_probes/iramp_accumulator_reconstruction/run_replay.sh`
- existing direct installed replayer and exhaustive inverse-basis harness
  under `tools/lldb_probes/iramp_accumulator_reconstruction/`
- retained raw captures under `runs/iramp_accumulator_reconstruction/`

Run:

```bash
bash tools/lldb_probes/iramp_accumulator_reconstruction/run_replay.sh
```

Terminal result:

```text
iramp_baseline_static=OK
numerator_seed=0.2f*forward97(src2_patch_coefficients)
denominator_seed=five_vec4(0.2f)
baseline_identity_reconstruction=OK max_abs=1.90734863281e-06
iramp_baseline_seed=OK
```

## Four-Focal Scope

The construction is fixed installed arithmetic with no focal, calibration,
body, or firmware selector. Existing complete canonical Unit-1
`28/35/70/150mm` reports prove the same outer IRAMP, `0x36b920` preparation,
`0x36e530` reconstruction, and weighted accumulator route is live at every
canonical focal tier. The new whole-buffer numerical oracle is Unit-1
`35mm`; it is not misstated as four independent numerator captures.

A second-body packet is unnecessary to establish this fixed installed
multiply/store loop. This evidence does not claim cross-body pixel equality,
equal firmware, or body/firmware causation.

## Admission Boundary

Admitted:

- exact float32 numerator baseline `0.2f * forward97(src2)`;
- exact five-scale denominator baseline `vec4(0.2f)`;
- all-256-coefficient installed store coverage;
- baseline identity consequence through the exact admitted inverse; and
- four-focal liveness through the existing complete-render join.

Not claimed:

- that the entire 80-byte setup table is composed of `0.2`;
- that nonbaseline denominators are fixed constants;
- any new candidate acceptance rule beyond the already admitted policy; or
- body/firmware-dependent arithmetic.
