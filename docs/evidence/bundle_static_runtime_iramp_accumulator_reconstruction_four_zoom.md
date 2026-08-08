# Static/Runtime Evidence: IRAMP Accumulator Reconstruction Formula

**Date:** 2026-07-02  
**Status:** VERIFIED; admitted as bounded `CLM-PREFUSION-002` / `CLM-MERGE-005` progress  
**Scope:** SHA-pinned installed bundle; baseline and nonbaseline canonical
Unit-1 `35mm` full-buffer capture/replay; prior complete Unit-1 `28mm`,
`35mm`, `70mm`, and `150mm` call/output liveness

## Question

The caller invokes `0x36e530(scratch)` immediately before the proven
16-by-16 Hann-weighted accumulator. Prior evidence showed only that it
reciprocates five vectors, transforms scratch, and returns
`scratch+0x1580`.

This proof asks for the complete clean-room formula of that function.

## Reusable Harness

- `tools/lldb_probes/iramp_accumulator_reconstruction/capture_probe.py`
- `tools/lldb_probes/iramp_accumulator_reconstruction/capture_unit1_35mm.lldb`
- `tools/lldb_probes/iramp_accumulator_reconstruction/capture_nonbaseline_unit1_35mm.lldb`
- `tools/lldb_probes/iramp_accumulator_reconstruction/replay_36e530.c`
- `tools/lldb_probes/iramp_accumulator_reconstruction/dump_transform_basis.c`
- `tools/lldb_probes/iramp_accumulator_reconstruction/analyze_transform_basis.py`
- `tools/lldb_probes/iramp_accumulator_reconstruction/verify_accumulator_reconstruction.py`
- `tools/lldb_probes/iramp_accumulator_reconstruction/run_replay.sh`

Raw buffers and basis outputs are regenerated under ignored
`runs/iramp_accumulator_reconstruction/`; no `/tmp` artifact is cited.

The verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`,
the complete `0x36e530..0x36f7f3` body, constants, and critical opcodes.

## Scratch Layout

The function consumes:

```text
tile[y,x]       = vec4 at scratch + 0x1580 + 16*(16*y+x)
normalizer[s]   = vec4 at scratch + 0x2580 + 16*s, s=0..4
selector[y,x]   = byte at scratch + 0x25d0 + 16*y+x
```

The 256 selector bytes exactly obey:

```text
selector(x,y) = min(v2(x), v2(y), 4)
v2(0) = 4
```

Thus `(0,0)` selects scale `4`; odd rows or columns select scale `0`;
positions divisible by `2`, `4`, or `8` select the corresponding coarser
dyadic level.

## Scale Normalization

`0x36e530..0x36e5ed` computes five SIMD reciprocal approximations:

```text
inverse_normalizer[s] = rcpps(normalizer[s])
```

It then normalizes each interleaved coefficient independently:

```text
tile[y,x] *= inverse_normalizer[selector(y,x)]
```

All operations are lane-wise float32. Bit-exact implementations must retain
the installed `rcpps` approximation.

## Inverse Lifting Step

The remaining body is a four-stage inverse CDF 9/7 lifting reconstruction.
For an active even-length interleaved vector `z`, even indices are the
current low-pass samples and odd indices are detail samples.

The installed float32 steps are:

```text
even = even*0.869864404
       - odd_neighbor_sum*0.509857476

odd  = odd*1.14960444
       + even_neighbor_sum*(-0.882911086)

even = even
       - odd_neighbor_sum*(-0.0529801175)

odd  = odd
       + even_neighbor_sum*1.58613431
```

At a missing endpoint neighbor, the present neighbor is reflected. The
binary uses the fused doubled constants:

```text
1.01971495, -1.76582217, -0.105960235, 3.17226863
```

Every multiply, add, and subtract is rounded in the installed float32
operation order.

## Four-Level 2D Schedule

Starting from the normalized interleaved 16-by-16 tile:

```text
for stride in (8, 4, 2, 1):
    active = (0, stride, 2*stride, ..., 15)
    inverse97 each active row across active columns
    inverse97 each active column across active rows
```

This is a Mallat-style joint low-low recursion. The complete multilevel 2D
operator is therefore not one global Kronecker product, even though each
stage is separable.

The return pointer is exactly `scratch+0x1580`.

## Exhaustive Basis Proof

The basis harness calls transform entry `0x36e5ef` once for every one-hot
input coefficient in the 16-by-16 tile and records all 256 scalar outputs:

```text
256 inputs * 256 outputs = 65,536 float32 comparisons
```

The clean-room four-stage formula above matches all 65,536 installed outputs
bit-for-bit:

```text
schedule=horizontal_then_vertical
basis_exact_float_bits=65536/65536
basis_max_abs_error=0
iramp_inverse_transform_basis=OK
```

## Live Whole-Buffer Replays

Two canonical Unit-1 `35mm` calls were captured before and after
`0x369f34 -> 0x36e530`.

Baseline-only packet:

```text
normalizers = (0.2, 0.2, 0.2, 0.2, 0.2)
reciprocals = (5, 5, 5, 5, 5)
return      = scratch+0x1580
mismatched replay bytes = 0
```

First nonbaseline packet, reached at observed call pair 190:

```text
normalizers =
  (1.0625398159, 0.9859229922, 0.6156874895, 0.2, 0.2)
return      = scratch+0x1580
mismatched replay bytes = 0
```

Both calls modify only `scratch+0x1580..+0x25cf`, exactly the coefficient
tile plus the five in-place reciprocal vectors. Selector bytes remain
unchanged.

## Four-Zoom Scope

`bundle_lldb_iramp_36e530_accumulator_prep.md` already proves that complete
canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` bridge-HDR runs invoke
the same installed body, receive `scratch+0x1580`, and feed its output into
the 16-by-16 outer-product accumulator. The formula has no zoom branch.

The new full-buffer formula oracle uses canonical Unit-1 `35mm`; it is not
misstated as four independent full-buffer captures. The canonical quartet
is one calibration body, and numerical differences are not attributed to
body or firmware.

## Verification Output

```text
unit1_35mm: OK normalizers=0.2,0.2,0.2,0.2,0.2
unit1_35mm_nonbaseline: OK normalizers=1.06253982,0.985922992,0.61568749,0.2,0.2
inverse97_basis=OK exact_float_bits=65536/65536
iramp_accumulator_reconstruction_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
selector=min(v2(x),v2(y),4)
inverse97=strides_8_4_2_1_horizontal_then_vertical_symmetric
iramp_accumulator_reconstruction=OK
```

## Admission Boundary

Admitted:

- the exact scratch layout consumed by `0x36e530`;
- the dyadic scale-selector formula;
- five-vector reciprocal coefficient normalization;
- the exact four-stage inverse 9/7 lifting formula, order, and symmetric
  endpoint behavior;
- exhaustive bit-exact transform-basis equality;
- two byte-exact whole-buffer live replays; and
- prior complete four-focal call/output liveness joined to the static formula.

Still open:

- exhaustive upstream candidate construction and sentinel policy;
- a public schema name for the internal three-float tuple, if one exists;
- MonoFusion mode `1` relevance or unreachability; and
- final global contributor acceptance/rejection.

`CLM-PREFUSION-002` and `CLM-MERGE-005` remain `PARTIAL` blockers.
