# Static/Runtime Evidence: Index-5 SGM Recurrence Roles

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B operational-role refinement  
**Bearing:** target-index-5 `StereoLayer<false>::runPass` recurrence

## Question

Earlier proofs named the index-5 worker's `Guidance`, `Pixel buf`,
`Min cost buf`, and `Line buf` storage and its installed `P1`, adaptive
`P2/P1`, and guide-decay controls. They still described the live recurrence
inputs as anonymous `src0`, `src6`, `accum`, `bias2`, and `cap`.

This proof asks whether those are unresolved public calibration inputs or
generated SGM working terms with concrete operational roles.

## Artifacts

- Reusable static/reused-runtime verifier:
  `tools/lldb_probes/index5_sgm_recurrence_roles/verify_sgm_recurrence_roles.py`
- Reused complete four-focal reports:
  `runs/codex_276860_payload_vector_formula/vector_formula_*.json`
- Reused accepted four-focal term packets:
  `runs/codex_276860_xmm3_term_step/xmm3_term_step_*.json`
- Adjacent source proofs:
  `bundle_static_runtime_index5_cost_operand_names_four_zoom.md` and
  `bundle_static_runtime_index5_sgm_parameter_origins_four_zoom.md`

No new LLDB render was needed.

## Static Storage Layout

The verifier SHA-pins the allocator, local-cost helper, and recurrence
windows. `0x26c8e0` creates the three named scratch buffers:

| Storage | Verified layout |
|---|---|
| `Line buf` | two contiguous halves; all sampled predecessor reads and current-path stores fall inside the allocation |
| `Min cost buf` | two halves of `4 * expanded_width` `uint16` values; one half supplies the prior minimum and the other receives the current minimum |
| `Pixel buf` | two contiguous guide-vector halves used by the already-proven adaptive-penalty calculation |

`0x276b72..0x276b93` also allocates a 64-byte-aligned
`2 * hypothesis_count` byte temporary. The direct path at
`0x277270..0x27738e` expands Cost-volume payload bytes into this `uint16`
local-cost vector; the sibling `0x2730c0` / `0x2732f0` paths generate the
same temporary through the local matching-cost helpers.

## Recurrence Names

The pinned `0x27786b..0x277a3d` dataflow gives these exact operational roles:

| Earlier symbol | Admitted role |
|---|---|
| `src0`, `src6`, and their lane blend | predecessor directional path-cost candidates read from `Line buf` |
| `bias1` / `%xmm1` | installed adjacent-hypothesis penalty `P1` |
| `bias2` / `%xmm2` | prior directional minimum read from `Min cost buf`; the normalization baseline |
| `cap` / `%xmm3` | `Min cost buf` baseline plus guide-adaptive `P2` |
| `accum` / `[r10 + 2*rdx]` | per-pixel local matching-cost temporary |
| `[rcx + 2*rdx]` | current directional path-cost output in `Line buf` |
| `[r9 + 2*rdx]` | saturating accumulation into the per-pixel `Cost volume` payload |
| `phminposuw` result | current directional minimum stored to the other `Min cost buf` half |

In operational SGM notation, the selected term is:

```text
path_cost(p, d) =
  local_cost(p, d)
  + min(
      predecessor same/adjacent-hypothesis candidates with P1,
      min_predecessor + adaptive_P2
    )
  - min_predecessor
```

The exact SIMD lane-splice formula remains the one validated in
`lldb_276860_payload_vector_formula_four_zoom.md`. This note names its
storage and recurrence roles; it does not replace that byte-level formula
with an unverified disparity-direction convention.

## Runtime Join

Each accepted term packet independently proves:

```text
xmm2 = broadcast(Min cost buf baseline)
xmm3 = broadcast(Min cost buf baseline + adaptive P2)
```

| Tier | Baseline | Adaptive `P2` | Cap |
|---|---:|---:|---:|
| `28mm` | `240` | `499` | `739` |
| `35mm` | `199` | `479` | `678` |
| `70mm` | `229` | `414` | `643` |
| `150mm` | `185` | `469` | `654` |

These are one sampled packet per focal tier, not stable image constants.

Across `67` accepted vector samples, the verifier bounds every predecessor
read and current-path store to `Line buf`, every local-cost read to the
hypothesis-count-sized temporary, and every existing vector-formula and
payload-custody invariant. Every focal tier also contains at least one
initial-direction sample where the local-cost temporary equals the
pre-update Cost-volume payload.

## Verification

```text
static_index5_sgm_recurrence_roles=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
28mm: OK baseline=240 adaptive_P2=499 cap=739 vector_samples=16 initial_local_cost_matches=2
35mm: OK baseline=199 adaptive_P2=479 cap=678 vector_samples=20 initial_local_cost_matches=1
70mm: OK baseline=229 adaptive_P2=414 cap=643 vector_samples=15 initial_local_cost_matches=1
150mm: OK baseline=185 adaptive_P2=469 cap=654 vector_samples=16 initial_local_cost_matches=1
roles=Line_buf_predecessor_candidates+P1; cap=Min_cost_buf_baseline+adaptive_P2; local_cost=temp; output=Line_buf+Cost_volume+Min_cost_buf
index5_sgm_recurrence_roles=OK
```

## Admission and Remaining Boundary

Admitted:

- complete operational roles for the sampled recurrence sources, temporary,
  normalization baseline, adaptive cap, and generated outputs;
- their exact generated `Line buf`, `Min cost buf`, local temporary, and
  Cost-volume storage custody; and
- proof that the baseline and cap are live SGM terms, not additional public
  LRI/calibration parameters.

Still open:

- public names for key-`0` Guidance components `C0..C2`;
- universal all-pixel/focal/body proof for `C3=1`;
- stable full-map Cost-volume distributions;
- exact semantic identities for every selector bank and the whole State;
- final source contribution and acceptance/rejection.

The recurrence has no additional direct public calibration/LRI origin beyond
the already-proven tier-anchor Guidance and calibrated camera-model products.
Its remaining terms are generated algorithm state.
