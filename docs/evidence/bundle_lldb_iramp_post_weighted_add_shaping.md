# Bundle + LLDB IRAMP Post-Weighted-Add Shaping Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the immediate shaping stages after the post-reciprocal
weighted-add loop at `0x36aa30..0x36aa57`.

It proves:

- `0x36abf0..0x36ac15` applies a clamped vector update into the same destination
  buffer used by the weighted-add path
- the clamped update uses the formula
  `dest_after = weighted + dest_before + clamp((reference - dest_before) * scale * weighted_lane3, min, max)`
- the observed scale vector is `(2, 0, 0, 0)` and the clamp bounds are
  `(-0.1, -0.1, -0.1, -0.1)` to `(0.1, 0.1, 0.1, 0.1)`
- `0x36ad50..0x36adac` applies a fixed 3-vector linear transform to that shaped
  buffer and forces lane 3 to `1.0`
- the canonical four-zoom bridge HDR quartet all reach both shaping sites

It does not prove public names for the vectors, whether this transform is a
public color-space transform, complete downstream policy after the transform, or
final contributor acceptance / rejection.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_post_weighted_add_shaping/shaping_probe.py`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/clamp_first_28mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/clamp_first_35mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/clamp_first_70mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/clamp_first_150mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/transform_first_28mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/transform_first_35mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/transform_first_70mm.lldb`
- `tools/lldb_probes/iramp_post_weighted_add_shaping/transform_first_150mm.lldb`

