# Static/Runtime Evidence: IRAMP Two-Scale Patch-Score Formula

**Date:** 2026-07-02  
**Status:** VERIFIED; admitted as bounded `CLM-PREFUSION-002` / `CLM-MERGE-005` progress  
**Scope:** SHA-pinned installed bundle; bit-exact Unit-1 `35mm` capture/replay;
prior complete Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` score-site liveness

## Question

The outer IRAMP custody proof identifies `0x36cde0(reference,candidate)` as
the continuous scalar controlling normalized candidate contribution. This
proof asks for its clean-room formula.

It does not ask for the separate `0x36e530` preparation formula or the
exhaustive candidate/sentinel policy.

## Reusable Harness

- `tools/lldb_probes/iramp_score_kernel/capture_probe.py`
- `tools/lldb_probes/iramp_score_kernel/capture_unit1_35mm.lldb`
- `tools/lldb_probes/iramp_score_kernel/replay_36cde0.c`
- `tools/lldb_probes/iramp_score_kernel/stage_probe.py`
- `tools/lldb_probes/iramp_score_kernel/replay_stages.lldb`
- `tools/lldb_probes/iramp_score_kernel/verify_iramp_score_kernel.py`
- `tools/lldb_probes/iramp_score_kernel/run_probe.sh`

Raw inputs and reports are regenerated under ignored
`runs/iramp_score_kernel/`; no `/tmp` artifact is an evidence dependency.

The verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`,
the complete `0x36cde0..0x36e52f` body, normalization helper
`0x371ed0..0x3720ab`, all formula constants, and critical opcodes.

## Formula

Let `r[i,l]` be the prepared reference patch and `c[i,l]` the warped
candidate, with 256 `vec4` samples and lanes `l=0..3`.

### 1. Candidate luminance normalization

Helper `0x371ed0` computes:

```text
k = reference_l1 * rcp(1e-5 + sum_i(abs(c[i,0])))
c[i,0..2] *= k
c[i,3] is unchanged
```

`reference_l1` is read from prepared reference scratch `+0x26d0`.
`rcp` denotes the installed SSE reciprocal approximation.

### 2. Structural similarity at two scales

For each scale `s`, the body computes per-lane means, second moments, and
cross moments:

```text
mu_c = E(c)
mu_r = E(r)
var_c = max(E(c*c) - mu_c*mu_c, 0)
var_r = max(E(r*r) - mu_r*mu_r, 0)
cov   = max(E(c*r) - mu_c*mu_r, 0)
```

Fine scale uses all 256 samples (`E = sum/256`). Coarse scale uses the
64-sample low-pass representation (`E = sum/64`).

With:

```text
C = (0.01, 0.03, 0.03, 1.0)
b = (-0.8, -0.8, -0.8, -0.0)
g = (5.26315784, 5.26315784, 5.26315784, 1.0)
a_fine   = mu_c[3]
a_coarse = 0.5 * mu_c[3]
```

the per-lane structural vectors are:

```text
u_s = clamp(
  g * (a_s * (2*cov + C) * rcp(var_c + var_r + C) + b),
  0,
  1
)
```

The installed code uses `rcpps`, so bit-exact implementations must preserve
its reciprocal approximation and float32 operation order.

### 3. Fixed lifting transform and detail agreement

The candidate is transformed with the fixed lifting coefficients:

```text
1.58613431, 3.17226863,
-0.0529801175, -0.105960235,
-0.882911086, -1.76582217,
1.14960444, 0.869864404
```

The body sums absolute transformed detail coefficients into `S_fine` and
`S_coarse`. Prepared reference-detail accumulators are
`R_fine = scratch+0x1540` and `R_coarse = scratch+0x1550`.

```text
d_fine = clamp(
  1 - 8 * (R_fine + (-1/192)*S_fine) / (R_fine + 0.05),
  0,
  1
)

d_coarse = clamp(
  1 - 8 * (R_coarse + (-1/96)*S_coarse) / (R_coarse + 0.05),
  0,
  1
)
```

Again, the installed divisions are reciprocal approximations. Only lane 0
receives the detail factor:

```text
v_fine   = u_fine   * (d_fine,   1, 1, 1)
v_coarse = u_coarse * (d_coarse, 1, 1, 1)
```

### 4. Scalar reduction

The exact return is:

```text
score = sqrt(min4(v_coarse) * min4(v_fine))
```

The caller stores this continuous score as tuple field 3. Prior admitted
proof shows it subsequently controls candidate multiplication and the
normalization denominator; it is not a binary accept/reject flag.

## Live Capture and Bit-Exact Replay

The harness captured a prepared nonzero packet at `0x369e3f` from canonical
Unit-1 `35mm`, including `0x2800` reference scratch bytes and the `0x1000`
candidate patch. Standalone replay through the installed function reproduces
the live result bit-for-bit:

```text
fine structural vector   = (0.843024850, 1, 1, 1)
fine detail factor       = (1, 1, 1, 1)
fine min                 = 0.843024850

coarse structural vector = (0.336412072, 1, 1, 1)
coarse detail factor     = (0.842139959, 1, 1, 1)
coarse min               = 0.283306062

score = sqrt(0.283306062 * 0.843024850)
      = 0.488706499
bits  = 0x3efa37bd
```

Exact scalar division gives coarse detail approximately `0.842136008`; the
captured `0.842139959` is the expected `rcpss` operation-order result.

## Four-Zoom Scope

`lldb_iramp_w5_magnitude_repro_four_zoom.md` already captures non-degenerate
`0x36e511 -> 0x36e515` factor multiplication and square root on canonical
Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`.
`bundle_static_runtime_iramp_operand_roles_four_zoom.md` joins the same
installed function to reference/candidate custody and weighted-contribution
consequence at all four focals.

The formula itself is SHA-pinned installed code and has no zoom branch. The
new bit-exact full-input replay is one Unit-1 `35mm` packet; it is not
misstated as four independent full-input captures. The canonical quartet is
one calibration body, and capture differences are not attributed to body or
firmware.

## Verification Output

```text
iramp_score_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
fine_min=0.84302485 coarse_min=0.283306062
score=sqrt(fine_min*coarse_min)=0.488706499 bits=0x3efa37bd
iramp_score_kernel=OK
```

## Admission Boundary

Admitted:

- the complete clean-room scalar formula of installed `0x36cde0`;
- candidate lane-0 L1 normalization to prepared reference L1;
- fine/coarse structural vectors, fixed lifting/detail factors, `min4`
  reductions, and geometric-mean return;
- one bit-exact live-input replay; and
- prior four-focal liveness/consequence joined to this static formula.

Still open:

- a complete clean-room expansion of `0x36e530`;
- exhaustive candidate construction, sentinel, and continuous-score policy;
- a public schema name for the internal tuple score, if one exists; and
- final global contributor acceptance/rejection outside this bounded score.

`CLM-PREFUSION-002` and `CLM-MERGE-005` remain `PARTIAL` blockers.
