# Stage-A Boundary Closure: Guidance Photometry Ported; Residual Is CLM-PREFUSION-002 Geometry

**Date:** 2026-08-10
**Bearing:** deterministic u2_70 level-0 boundary comparison, stage A (guidance +
source planes) first-divergent finding.

## What was asked

Partition the stage-A plane divergence (Phoenix `PHX_DUMPSRC` collapse planes
vs Lumen `u2_70_executor_serial_r1/image0..4.rgba8`) into photometry vs
geometry, then port the divergent proven behavior -- NOT tune toward the diff.

## Method (code-vs-spec, then one partitioning measurement)

1. Read Phoenix `computeGuidanceYUVFloat` / `buildGuidanceYUVMatrix` /
   `guidanceSignPow` against the PROVEN `bundle_static_runtime_index5_guidance_
   yuv_formula_two_body.md`. Every element matches bit-for-bit:
   - input normalization `(raw-42)/981` (proven Bayer-norm scale `1/f32(1023-42)`);
   - collapse2 `[R, f32(0.5*G1+0.5*G2), B, 1]`;
   - sensor response `w = [0.2155500054359436, 0.43230700492858887,
     0.35214298963546753]`; neutral `p = 1/awb_gains.{r,g_r,b}`;
   - matrix construction (`S,nb,q,y1,m,x1,z1,x2,z2,nw,s1,s2`) identical;
   - signed fast-pow to `1/2.2` with pinned constants (`0.204204366`,
     `-1.25254691`, `3.33102155`, `-2.28267884`; exp `0.454545438`; exp-poly
     `0.0780245215`, `0.226067156`, `0.695833564`, `0.999925196`; scale `255`);
   - offset `[0,128,128,0]`; `C3 = 1` (already ported: `packYUVFloatToU8`
     writes byte 1, not 255).
   => Guidance YUV photometry is a VERIFIED bit-exact port. No divergence.

2. Partition measurement -- per-channel affine of Lumen image0 vs Phoenix,
   sampled every 37th pixel, envelope rectification ON vs OFF:

   | Channel | ENV ON slope/corr | ENV OFF slope/corr |
   |---|---|---|
   | R (Y) | 0.903 / **0.974** | -0.110 / -0.228 |
   | G (U) | 0.385 / 0.566 | 0.063 / 0.112 |
   | B (V) | 0.624 / 0.806 | -0.106 / -0.198 |

   Envelope OFF => correlation ~0 on every channel (planes spatially
   unaligned). Envelope ON => R aligns to 0.974. The ALIGNMENT lever is
   entirely geometric.

## Conclusion

Stage-A photometry is closed (bit-exact port, verified against the proven
formula). The residual stage-A divergence (R corr 0.974 not 1.0; U/V lower) is
the GEOMETRY gap: Phoenix's DERIVED envelope-fit resample approximates -- but
is not -- Lumen's proven src2 stereo-plane resample (radial table + uniform
matrix), which is CLM-PREFUSION-002, still OPEN. The apparent per-channel
"gain/offset" is the signature of comparing two differently-resampled planes
(resampling redistributes energy; vignetting gradients under a slightly-wrong
warp read as a slope), NOT a photometric formula error.

WSJF: the next real stage-A work is the src2 resample (CLM-PREFUSION-002) --
a large job, the same resample whose byte-plane producer resisted 14
instruments. It is correctly NOT a quick formula port. No Phoenix change is
licensed for stage-A photometry: it already ports the proven formula.

## Correction to prior note

The earlier `runtime_unit2_70mm_b4_create_stereo_stage_vector.md` addendum
called stage 15 a "nonlinear global tone transform" on the depth path. That is
RETRACTED for the depth planes: stage 15 materializes the u16 storage from the
RGBA slot (output is NOT a function of the plane's own input -- 973/973
inputs map to multiple outputs), and it is on the DISPLAY color path. The
depth GUIDANCE uses the separate collapse2->ConvertToYUV path proven above,
which Phoenix already ports. Stage 15 is not a depth-plane port item.
