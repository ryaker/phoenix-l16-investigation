# Static and Runtime Proof: CNR Matrix Helper SVD Equivalent

## Scope

This bundle closes the `0x309270 -> 0x309d50` matrix-helper gap for the live
`ColorNoiseReduction` worker admitted by
`bundle_static_runtime_cnr_worker_formula_four_zoom_two_body.md`.

Coverage is Unit-1 canonical profile-3 bridge-HDR `28mm`, `35mm`, `70mm`, and
`150mm`, plus exact-35mm Unit-2. This proves an independently specified
equivalent for the helper on the live CNR path; it does not classify the
Unit-2 exact-35mm `0x2fd070` sibling-arm selector. The later
`bundle_static_runtime_denoise_selector_2fd070_two_body.md` proof closes that
selector-cause gap only.

## Artifacts

Reusable verifier:

- `tools/lldb_probes/denoise_route_census/verify_cnr_matrix_helper_svd.py`

Runtime inputs reused from the formula proof:

- `runs/denoise_route_census/unit1_28mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_35mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_70mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_150mm_cnr_formula.json`
- `runs/denoise_route_census/unit2_35mm_cnr_formula.json`

Verifier output:

- `runs/denoise_route_census/cnr_matrix_helper_svd.json`

Verifier result:

```text
cnr_matrix_helper_svd=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 samples=18 max_recon_abs=2.79e-09 max_singular_abs=1.86e-09 max_asym=0.125
```

## Static Proof

The verifier reuses `inspect_cnr_static.py` and pins the installed
`libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It verifies the already admitted helper ranges:

| Body | Range | SHA-256 |
|---|---:|---|
| Matrix helper | `0x309270..0x309d50` | `8c00b98db2d08556b0e0a895ab62dee34c0742f33a76aec542f982232fe39277` |
| Rotation helper range | `0x309d50..0x30a050` | `639f9a91a700f7b4df6b26d373da25ebf471cfbf8bd6252ad7123b2a46b78415` |

It also verifies:

- the CNR worker callsite `0x3088a8 -> 0x309270`;
- the helper-internal callsite `0x30960e -> 0x309d50`;
- the live caller mode immediate `0x14`;
- the helper sweep epsilon constant `4.440892098500626e-16`;
- the `DBL_MIN` guard constant; and
- the double absolute-value mask `0x7fffffffffffffff` in both SIMD lanes.

Mode `0x14` sets the two matrix-output families used by this CNR path. The
worker passes a 3x3 double matrix generated from the normalized RGB
second-moment matrix and receives two 3x3 double blocks plus three scalar
values.

## Equivalent Formula

For the admitted live CNR mode, `0x309270 -> 0x309d50` is equivalent to a
3x3 two-sided singular value decomposition of the input matrix `M`.

Let the helper output object contain:

```text
A = object[0x00..0x40]  as a row-major 3x3 double matrix
B = object[0x48..0x88]  as a row-major 3x3 double matrix
S = object[0x90..0xa0]  as three double singular values
```

The verified convention is:

```text
M = transpose(B) * diag(S) * A
```

The two output blocks are orthonormal and the singular values are
nonnegative, sorted in descending order. On exactly symmetric inputs the two
blocks collapse to the same eigenvector basis up to sign; on slightly
asymmetric captured inputs, the two-sided SVD form is required. The largest
captured input asymmetry is `0.125`, from a matrix whose largest absolute
entry is over two million.

The CNR caller then uses the first block and the singular values as the
basis for its downstream Wiener-style row transform. This evidence closes the
helper itself as an SVD equivalent; the caller-side final store formula is
covered by `bundle_static_runtime_cnr_worker_formula_four_zoom_two_body.md`.

## Runtime Coverage

| Sample set | Helper samples | Max reconstruction abs error | Max input asymmetry | First captured singular values |
|---|---:|---:|---:|---|
| Unit-1 `28mm` | `4` | `4.66e-10` | `0.125` | `[866108.527378043, 77.11748604471127, 3.3238859125163773]` |
| Unit-1 `35mm` | `4` | `6.40e-10` | `0.001953125` | `[77861.99984629331, 1069.3740936527302, 6.538169429747315]` |
| Unit-1 `70mm` | `3` | `3.49e-10` | `0.0625` | `[373800.88497999025, 568.707014096468, 37.908005926020174]` |
| Unit-1 `150mm` | `4` | `2.79e-09` | `0.125` | `[4668499.684817259, 17.09938027058894, 1.0910000567969755]` |
| Unit-2 exact `35mm` | `3` | `1.46e-10` | `0.00390625` | `[202324.03390619272, 439.62646920070455, 132.84353085661016]` |

Across all 18 helper samples:

| Metric | Maximum |
|---|---:|
| `B.T * diag(S) * A` reconstruction abs error | `2.7939677238464355e-09` |
| Reconstruction relative error | `1.5634297163894739e-15` |
| Orthonormality abs error | `8.881784197001252e-16` |
| Independent `numpy.linalg.svd` singular-value abs error | `1.862645149230957e-09` |
| Captured input asymmetry | `0.125` |

## Admission

This is a `CLM-DENOISE-002` partial-strengthening:

- admitted: the live CNR matrix helper at mode `0x14` is a 3x3 two-sided SVD
  equivalent with convention `M = B.T * diag(S) * A`;
- admitted: Unit-1 `28/35/70/150mm` and exact-35mm Unit-2 helper outputs
  satisfy that SVD convention at runtime;
- admitted: the previous "matrix helper internals/equivalent" gap is closed
  for this live CNR path;
- superseded by later proof: selector cause for the Unit-2 exact-35mm extra
  `0x2fd070` denoise sibling arm.
