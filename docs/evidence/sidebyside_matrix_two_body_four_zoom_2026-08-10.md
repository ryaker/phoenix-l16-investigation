# Side-by-Side Plane Matrix: Two Bodies x Four Focals (2026-08-10)

Both sides FRESH from one LRI per row (fresh Lumen deterministic capture +
fresh Phoenix, same session). Harness: `tools/sidebyside_matrix.sh`. Kernel =
bilinear (current default). Metric = R/G/B corr of Phoenix vs Lumen `image_i`,
sampled every 17th pixel. All 7 LRIs tier/focal-verified via PHX_CALIBDUMP.

## Anchor plane (img0) R corr / slope

| Capture | R corr | G corr | B corr |
|---|---|---|---|
| u1_28  | 0.9994 | 0.9166 | 0.9953 |
| u1_35  | 0.9982 | 0.9432 | 0.9947 |
| u1_70  | 0.9665 | 0.8951 | 0.9646 |
| u1_150 | 0.9864 | 0.9610 | 0.9857 |
| u2_28  | 0.8452 | 0.6063 | 0.5945 |
| u2_35  | 0.9955 | 0.8983 | 0.9335 |
| u2_70  | 0.9738 | 0.5644 | 0.8056 |

## Findings a single-LRI comparison hides

1. **Unit-1 is strong across all focals** (R 0.966-0.999; wide 28/35 near
   perfect). The port generalizes well on body 1.

2. **Unit-2 28mm is the weak spot** (R 0.845, G 0.606, B 0.595) and u2_70 has
   weak chroma (G 0.564). Body-2 wide + chroma is where the port is worst. The
   single u2_70 point I had fixated on is middling, not representative.

3. **img2 has a systematic chroma SIGN FLIP on every capture** (R ~+0.99 but G
   ~-0.99, B ~-0.95 across all 7 LRIs/both bodies). This is the mono/A2 plane
   index; Phoenix's img2 U/V is the negative of Lumen's -- a fixed convention
   bug on that plane, invariant to focal/body. Worth a dedicated fix.

4. **G (U chroma) is systematically the weakest channel** (R/B are stronger),
   pointing at an AWB/color-match residual, not only geometry.

Slopes range 0.36..1.07 -> a photometric gain component also varies by capture.

## Bearing

Any resample/geometry port (e.g. Catmull-Rom, the tele operands) must be
A/B'd across THIS matrix, not one LRI -- a change can help Unit-1 tele and
hurt Unit-2 wide. The img2 chroma sign flip and the Unit-2 chroma weakness are
higher-value, more general targets than the sub-1% resample-kernel refinement.
