# Evidence: G-49 IRAMP Guarded Sub-Pixel Refinement

## Result

G-49 is formula-closed for the installed IRAMP block-matching route. After
integer WTA and the admitted local `[-2,+2]^2` absolute-difference search,
`0x369b1f..0x369cb0` consumes a row-major `3x3` neighborhood of integer SAD
costs, solves a guarded two-variable quadratic fit in float32, and either
keeps both offsets or resets both to zero.

This is not a separable pair of one-dimensional parabolic fits. The installed
body includes a cross term and solves a coupled `2x2` system.

## Exact Algebra

Let the nine signed-int32 local costs be:

```text
A B C
D E F
G H I
```

All integer expressions below use installed signed 32-bit arithmetic. Define:

```text
Q   = 4 * (A + C + G + I - 4*E)
U   = max(Q + 8*(D + F - B - H), 0)
V   = max(Q + 8*(B + H - D - F), 0)
W0  = 4 * (A + I - G - C)

det0 = f32(f32(V)*f32(U) - f32(W0)*f32(W0))
W    = f32(W0) if 0.0f < det0 else 0.0f
den  = f32(f32(V)*f32(U) - f32(W)*f32(W))
```

The `det0` test does not reject the complete fit. A non-positive preliminary
determinant disables only the cross term by setting `W=0`; the denominator is
then recomputed. If `den == 0.0f`, both offsets are zero.

For nonzero `den`:

```text
GX = 4*(F-D) + 2*(C-G) + 2*(I-A)
GY = 2*(I-A+G-C) + 4*(H-B)

num_x = f32(f32(W)*f32(GY) - f32(V)*f32(GX))
num_y = f32(f32(W)*f32(GX) - f32(U)*f32(GY))
inv   = f32(1.0f / den)
dx    = f32(num_x * inv)
dy    = f32(inv * num_y)
```

The final guard is all-or-nothing:

```text
if !(abs(dx) < 1.0f && abs(dy) < 1.0f):
    dx = 0.0f
    dy = 0.0f
```

The installed comparisons are strict. Equality to `1.0f` rejects. The body
uses the `0x7fffffff` four-lane mask at `0x5a81f0` for scalar absolute values.

The accepted offsets feed the already bounded coordinate assembly:

```text
coord_x = ((dx + coarse_x_local) * (1.0f/3.0f) + coarse_x_base) * object_scale
coord_y = ((dy + coarse_y_local) * (1.0f/3.0f) + coarse_y_base) * object_scale
```

The local/base terms above name arithmetic roles only; this admission does not
assign public calibration names to their stack/register carriers.

## Static Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier pins all 401 bytes of `0x369b1f..0x369cb0` with SHA-256:

```text
9c32d42d9d21931bb56d266c5098f5d6f0024dcedbe1eb3d75661261a69515f9
```

It also asserts the multiply/subtract sequence, preliminary determinant mask,
exact-zero denominator branch, reciprocal/divide order, abs-mask operations,
strict `<1.0f` comparisons, and combined boolean guard.

## Runtime Replay

The focused probe captures the nine costs at `0x369b1f`, optional raw offsets
at `0x369c72`, and final accepted offsets at `0x369cb0`, joined by thread. It
retains 24 complete packets per canonical Unit-1 focal and intentionally kills
the process after the cap; no output image is an evidence dependency.

Every one of the 96 packets replays bit-for-bit under the exact float32
operation order:

| Focal | Zero denominator | Accepted fit | Rejected by unit guard |
|---|---:|---:|---:|
| 28mm | 7 | 10 | 7 |
| 35mm | 8 | 6 | 10 |
| 70mm | 12 | 5 | 7 |
| 150mm | 1 | 19 | 4 |
| **Total** | **28** | **40** | **28** |

Thus the corpus exercises all three material outcomes: denominator fallback,
accepted coupled refinement, and non-unit fit reset.

## Scope

- Formula: SHA-pinned installed code, body/focal independent for this IRAMP
  route.
- Runtime branch and bit replay: canonical Unit-1 `28/35/70/150mm`, 24
  packets per focal.
- Prior complete four-focal evidence supplies normal-render liveness through
  the refined tuple store; these focused captures terminate after the packet
  cap.
- No Unit-2 G-49 packet is claimed. The installed arithmetic has no public
  calibration/body input, so a second-body replay is not required to identify
  the formula; body-independent route compatibility remains a broader corpus
  question.

## Artifacts

- Probe: `tools/lldb_probes/g49_subpixel_refinement/subpixel_refinement_probe.py`
- Runner: `tools/lldb_probes/g49_subpixel_refinement/run_four_zoom.sh`
- Verifier: `tools/lldb_probes/g49_subpixel_refinement/verify_g49_subpixel_refinement.py`
- Reports: `runs/g49_subpixel_refinement/refinement_{28mm,35mm,70mm,150mm}.json`

## Verification

```bash
python3 tools/lldb_probes/g49_subpixel_refinement/verify_g49_subpixel_refinement.py
```

Expected terminal line:

```text
g49_subpixel_refinement=OK
```

## Rejected Upgrades

- This is not a pair of independent one-dimensional parabolic refinements.
- A non-positive preliminary determinant does not always reject; it zeros the
  cross term and recomputes the denominator.
- The unit guard does not clamp offsets to `[-1,1]`; it resets both to zero.
- Runtime packet values are observations, not constants.
- This does not close a later global contributor accept/suppress policy.
