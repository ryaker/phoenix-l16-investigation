# Side-by-Side Protocol + Result: u2_70 Resample Kernel (2017-12-01)

**Date:** 2026-08-10

## Protocol (corrects two prior method errors)

All Phoenix-vs-Lumen and Phoenix-vs-Phoenix comparisons MUST run both sides
FRESH from the SAME LRI in the same session. Do NOT compare against a cached
dump: a cached side hides (a) input mismatch and (b) build mismatch. Both bit
me this turn -- fresh Phoenix (2018-02-08, parses WIDE/35) vs stored Lumen
(2017-12-01, TELE/70) gave garbage (R corr -0.23), and fresh-vs-cached-Phoenix
crossed builds.

The correct u2_70 tele input is `/Volumes/Base Photos/Light/2017-12-01/
L16_00010.lri` (the 2018-02-08 same-basename file parses WIDE/35).

## Determinism check

Re-ran the deterministic Lumen capture (`run_g42_bank_capture.sh ...
serial-executor-2d30`) fresh on 2017-12-01 -> `u2_70_sidebyside_fresh/`.
`image0` is BYTE-IDENTICAL to the stored `u2_70_executor_serial_r1/image0`
(mean|delta|=0.0000). The executor-2d30 serialization is deterministic; the
stored capture was valid. The only invalid runs were Phoenix on the wrong LRI.

## Result (both fresh, LRI=2017-12-01, Phoenix vs Lumen image0)

| Kernel | R corr | R slope | G corr | B corr |
|---|---|---|---|---|
| bilinear (default) | 0.97378 | 0.9023 | 0.564 | 0.806 |
| Catmull-Rom (PHX_ENVCATMULL) | 0.96655 | 0.8867 | 0.501 | 0.730 |

The proven Catmull-Rom kernel (bit-exact, addendum 3) run ALONE slightly
regresses on every channel, because Phoenix still applies its envfit + full
per-camera Brown-Conrady radial table while Lumen's captured anchor resample is
affine + a NEAR-IDENTITY radial LUT; a sharper kernel amplifies that operand
mismatch. Hence Catmull-Rom is gated opt-in until the full geometry operands
(captured on THIS tele LRI, not the wide one) are ported as a unit and
validated fresh side-by-side.

## Next

Capture src2 warp operands on 2017-12-01 (tele H, center, radial LUT), port the
complete transform (affine H + captured LUT + Catmull-Rom + 1/64 subpixel) as a
unit, and re-validate with a fresh Lumen + fresh Phoenix run on the same LRI.
