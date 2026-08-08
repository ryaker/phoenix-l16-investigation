# Selected Scalar Cross-Talk Exact Formula and Public Origin

## Result

The selected profile-3 Bayer cross-talk path is formula-closed from public
LRI bytes through the scalar output consumed by demosaic.

The public matrix grid is
`FactoryModuleCalibration.vignetting.crosstalk`, selected by public
`FactoryModuleCalibration.camera_id`. The runtime owner grid at callback
`+0x28` is byte-identical to that public `17 x 13 x 4 x 4` float32 grid. It
is not generated IR data. Callback `+0x30` is a separate generated diagonal
IR grid selected from installed tables by camera group, sensor type, variant,
and an image-derived amount.

This selection rule is deliberately distinct from the already admitted
vignetting-profile rule. The selected vignetting profile uses calibration
vector ordinal `CapturedImage+0x60`; the cross-talk owner map keys modules by
public `camera_id`. Applying the vignetting ordinal to cross-talk was the
source of an earlier apparent public/runtime hash mismatch.

## Installed Custody

- binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- public owner accessor `0xe7290..0xe72f4`:
  `6ae396299c8db85d44f2d34f79c2e5630858ee45417ebb98620a61e352ee28cc`
- public cross-talk decoder `0x135620..0x1362bb`:
  `d1585d0ab11fd5cc8a878bef219e7cc017f1f4cb55dae7dca0ae4bcde89c1d6d`
- repeated `Matrix4x4F` decoder `0x1362c0..0x136384`:
  `2979bf6e53b60b3e1458f732004c1d24e0ce2ca62ea2b26c0e18cf294228613d`
- selected scalar factory `0xfb6a0..0xfbd00`:
  `68f7970dd651e3a4400e52f1cbb7ec9c59867f4fdb98f6124e6b4f29ba42d229`
- selected scalar callback `0x1054d0..0x106c80`:
  `b18f4a2134ecc02222e640a0e6d8b06d62fdb6a5ff3a13adf5a014b881d8ef9d`

Factory `0xfb6a0` calls `0xf3570(CapturedImage)` at `0xfb79e`.
`0xf3570` delegates to `0xe7290(owner, CapturedImage+0x60)`, and the returned
camera-keyed grid is installed at callback `+0x28`. Accessor `0xe7290`
returns keyed owner-node field `+0x110`.

Decoder `0x135620` supports both public encodings. The packed path requires a
word count divisible by 16, allocates 64 bytes per matrix, and copies all 16
float32 words unchanged. The repeated-message path calls `0x137c50` and
stores four XMM rows unchanged. Both paths validate the declared
`width * height`; the selected LRIs declare `17 x 13`.

## Public Matrix Join

The verifier scans every LELR block, decodes both public encodings, and
requires a unique byte identity at the matching public camera ID.

| Input | Runtime key | Public module index / `camera_id` | Encoding | Exact grid SHA-256 |
|---|---:|---:|---|---|
| Unit-1 exact `28mm` A1 | `0` | `1 / 0` | `data_packed` | `9395820b112e67e485dbd14756d532171c171fd764154f8968940f20ff636606` |
| Unit-1 exact `28mm` B2 | `6` | `9 / 6` | `data_packed` | `69fd0df4061a87c951271b2dd08432111a4dccba170bef27dc917ba437fd1a0d` |
| Unit-2 exact `28mm` A1 | `0` | `2 / 0` | `data_packed` | `1cdd12303bd0e7a4abe03b0f999e7df7d5cce738ca4c64c76ad572eca37ff8cf` |

The differing module positions (`1`, `9`, and `2`), camera keys, and body
calibrations rule out a fixed-vector-position or fixed-A1 coincidence.

## Amount Selection

All operations below are binary32 in the order implemented by
`verify_crosstalk_amount_formula.py`.

For Bayer red phase `(rx, ry)`, form half-resolution planes

```text
R = raw[ry::2, rx::2]
B = raw[1-ry::2, 1-rx::2]
Gh = raw[ry::2, 1-rx::2]
Gv = raw[1-ry::2, rx::2]
G = f32(f32(Gh + Gv) * 0.5)
RR = f32(R * f32(1 / G))
BR = f32(B * f32(1 / G))
```

For each ratio plane, backward x/y differences are formed from `(1,1)`.
Samples pass when the combined red and blue squared-gradient energy is
`<= 0.02`; each color additionally requires its own gradient magnitude to be
nonzero. The image is partitioned by truncated boundaries into `17 x 13`
cells. Accepted `RR` and `BR` samples are sequentially float32-summed and
divided by their count into fit lanes `0` and `2`; empty cells and unused
lanes `1` and `3` remain `1.0`.

Installed A/B/C tables are selected by sensor type, variant flag, and camera
group `0` for IDs `0..4`, `1` for IDs `5..9`, or `2` for IDs `10..15`.
The companion selector-origin bundle closes those inputs as public
`LightHeader.sensor_data.type`, public
`FactoryModuleCalibration.color[].color_matrix` presence, public
`FactoryModuleCalibration.camera_id`, and the admitted public-AWB/A-D65
scene solve followed by installed Robertson xy-to-CCT conversion.
For `i = 0..19`:

```text
t_i = f32(i * f32(1 / 19))
S_i = f32(f32(A * t_i) + f32(B * f32(1 - t_i)))
Q_i = f32(S_i * fit)
score_i = population_variance(Q_i[:,0]) + population_variance(Q_i[:,2])
```

The strict-`<` minimum wins. C is considered only when
`energy < 6504070`, `3000 <= CCT < 5000`, and `energy >= 2504070`; if its
score is strictly below the best A/B score, the returned amount is `-1`.
The energy path selects histogram `1` from four RAW histograms sampled every
eight pixels, finds its half-count median bin, normalizes by public
black/white levels, then computes
`f32(f32(normalized * sensor_analog_gain) * sensor_exposure)`.

