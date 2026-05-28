# LLDB Evidence: C6/Post-Mutation ImagePyramid Downstream Candidate Liveness

**Date:** 2026-05-28
**Status:** admitted negative-scope evidence for `CLM-C6-001`
**Scope:** canonical bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This probe tests whether selected static downstream users of `context+0x538`
execute after the already proven C6/post-mutation ImagePyramid zero-fill route.

The question is deliberately narrow:

- Does the same bridge-HDR render hit the proven zero-fill checkpoint?
- Do any of the selected later static candidate sites that wrap/read
  `context+0x538` also execute in that render?

This is not a terminality proof. Zero hits at the selected candidate sites do
not prove that no later reader or writer exists outside the probed set.

## Tested LRIs

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Probe Artifacts

Reusable probe harness:

- `tools/lldb_probes/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_probe.py`
- `tools/lldb_probes/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_28mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_35mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_70mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_150mm.lldb`

Ignored raw outputs:

- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_28mm.json`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_35mm.json`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_70mm.json`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_150mm.json`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_28mm.log`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_35mm.log`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_70mm_retry.log`
- `runs/c6_image_pyramid_downstream_liveness/c6_image_pyramid_downstream_liveness_150mm.log`

The first `70mm` attempt wrote a partial JSON after `EXC_BAD_ACCESS`; it is not
used as evidence. The cited `70mm_retry.log` records a complete render and
writes the final cited `70mm` JSON.

## Static Candidate Boundary

Repo-local static inspection identified these later `context+0x538` candidate
families and call surfaces:

| Family | Runtime sites probed | Static role under test |
|---|---|---|
| Zero-fill checkpoint | `0x3b2abd`, `0x3b2f59` | same-render control sites proving the known route fired |
| Histogram-like last-level consumer | `0x3b7470`, `0x3b7490`, `0x3b74e0`, `0x3b7546` | wraps `context+0x538`, indexes last ImagePyramid level, reads image data, and branches by `0x3c6450(ctx, 10)` |
| Last-level materializer | `0x3b77b0`, `0x3b7839`, `0x3b78c5`, `0x3b7919`, `0x3b7988`, `0x3b79be`, `0x3b79d6`, `0x3b7ab4` | scans/updates last-level mask state, wraps `context+0x538`, and can call `0x27e0d0` or `0xf540` |
| Region/deeper-level consumer | `0x3b9820`, `0x3b9846`, `0x3b988f`, `0x3b9c46`, `0x3b9c51`, `0x3b9c82`, `0x3b9f0c`, `0x3b9f89` | wraps `context+0x538`, reads indexed/deeper levels, can call `0xd7a10`, and can call a `context+0x5a0` virtual |
| Direct first-image descriptor path | `0x3bdd9b`, `0x3bddd3`, `0x3bde8d` | reads `context+0x538` directly, forms a descriptor from the first image, and can call `0xf540` |
| Virtual consumer path | `0x3bf3b3`, `0x3bf419` | wraps `context+0x538` and can call a `context+0x5a0` virtual |

## Runtime Hit Summary

Every cited final run completed the bridge HDR render and wrote the JSON report.
Every JSON reports zero LLDB callback errors.

| Site / group | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---:|---:|---:|---:|
| `0x3b2abd` zero-fill route `context+0x538` store | 1 | 1 | 1 | 1 |
| `0x3b2f59` after zero-fill callsite | 5 | 5 | 5 | 5 |
| selected downstream candidate sites listed above | 0 | 0 | 0 | 0 |

For all four runs:

- `derived_summary.zero_fill_hit_sites = ["0x3b2abd", "0x3b2f59"]`
- `derived_summary.downstream_hit_sites = []`
- `derived_summary.contexts_with_both_zero_fill_and_downstream_site_hits = []`
- after-return first-32-byte samples at `0x3b2f59` are zero for all five level descriptors

## Proven Facts

- The proven ImagePyramid zero-fill route fired in all four canonical bridge HDR runs under this probe.
- The after-zero-fill checkpoint `0x3b2f59` fired exactly five times in each run, matching the five ImagePyramid levels.
- None of the selected later static `context+0x538` candidate sites fired in the completed `28mm`, `35mm`, `70mm`, or `150mm` runs.
- Therefore, the selected static candidate families in this probe are excluded as live downstream consumers of the zero-filled ImagePyramid route under the canonical bridge HDR quartet.

## Non-Conclusions

- This does not prove the zero-filled ImagePyramid/geometry route is terminal.
- This does not prove there are no later reads or writes through unprobed generic helpers, indirect callers, callbacks, or data-pointer aliases.
- This does not prove C6 contributes to the final rendered image.
- This does not prove C6 is globally unused or globally excluded.
- This does not prove absence of non-focused `0xf2720` routes or non-`0xf2720` routes.
- This does not close final merge acceptance/rejection or ghost-free parity math.

## Next Evidence Path

The next stronger terminality test is data-driven rather than callgraph-driven:
install hardware read/write watchpoints on representative zero-filled
ImagePyramid backing buffers after `0x3b2f59`, then let the render continue.
That can prove whether the actual buffer storage is touched later, independent
of which static function name or call surface performs the access.
