# LLDB IRAMP W5 Magnitude Reproduction Evidence

**Date:** 2026-06-05
**Status:** Runtime evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local `lri_process`, and the
canonical four-zoom bridge HDR quartet with `--no-auto-lris`.

This document independently reproduces the useful part of Opus's W5 magnitude
method: LLDB core-handled ignore-count / conditional breakpoints can stop at
mid-render arithmetic sites without Python per-hit callbacks, and the live
registers show non-degenerate score values plus non-common reciprocal
denominators inside the terminal IRAMP path.

It does not assert Opus's exact sampled numbers as universal values. Several
Codex samples intentionally differ from Opus's table because they are different
first matching hits under LLDB scheduling / condition choice. The admitted fact
is the runtime arithmetic and representative non-degenerate magnitudes, not a
per-pixel distribution or an algorithm constant.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harness:

- `tools/lldb_probes/codex_opus_w5_magnitude_repro/magnitude_dump.py`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_28mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_35mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_70mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_150mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_nonzero_35mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/score_nonzero_70mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/sigma_28mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/sigma_35mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/sigma_70mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/sigma_150mm.lldb`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/run_four_zoom.sh`
- `tools/lldb_probes/codex_opus_w5_magnitude_repro/run_nonzero_scores.sh`

Generated raw reports and LLDB logs live under ignored local directory:

- `runs/codex_opus_w5_magnitude_repro/`

No live `/tmp` or `/private/tmp` artifact is cited by this evidence.

Python was used only after LLDB had already stopped at a core-handled
breakpoint, to read registers and write JSON. It was not installed as a per-hit
breakpoint callback.

## Static Arithmetic Sites

Score return site:

```asm
0x36e511  mulss  %xmm1, %xmm0
0x36e515  sqrtss %xmm0, %xmm0
0x36e528  retq
```

Reciprocal normalizer site:

```asm
0x36a934  shufps $0x0, %xmm2, %xmm2
0x36a938  rcpss  %xmm2, %xmm2
0x36a93c  movaps %xmm2, -0x42f0(%rbp)
```

## Runtime Score Captures

The score captures stop before `0x36e511`, record `xmm0` and `xmm1`, single-step
`mulss`, record the product, single-step `sqrtss`, and record the returned
score.

| Zoom | Capture | Factor `xmm0` | Factor `xmm1` | Product after `mulss` | Score after `sqrtss` |
|---|---|---:|---:|---:|---:|
| `28mm` | `score_28mm` (`-i 8000`) | `0.845083833` | `1.000000000` | `0.845083833` | `0.919284403` |
| `35mm` | `score_nonzero_35mm` (condition `xmm0 != 0 && xmm1 != 0`) | `0.283306062` | `0.843024850` | `0.238834053` | `0.488706499` |
| `70mm` | `score_nonzero_70mm` (condition `xmm0 != 0 && xmm1 != 0`) | `0.660202682` | `0.800213039` | `0.528302789` | `0.726844430` |
| `150mm` | `score_150mm` (`-i 2000`, same nonzero condition) | `0.941425800` | `1.000000000` | `0.941425800` | `0.970270991` |

Arithmetic check:

- For every row, the post-`sqrtss` value matches `sqrt(factor0 * factor1)`
  within normal float precision.
- The captured nonzero rows prove representative non-degenerate score values
  on all four canonical focal tiers.

False-start note:

- Fixed ignore-count captures `score_35mm` (`-i 2000`) and `score_70mm`
  (`-i 2000`) landed on real zero-factor packets in this Codex run. Those
  packets are preserved in `runs/codex_opus_w5_magnitude_repro/`, but they are
  not used as non-degenerate magnitude evidence.

## Runtime Reciprocal / Denominator Captures

The reciprocal captures use a conditional breakpoint at `0x36a938`:

```text
(*(int*)&$xmm2) != 0x3e4ccccd
```

This excludes the common `0.200000003` denominator observed in first-hit
captures, then stops before `rcpss`. The probe records `xmm2`, single-steps the
`rcpss`, and records the reciprocal approximation.

| Zoom | `xmm2` before `rcpss` | Exact `1/xmm2` | `xmm2` after `rcpss` | Relative error |
|---|---:|---:|---:|---:|
| `28mm` | `0.399711609` | `2.501803745` | `2.501953125` | `5.971e-05` |
| `35mm` | `1.023340702` | `0.977191661` | `0.977294922` | `1.057e-04` |
| `70mm` | `0.902118564` | `1.108501743` | `1.108398438` | `9.319e-05` |
| `150mm` | `1.149109244` | `0.870239279` | `0.870239258` | `2.406e-08` |

Accepted conclusions:

- `0x36a938` is reached with non-common denominator values on all four
  canonical focal tiers under the tested conditions.
- The instruction computes the expected approximate reciprocal of that
  denominator.
- The observed denominator is not always the common first-hit `0.200000003`.

## Relationship To Opus W5

Reproduced:

- LLDB ignore-count and conditional breakpoints are practical under Rosetta for
  these mid-render sites.
- The score return chain is live and produces nonzero representative values on
  all four focal tiers.
- The reciprocal normalizer is live and receives non-common denominator values
  on all four focal tiers.

Not reproduced as exact constants:

- Codex did not reproduce Opus's exact per-tier W5 score and denominator sample
  table. The captured values are valid runtime samples from the same arithmetic
  sites, but they are not the same hit windows.
- Therefore, Opus's specific numeric table remains a quarantined sample table
  unless a later Codex harness is designed to reproduce those exact hit
  windows. The arithmetic mechanism, not the exact Opus sample rows, is the
  admitted fact here.

## Non-Claims

- This is not a full per-pixel or per-tile distribution.
- This does not prove the complete `0x3661b0` reducer algorithm.
- This does not assign public semantic names to `xmm2`, tuple fields, channels,
  or weights.
- This does not prove Lumen-quality merge parity or final anti-ghosting policy.