Generated render outputs go under ignored
`runs/iramp_post_weighted_add_shaping/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Clamped Update

After the post-reciprocal weighted-add loop and clipping setup, the body enters
a vector update loop:

```asm
0x36abf0  movaps (%rdx), %xmm3
0x36abf3  movaps (%rax), %xmm4
0x36abf6  subps  %xmm4, %xmm3
0x36abf9  movaps (%rcx), %xmm5
0x36abfc  movaps %xmm5, %xmm6
0x36abff  shufps $0xff, %xmm6, %xmm6
0x36ac03  mulps  %xmm0, %xmm3
0x36ac06  mulps  %xmm6, %xmm3
0x36ac09  maxps  %xmm1, %xmm3
0x36ac0c  minps  %xmm2, %xmm3
0x36ac0f  addps  %xmm4, %xmm5
0x36ac12  addps  %xmm3, %xmm5
0x36ac15  movaps %xmm5, (%rax)
```

The constants immediately before the loop are loaded at:

```asm
0x36abca  movss  0x5a887c, %xmm0
0x36abd2  movaps 0x5fdbc0, %xmm1
0x36abd9  movaps 0x5cbf70, %xmm2
```

Static and runtime evidence together prove the first captured formula:

```text
raw_delta = (reference_vec4 - dest_vec4_before) * scale_vec * weighted_vec4[3]
clamped_delta = clamp(raw_delta, clamp_min, clamp_max)
dest_vec4_after = weighted_vec4 + dest_vec4_before + clamped_delta
```

Do not assign public semantic names to `reference_vec4`, `dest_vec4_before`, or
`weighted_vec4` here; these names describe only the instruction roles.

### Fixed 3-Vector Transform

After cleanup of the temporary descriptors, the body transforms the shaped
buffer in place. The tested bridge HDR quartet all take the even-width loop
body at `0x36ad50`:

```asm
0x36ad50  movaps -0x10(%rdi,%rbx), %xmm4
0x36ad55  movaps %xmm4, %xmm5
0x36ad58  shufps $0x0, %xmm5, %xmm5
0x36ad5c  mulps  %xmm0, %xmm5
0x36ad5f  movaps %xmm4, %xmm6
0x36ad62  shufps $0x55, %xmm6, %xmm6
0x36ad66  mulps  %xmm1, %xmm6
0x36ad69  addps  %xmm5, %xmm6
0x36ad6c  shufps $0xaa, %xmm4, %xmm4
0x36ad70  mulps  %xmm2, %xmm4
0x36ad73  addps  %xmm6, %xmm4
0x36ad76  blendps $0x8, %xmm3, %xmm4
0x36ad7c  movaps %xmm4, -0x10(%rdi,%rbx)
```

The duplicate second-vector body at `0x36ad81..0x36adac` has the same structure.

For this instruction window, the proven arithmetic is:

```text
out[i] = in[0] * row0[i] + in[1] * row1[i] + in[2] * row2[i]
out[3] = lane3_source[3]
```

## Runtime Proof

The LLDB probes stop independently at `0x36abf0` and `0x36ad50`.
The clamp and transform packets below are first-hit samples from separate
single-breakpoint runs; they prove liveness and instruction-window arithmetic,
not stable per-image constants.

### Clamp Packets

All four clamp packets observed:

- `scale_vec_xmm0 = (2.0, 0.0, 0.0, 0.0)`
- `clamp_min_xmm1 = (-0.100000001, -0.100000001, -0.100000001, -0.100000001)`
- `clamp_max_xmm2 = (0.100000001, 0.100000001, 0.100000001, 0.100000001)`

| Zoom | Raw delta | Clamped delta | Predicted destination after update |
|---|---|---|---|
| `28mm` | `(0.738088131, 0.0, -0.0, 0.0)` | `(0.100000001, 0.0, -0.0, 0.0)` | `(0.931812110, 0.006972316, -0.005407554, 1.694444656)` |
| `35mm` | `(0.003010839, 0.0, 0.0, 0.0)` | `(0.003010839, 0.0, 0.0, 0.0)` | `(0.116169531, -0.003146829, -0.001841841, 1.999999940)` |
| `70mm` | `(0.371722937, 0.0, -0.0, 0.0)` | `(0.100000001, 0.0, -0.0, 0.0)` | `(0.505958667, 0.008328820, -0.007252717, 1.694444418)` |
| `150mm` | `(-0.000399590, -0.0, -0.0, -0.0)` | `(-0.000399590, -0.0, -0.0, -0.0)` | `(1.305866841, -0.068151973, -0.003214966, 2.000001132)` |

### Transform Packets

All four transform packets observed the same row vectors and lane-3 source:

```text
row0 = (0.577350020, 0.577350020, 0.577350020, 0.0)
row1 = (0.707109988, 0.0, -0.707109988, 0.0)
row2 = (0.408250004, -0.816500008, 0.408250004, 0.0)
lane3_source = (0.0, 0.0, 0.0, 1.0)
```

| Zoom | Source before transform | Predicted vector after transform |
|---|---|---|
| `28mm` | `(0.931812108, 0.006972316, -0.005407554, 1.694444656)` | `(0.540704300, 0.542397007, 0.530843911, 1.0)` |
| `35mm` | `(0.116169527, -0.003146829, -0.001841841, 2.0)` | `(0.064093393, 0.068574342, 0.068543702, 1.0)` |
| `70mm` | `(0.505960524, 0.008329350, -0.007250806, 1.694444418)` | `(0.295045943, 0.298036602, 0.283266411, 1.0)` |
| `150mm` | `(1.305866838, -0.068151973, -0.003214966, 2.000001192)` | `(0.704438794, 0.756567265, 0.800820676, 1.0)` |

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- The post-reciprocal weighted-add output is followed by a clamped update loop
  at `0x36abf0..0x36ac15`.
- The clamped update adds the current destination vector, the weighted vector,
  and a bounded correction derived from `(reference - destination)`.
- The correction is scaled by the weighted vector's lane 3.
- In the first captured runtime packets, the correction scale vector is
  `(2, 0, 0, 0)`, so only lane 0 receives a nonzero correction.
- The clamped-update site is reached on `28mm`, `35mm`, `70mm`, and `150mm`.
- The shaped buffer is then transformed in place by a fixed 3-vector transform,
  with lane 3 replaced by `1.0`.
- The transform site is reached on `28mm`, `35mm`, `70mm`, and `150mm`.

## Not Proven Here

- Public semantic names for the three vector roles in the clamped update.
- Whether the fixed transform corresponds to a public color-space name.
- Whether first-hit numeric vectors are representative.
- Complete downstream policy after `0x36adac`.
- The complete candidate predicate.
- Final contributor acceptance / rejection or ghost-suppression policy.
