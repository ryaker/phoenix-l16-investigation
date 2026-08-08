# Static/Runtime Evidence: Index-5 Skip-Mask Population Policy

**Date:** 2026-07-10  
**Status:** VERIFIED; admitted `CLM-STEREO-001` refinement  
**Bearing:** selected target-index-5 `StereoLayer<false>+0x208` `Skip mask`

## Question

The index-5 cost path already names `StereoLayer+0x208` as `Skip mask` and
proves that it helps size the generated per-pixel Cost-volume records. The
remaining clean-room gap was the predicate that populates the mask.

This proof asks which installed sampling-pattern arm is selected at index 5,
how that arm writes the mask, and whether an independent implementation can
reproduce the complete selected masks at all four canonical focal tiers.

## Artifacts

- live builder-receipt probe:
  `tools/lldb_probes/stereolayer_depth_writer/stereolayer_depth_writer_probe.py`
- reusable task-rectangle probe:
  `tools/lldb_probes/index5_stereo_residual_policy/skip_mask_task_probe.py`
- LLDB command file:
  `tools/lldb_probes/index5_stereo_residual_policy/skip_mask_tasks_28mm.lldb`
- static/runtime/replay verifier:
  `tools/lldb_probes/index5_stereo_residual_policy/verify_skip_mask_policy.py`
- fresh complete-render receipt:
  `runs/stereolayer_depth_writer/depth_writer_28mm.json`
- fresh bounded task capture:
  `runs/index5_stereo_residual_policy/skip_mask_tasks_28mm.json`
- reused complete four-focal mask dumps:
  `runs/codex_29a140_source_local_producer/source_local_*_full_mask_descriptor.bin`

The verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and the exact dispatcher, setter, pattern-2 builder, MT19937 worker, and
uniform-integer helper body ranges.

## Installed Dispatch

`0x26db40` reads `StereoLayer+0x50` and dispatches through the four-entry
jump table at `0x26dd24`:

| Pattern | Target | Bounded behavior |
|---:|---:|---|
| `0` | `0x26dc8a` | zero-fill output |
| `1` | `0x26db73 -> 0x28fa70` | separate step-2 arm |
| `2` | `0x26db8f -> 0x28fba0` | selected randomized step-2 arm |
| `3` | `0x26dbab` | separate image-derived arm |

The pattern-2 builder fills the destination with `0xff`, sets executor task
size to `64 x 64`, and dispatches worker `0x28fed0` with step `2`.

## Direct Runtime Receipt

A fresh Unit-1 `28mm` complete render reaches `0x26db40` eleven times:

| Layer index | Dimensions | `sampling_pattern` | Calls |
|---:|---:|---:|---:|
| `0` | `65 x 49` | `0` | `1` |
| `1` | `130 x 98` | `0` | `2` |
| `2` | `260 x 195` | `0` | `2` |
| `3` | `520 x 390` | `0` | `2` |
| `4` | `1040 x 780` | `2` | `2` |
| `5` | `2080 x 1560` | `2` | `2` |

The index-5 receipt therefore directly selects installed pattern `2`; it is
not inferred from the output distribution.

The focused worker capture records exactly `768` distinct index-5 tasks,
all with step `2` and one destination descriptor. The task grid is 32 columns
by 24 rows. Interior tasks are `64 x 64`; the final x tile is
`[1984,2080)` and the final y tile is `[1472,1560)`.

## Exact Population Formula

Each worker task constructs a fresh standard `std::mt19937` state with seed
`5489`. For each 2x2 cell whose upper-left coordinate lies in that task:

```text
dx = mt19937() & 1
dy = mt19937() & 1
mask[y + dy][x + dx] = 0
```

The other three bytes retain the builder's initial `0xff`. Because each task
restarts the engine, tile boundaries are part of the exact policy. The two
draws are the installed uniform-integer `[0,1]` route; the verifier also pins
both calls and the zero-byte store.

For `2080 x 1560`, the result contains exactly:

- `811,200` zero bytes, one for every 2x2 cell;
- `2,433,600` `0xff` bytes; and
- SHA-256
  `1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba`.

## Four-Focal Replay

The independent generator reproduces every byte of the previously captured
full index-5 masks:

```text
28mm=OK bytes=3244800 sha256=1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba
35mm=OK bytes=3244800 sha256=1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba
70mm=OK bytes=3244800 sha256=1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba
150mm=OK bytes=3244800 sha256=1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba
index5_skip_mask_policy=OK pattern=2 step=2 tasks=768 tile=64x64 seed=5489 zeros=811200 nonzero=2433600
```

## Admission and Scope

Admitted for canonical Unit-1 profile-3 bridge HDR:

- target index 5 selects `sampling_pattern = 2`;
- the exact pattern-2 byte-population formula, RNG, seed, task tiling, and
  edge tiles are clean-room reproducible; and
- complete captured masks are byte-identical at `28mm`, `35mm`, `70mm`, and
  `150mm`.

The direct field/pattern receipt and task capture are Unit-1 `28mm`; the
complete generated-mask equality is Unit-1 four-focal. Installed static proof
is body-independent for this pinned bundle, but no Unit-2 runtime receipt was
run, and patterns `1` and `3` are not generalized. This evidence states the
literal `0` / `0xff` policy and does not invent public accept/reject names for
those byte values.

`CLM-STEREO-001` remains `PARTIAL` / `BLOCKER` for exact Guidance
component semantics and the disparity-direction lane convention.