Exact replay results:

| Input / camera | RAW ratio words | Fit words | Scores | Selected amount |
|---|---:|---:|---:|---:|
| Unit-1 A1 / `0` | `6,489,600` | `442` | `20` | `1.0` (`i=19`) |
| Unit-1 B2 / `6` | `6,489,600` | `442` | `20 + C` | `1.0` (`i=19`; C loses) |
| Unit-2 A1 / `0` | `6,489,600` | `442` | `20` | `0.7368420958518982` (`i=14`) |

The three returned amounts, every candidate score, all fit words, all ratio
words, and the captured histogram/energy packets match exactly.

## IR and Prepared Matrices

If `amount < 0`, select installed table C. Otherwise select
`S = f32(f32(A*amount) + f32(B*f32(1-amount)))`. For every grid node and
table lanes `(r,g,b,unused)`:

```text
q = f32(f32(f32(S - 1) * 0.75) + 1)
B_ir = diag(q.r, q.g, q.g, q.b)
```

All `3,536` generated IR matrix words match captured callback `+0x30` for
Unit-1 A1, Unit-1 B2, and Unit-2 A1.

The callback's public AWB vector `(wr,wg,wb)` expands to
`w = (wr,wg,wg,wb)`, `D = diag(w)`. At each public/IR grid node, the worker
matrix is

```text
M = (inverse(D) * A_public * D) * B_ir
```

The installed operation order is preserved. The four captured prepared
corners use `(y,x) = (0,0), (1,0), (0,1), (1,1)`. All `64/64` words match
for each physical body's A1 packet. The AWB vector's separate public origin
is admitted by `bundle_static_runtime_awb_public_origin_four_zoom_two_body.md`.

## Scalar Worker

For an even Bayer-group origin `(x,y)`, callback helper `0x1019d0` bilinearly
interpolates every matrix element from four prepared corners. In a tile with
offset `(ox,oy)` and scale `(sx,sy)`:

```text
tx = f32(f32(x + ox) * sx)
ty = f32(f32(y + oy) * sy)
```

The executable verifier preserves the installed non-associative interpolation
order. The observed `260 x 260` packets use zero offset and
`sx = sy = 0.003846153849735856`.

Let `P(y,x)` be the scalar Bayer input. Low-edge reads use whole-sample
reflection (`-1 -> +1`), then coordinates clamp at the high edge. For the
four output parities, in store order `(y,x+1)`, `(y,x)`, `(y+1,x+1)`, and
`(y+1,x)`, the correction candidates are:

```text
C0 = P(y,x+1)*M00
     + 0.5*M01*(P(y,x)+P(y,x+2)+P(y-1,x+1)+P(y+1,x+1))

C1 = P(y,x)*M11
     + 0.5*(M10*(P(y,x-1)+P(y,x+1))
            + M13*(P(y-1,x)+P(y+1,x)))

C2 = P(y+1,x+1)*M22
     + 0.5*(M20*(P(y,x+1)+P(y+2,x+1))
            + M23*(P(y+1,x)+P(y+1,x+2)))

C3 = P(y+1,x)*M33
     + 0.5*M31*(P(y+1,x+1)+P(y+1,x-1)+P(y,x)+P(y+2,x))
```

Each multiply/add follows the exact nested binary32 order in
`verify_crosstalk_scalar_formula.py`. With originals
`O=(P(y,x+1),P(y,x),P(y+1,x+1),P(y+1,x))` and captured limit vector
`L=(Lr,Lg,Lb)`:

```text
alpha = clamp(max((O0-1)*Lr, (max(O1,O2)-1)*Lg, (O3-1)*Lb), 0, 1)
out_k = f32(Ck + f32((Ok-Ck) * alpha))
```

Two physical-body A1 packets each replay `67,600/67,600` destination words
bit-for-bit, with zero mismatch and zero error. Their public matrix hashes,
AWB vectors, selected amounts, generated IR grids, and red/blue limiter
values differ. The sampled packets had `alpha=0`. That is the required
supported-input result rather than an uncovered bright-pixel branch: public
RAW10 is bounded by `1023`, every complete corpus input uses public
`white_level=1023`, the admitted upper-median hot-pixel stage is
range-preserving, and stage-3 normalization maps every retained sample to
`<= 1.0`. Therefore each unclamped limiter term is nonpositive and the
clamped selected-path `alpha` is structurally zero. The installed limiter
formula remains admitted for alternate inputs, but a nonzero-alpha public
RAW10 discriminator is not expected under the supported contract.

## Downstream and Scope

The companion corrective liveness bundle proves selected callback `0x1054d0`
executes in complete profile-3 Unit-1 `28/35/70/150mm` renders and exact-70mm
Unit-2, and joins `240/240` stage-6 demosaic inputs to its stage-5 allocation.
Therefore the formula has canonical four-focal mechanism scope, with exact
numeric two-body replay at exact `28mm`.

This admits the selected `float,true` profile-3 path. It does not claim
profiles 1/2, the other three cross-talk specializations, a full all-camera
numeric census, a nonzero-limiter output packet, firmware invariance, or a
body/firmware cause. Those are validation or unsupported-route scope, not
gaps in the admitted selected-profile formula.

## Reproduction

```bash
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_callback_slots.py
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_public_origin.py
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_amount_formula.py
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_ir_preparation.py
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_scalar_formula.py \
  runs/correction_liveness/formula_unit1_28mm_a1
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_scalar_formula.py \
  runs/correction_liveness/formula_unit2_28mm_a1
```

All commands fail closed on installed-body drift, missing artifacts, public
identity ambiguity, or any float32 word mismatch.
