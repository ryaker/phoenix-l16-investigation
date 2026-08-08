# MonoFusion 5/3 Transform Edge and Packing Formula

**Date:** 2026-07-02  
**Claim:** `CLM-PREFUSION-002` addendum  
**Scope:** installed `libcp.dylib`; explicit canonical four-zoom route boundary

## Question

The normalized 5/3 lifting equations and installed forward/inverse bodies
were already pinned, but clean-room edge extension and coefficient packing
were left as prose gaps. This proof exhaustively identifies both.

## Reusable Exhaustive Probe

```text
tools/lldb_probes/prefusion_monofusion_worker/
  probe_transform_matrix.c
  run_transform_matrix.sh
  validate_transform_matrix.py
```

Run:

```bash
tools/lldb_probes/prefusion_monofusion_worker/run_transform_matrix.sh
```

The x86_64 harness invokes installed forward `0x1a28f0` and inverse
`0x1a2c10` on every one of the 256 basis vectors. It writes two 256x256
float32 matrices under ignored `runs/prefusion_monofusion_worker/`.

> **Corrective bit-order addendum (2026-08-08):** the matrix fit below
> established transform identity and boundaries but did not reproduce every
> word. Direct live-stage replay in
> `bundle_static_runtime_prefusion_monofusion_mode0_patch_terminal_exact_replay.md`
> proves the installed inverse executes row before column at the live
> stride-2 and stride-1 stages, with a fused coarse-lattice schedule. The
> older column-before-row pseudocode below is superseded for bit-exact work.

```text
forward SHA-256 d8eb695ea69277a83979a348aad7dccd5dfd070253d67fb2b519f2e921554693
inverse SHA-256 d83beb53f1f2d367782558b7d91ec1f992b3d19140bbd2037ababcc5bf0bde55
```

The prior verifier independently pins the installed function bodies and
constants. The matrix validator reproduces every output with direct
clean-room pseudocode:

```text
forward maximum absolute error = 2.980232238769531e-7
inverse maximum absolute error = 5.960464477539063e-8
```

## One-Dimensional Forward Step

For an even-length line `x`, split `e_i=x[2i]`, `o_i=x[2i+1]`.

```text
right_i = e_(i+1), except right_last = e_last
d_i = o_i/sqrt(2) - (e_i + right_i)/(2*sqrt(2))

left_i = d_(i-1), except left_0 = d_0
s_i = sqrt(2)*e_i + (left_i + d_i)/2
```

Store `s_i` at even positions and `d_i` at odd positions. Thus both
boundaries are symmetric replication: the last even sample supplies the
missing right predictor, and the first detail supplies the missing left
update.

## One-Dimensional Inverse Step

Read interleaved smooth/detail values:

```text
left_i = d_(i-1), except left_0 = d_0
e_i = s_i/sqrt(2) - (left_i + d_i)/(2*sqrt(2))

right_i = e_(i+1), except right_last = e_last
o_i = sqrt(2)*d_i + (e_i + right_i)/2
```

Store reconstructed `e_i,o_i` at even/odd positions.

## Two-Dimensional Lattice Order

Forward uses separable row then column lifting at progressively sparse
low-pass lattice strides:

```text
for stride in [1, 2, 4, 8]:
    indices = range(0, 16, stride)
    forward every indexed row over indexed columns
    forward every indexed column over indexed rows
```

Because each line stores smooth/detail at even/odd positions, recursion
naturally remains on the even-even lattice. No hidden terminal permutation
exists.

The algebraic matrix model used here reversed the separable schedule as:

```text
for stride in [8, 4, 2, 1]:
    indices = range(0, 16, stride)
    inverse every indexed column over indexed rows
    inverse every indexed row over indexed columns
```

This ordering is sufficient for the stated low-error matrix identity check,
but it is not the installed scalar execution order. The corrective direct
stage proof gives the bit-exact inverse as fused coarse lattice, then
stride-2 row/column, then stride-1 row/column.

## Four-Zoom Scope and Admission

Prior admitted route proof establishes that canonical Unit-1 `28mm` and
`35mm` use this exact mode-0 MonoFusion transform. Canonical `70mm` and
`150mm` construct no MonoFusion and use direct B4, so this transform is
explicitly absent at those tiers. Exact-focal Unit-2 wide runtime already
binds the same installed mode-0 worker; the transform itself is an installed
constant algorithm, not an LRI/body/firmware-derived parameter.

Admit the forward/inverse boundary extension, interleaved coefficient
packing, and recursive lattice schedule. Unobserved mode `1` and the outer
distributed selection/reduction and final contributor policy remain open.
