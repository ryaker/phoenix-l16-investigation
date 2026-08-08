# Static/Runtime Evidence: IRAMP Operand Roles and Score Consequence

**Date:** 2026-07-02  
**Status:** VERIFIED; admitted as bounded `CLM-PREFUSION-002` / `CLM-MERGE-005` progress  
**Scope:** installed bundle and canonical Unit-1 `28mm`, `35mm`, `70mm`, `150mm`

## Question

IRAMP is already proven to receive `src1`, `src2`, five direct contributors,
five paired warp records, scale, and ROI. This proof asks what distinct roles
those image operands play inside `0x3661b0`, and whether the
reference/candidate comparison affects pixel contribution.

## Reusable Verifier

`tools/lldb_probes/iramp_operand_role_custody/verify_iramp_operand_roles.py`

The verifier SHA-pins ten installed windows spanning:

- closure loads and image generation;
- direct-source and paired-warp selection;
- `src1` guide-patch reads;
- `src2` reference-patch preparation;
- direct-candidate comparison;
- tuple-score consumption; and
- normalized weighted accumulation.

It separately checks every direct-call target and the exact operand-custody
instructions.

## Installed Operand Custody

### `src1`: coarse registration guide

`0x36656b` loads closure `+0x08` and `0x3665d5 -> 0x374ac0` renders `src1`
into the local `vec4` image at `rbp-0x1600`.

That image then takes this distinct path:

1. `0x3666ba -> 0x374870` derives a three-float transform/statistics packet.
2. `0x366826 -> 0x36fba0` materializes the byte-domain guide at
   `rbp-0x1790`.
3. `0x3691b2..0x3692a9` copies the current 16-row guide neighborhood from
   descriptor data `rbp-0x1770` into `rbp-0x1b40`.
4. The admitted coarse search at `0x369490..0x369558` compares each direct
   partner's byte patch against that guide with SIMD SAD and WTA.

The same `src1` pointer is also loaded at `0x366b18` for dimensions used by
the per-source warp-grid bounds at `0x366c70..0x366d59`.

Thus `src1` is not a pixel candidate in the later partner loop. It supplies
the coarse registration/guide domain and its coordinate bounds.

### `src2`: full-vector reference patch

`0x366915` loads closure `+0x10`, and `0x36695a -> 0x374ac0` renders `src2`
into the local `vec4` image at `rbp-0x17d0`.

For every output-grid point:

1. `0x3692b8` passes that exact descriptor as `rsi` to
   `0x3692c6 -> 0x36b920`.
2. `0x36b920` copies the selected 16x16 `vec4` neighborhood and prepares the
   reference scratch rooted at `rbp-0x4240`.
3. The same scratch pointer is later passed as the first patch argument to
   `0x369e3f -> 0x36cde0`.

Thus `src2` supplies the full-vector reference patch used by the
reference/candidate comparison and baseline reduction preparation.

### `srcs[i] + warps[i]`: warped direct candidates

`0x366a50` reads the direct-source vector at closure `+0x18`;
`0x366b1c` reads the paired warp vector at closure `+0x20`. The common loop
index selects one 16-byte source item and one `0x50` warp record.

For each item:

1. `0x366e5d..0x366e76` selects `srcs[i]`.
2. `0x366f1c -> 0x374ac0` renders that direct contributor.
3. The matching warp fields create its transformed pair grid and source
   record.
4. The record stores both a byte-domain search representation and full
   `vec4` image data.
5. For a valid non-sentinel partner, the admitted bilinear path writes a
   16x16 warped candidate patch at `rbp-0x11a0`.
6. `0x369e38` passes that candidate as the second patch argument to
   `0x36cde0`.

Therefore the five direct contributors are candidate patches, paired
one-to-one with their five warp records.

## Comparison and Contribution Consequence

The comparison call is exactly:

```text
t = 0x36cde0(
  reference_patch = scratch_from_src2,
  candidate_patch = warped_srcs_i_patch
)
```

Prior admitted proof establishes that `0x36cde0` traverses both 16x16 `vec4`
patches, computes normalized sums, square sums, cross products,
variance/covariance-like terms, transform reductions, and returns
`sqrt(a*b)`. The return is stored as tuple field 3 at `0x369e91`.

That field is subsequently read at `0x36a7d8`. For `t`, the installed body
forms:

```text
candidate_multiplier = (t + 2*max(0, t - 0.5), t, t, t)
```

The candidate patch is multiplied by this vector and accumulated. The running
normalization denominator starts at `0.2`, adds each non-sentinel `t`, and is
reciprocated. The normalized candidate result is then added through the
separable spatial-weight product. Consequently, the comparison scalar has a
direct pixel-contribution effect; it is not debug-only metadata.

This proof does not rename `t` as a public field or claim it is a binary
accept/reject bit. Sentinel entries are skipped, while valid entries have a
continuous multiplier that can be zero.

## Four-Zoom Runtime Join

The following admitted complete-render evidence supplies four-focal liveness
for the SHA-pinned static edges:

- `lldb_iramp_terminal_consolidation_four_zoom.md`:
  entry, inner closure, sentinel compare, score multiply, tuple store,
  reciprocal, weighted store;
- `bundle_lldb_iramp_refined_tuple_four_zoom.md`:
  non-empty partner path, warped candidate patch, `0x36cde0`, tuple write;
- `bundle_lldb_iramp_tuple_downstream_consumer.md`:
  tuple score read and multiplier/add loop; and
- `bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`:
  normalization and post-reciprocal weighted add.

All four canonical Unit-1 bridge HDR renders complete and write HDR under
those probes. Static operand custody is invariant in the installed binary;
runtime packets cover `28mm`, `35mm`, `70mm`, and `150mm`.

The canonical quartet is one physical calibration body. Numerical
differences among captures are not attributed to body or firmware. This proof
concerns installed control/data custody, not a body-dependent parameter
comparison.

## Verification Output

```text
iramp_operand_roles_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
src1=coarse_registration_guide
src2=vec4_reference_patch
srcs[i]+warps[i]=warped_direct_candidate_patch
comparison=reference_candidate_patch_score
score_consequence=tuple_multiplier_normalized_weighted_add
iramp_operand_roles=OK
```

## Admission Boundary

Admitted:

- `src1` is the coarse registration/guide operand;
- `src2` is the full-vector reference/baseline patch operand;
- `srcs[i] + warps[i]` supplies each warped direct candidate;
- `0x36cde0` compares the `src2` reference patch with that candidate; and
- its tuple scalar directly controls normalized weighted pixel contribution.

Still open:

- a complete clean-room expansion of every `0x36cde0` transform/reduction
  stage;
- a complete clean-room expansion of `0x36e530` selector/normalization
  preparation;
- the exhaustive sentinel/continuous-score policy for every candidate; and
- the final global acceptance/rejection claim outside this bounded IRAMP
  path.

`CLM-PREFUSION-002` and `CLM-MERGE-005` remain blockers, but the old
"unknown src1/src2 meaning" boundary is superseded by these concrete roles.
