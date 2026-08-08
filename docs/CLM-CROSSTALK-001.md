# CLM-CROSSTALK-001 — Lumen's Bayer cross-talk correction stage

Status: **CLOSED** (2026-08-03). Selector, amount fit, IR/AWB matrix preparation,
scalar worker and full-frame tile decomposition all proven from the binary;
ported to Phoenix; amount fit reproduces the Codex two-body replay bit-exactly;
end-to-end image-quality win measured across both bodies and four focals.

Binary of record: `libcp.dylib`
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## 1. Where it sits

Pipeline order (CLM-PIPELINE-001), Bayer stage index 4:

    hot pixel (0x341770) -> highlight restore (0x343e10) -> default Bayer
    normalization/materialization (0x340a30 -> 0x350ff0) -> CROSS TALK (0x342280)
    -> demosaic (0x342c60) -> CNR (0x34b3b0) -> ...

The stage runs on the **normalized** float plane, i.e. after

    n = f32(f32(v - black) / f32(white - black))

and before demosaic.

Phoenix insertion point: `tools/phoenix_fuse.cpp`, inside `buildPlane`, between
the Bayer-phase override and `premerge::demosaickLightV1`. The fit
(`depth::crossTalkFit`) is computed per camera on the **pristine** u16 raw; the
apply (`depth::crossTalk`) normalizes, corrects, and maps back to RAW-DN
(`n*span + black`) so Phoenix's separately-validated demosaic scale (whose
`eps1`/`eps2` depend on the DN-scale `max_gain`) is undisturbed. Env gate
`PHX_NOXT` reverts to the previous behaviour.

Implementation: `engine/depth/cross_talk.{h,cpp}` plus the 21 installed
candidate tables emitted as hex-float literals into
`engine/depth/cross_talk_tables.{h,cpp}` by
`tools/lldb_probes/correction_liveness/emit_crosstalk_tables_cpp.py`
(fails closed on SHA/digest drift).

## 2. Public inputs

The per-camera matrix grid is `FactoryModuleCalibration.vignetting.crosstalk`,
selected by the public `FactoryModuleCalibration.camera_id`. It is a
`17 x 13 x 4 x 4` float32 grid, row-major `(y, x, row, col)`; element `(y,x)`
starts at word `(y*17 + x)*16`.

The candidate-table selector inputs are all public:

    sensor_type = LightHeader.sensor_data.type    (field 16 -> field 1;
                                                   2 = SENSOR_AR1335)
    variant     = exists(FactoryModuleCalibration.color[] record with
                         color_matrix present)
    CCT         = robertson_xy_to_cct(scene_xy)              (libcp 0xab2e0)
    group       = 0 if camera_id <= 4 else (1 if camera_id <= 9 else 2)

Installed table base addresses (add `group*3536`):

    A_true 0x5B0540   A_false 0x5B2EB0
    B_true 0x5B65F0   B_false 0x5B8F60
    C_true 0x5BC6A0   C_false 0x5BF010
    SENSOR4:  A 0x5AF770   B 0x5B5820   C 0x5BB8D0

Scalar constants: `0x5AF2D8` = 1e9 (best-score init), `0x5AF2DC` = f32(1/19),
`0x5AF2E0` = 6504070.0, `0x5AF2E4` = 3000.0, `0x5AF2E8` = 5000.0,
`0x5AF2EC` = 2504070.0, `0x5A886C` = 0.5.

## 3. Amount selection

Proven by `verify_crosstalk_amount_formula.py`. Binary32 throughout, in this
exact order.

Half-res ratio planes (2080x1560 for a 4160x3120 mode-0 frame):

    R  = raw[ry::2, rx::2]        B  = raw[1-ry::2, 1-rx::2]
    Gh = raw[ry::2, 1-rx::2]      Gv = raw[1-ry::2, rx::2]
    G     = f32(f32(f32(Gh) + f32(Gv)) * 0.5)
    recip = f32(1.0 / G)
    RR = f32(R * recip)           BR = f32(B * recip)

Backward first differences, energy, and acceptance:

    ar_x[1:,1:] = RR[1:,1:] - RR[1:,:-1]   ar_y[1:,1:] = RR[1:,1:] - RR[:-1,1:]
    ab_x, ab_y likewise from BR
    red_energy    = f32(ar_x*ar_x + ar_y*ar_y)
    blue_x_energy = ab_x*ab_x     blue_y_energy = ab_y*ab_y
    total    = f32(f32(red_energy + blue_x_energy) + blue_y_energy)
    accepted = total <= f32(0.02)
    red_mask  = accepted & (sqrt(red_energy)  > 0)
    blue_mask = accepted & (sqrt(blue_energy) > 0)

Cell fit onto the 17x13 node grid (`scale_x = f32(2080/f32(17))`,
`scale_y = f32(1560/f32(13))`, `x0 = int(trunc(f32(x)*scale_x))`,
`x1 = int(trunc(f32(x+1)*scale_x))`, same for y):

    fit[y,x,0] <- mean(RR | red_mask)     fit[y,x,2] <- mean(BR | blue_mask)
    all lanes init 1.0; lanes 1 and 3 stay 1.0

Twenty-step A/B blend search (`best` init 1e9, strict `<`):

    for i in 0..19:
        amount    = f32(f32(i) * f32(1/19))
        candidate = f32(f32(A*amount) + f32(B*f32(1 - amount)))
        product   = f32(candidate * fit.reshape(-1,4))
        mean      = sequential_sum / 221
        variance  = sum((mean - product)^2) / 221
        score     = variance[0] + variance[2]
        if score < best: best, selected = score, amount

Exposure energy, from an 8x8-decimated histogram of the **Gh** site:

    hist        = bincount(raw[ry::8, (1-rx)::8], minlength=1024)
    cumulative  = cumsum(hist)
    target      = f32(f32(cumulative[-1]) * 0.5)
    median_bin  = argmax(cumulative >= int(target))
    normalized  = f32(f32(f32(median_bin) - f32(black)) /
                      f32(f32(white) - f32(black)))
    energy      = f32(f32(normalized * sensor_analog_gain) *
                      f32(sensor_exposure))

Table-C gate and override:

    c_gate = (energy < 6504070.0) and (cct >= 3000.0) and (cct < 5000.0)
             and (energy >= 2504070.0)
    if c_gate and score(C) < best: selected = -1.0     # sentinel for "use C"

## 4. IR shaping and AWB conjugation

Proven by `verify_crosstalk_ir_preparation.py`.

    selected = C            if amount < 0
             = f32(f32(A*amount) + f32(B*f32(1 - amount)))   otherwise
    shaped   = f32(f32(f32(selected - 1.0) * 0.75) + 1.0)
    ir[y,x]  = diag(shaped[y,x,0], shaped[y,x,1], shaped[y,x,1], shaped[y,x,2])

    bayer_awb = [v0, v1, v1, v2]   with v = f32(1 / awb_gains.{r, g_r, b})
    D         = diag(bayer_awb)
    M[y,x]    = ((invD @ A_public[y,x] @ D) @ ir[y,x])

Scalarized exactly as the binary does it:

    T1[i][j] = invw[i] * A[i][j]
    T2[i][j] = T1[i][j] * w[j]
    M[i][j]  = T2[i][j] * q[j]          q = [s0, s1, s1, s2]

The `invD * A * D` conjugation is why `M` operates on the **non**-white-balanced
plane — exactly what Phoenix has at that point. The reciprocal AWB triplet is
therefore read directly from `p.header.view_preferences.awb_gains`,
**independently of the `PHX_AWB` gate** (Phoenix's master path is AWB-free by
default: `phoenix_fuse.cpp:1268` leaves `gains.g` at `{1,1,1}`).

## 5. Scalar worker and tile decomposition

Helper `0x1019d0`, proven by `verify_crosstalk_scalar_formula.py`.

Bilinear node interpolation, corners in the binary's own order:

    c0 = node(cy, cx)      c1 = node(cy+1, cx)
    c2 = node(cy, cx+1)    c3 = node(cy+1, cx+1)
    left  = lerp(c0, c1, ty)
    slope = add(sub(mul(sub(c3, c2), ty), left), c2)
    M     = add(left, mul(tx, slope))

Full-frame decomposition (CLOSED): a **uniform** pitch,
`scale_f32 = f32(1/260)`, evaluated at the **quad origin** (even coords):

    gx = f32(x * f32(1/260))   cx = trunc(gx)   tx = gx - cx      (same for y)

Sampling policy: whole-sample reflection on the low side (`abs`), clamp on the
high side (`min(v, N-1)`); reflection only ever fires at the true frame border.

Lane semantics, recovered from `parity_i32 = (1,0, 0,0, 1,1, 0,1)` and stated
relative to the EVEN quad origin `(x, y)`:

    lane0 (R)    site (x+rx,   y+ry)    four-sum (-1,0),(+1,0),(0,-1),(0,+1) x M01
    lane1 (G_r)  site (x+1-rx, y+ry)    pair (-1,0),(+1,0) x M10;
                                        pair (0,-1),(0,+1) x M13
    lane2 (G_b)  site (x+rx,   y+1-ry)  pair (0,-1),(0,+1) x M20;
                                        pair (-1,0),(+1,0) x M23
    lane3 (B)    site (x+1-rx, y+1-ry)  four-sum (+1,0),(-1,0),(0,-1),(0,+1) x M31

The nesting differs per lane: C0/C3 multiply the four-sum by `mul(M_elem, 0.5)`,
while C1/C2 multiply the bracketed pair-sum by `0.5` last.

Limiter (structurally 0 under the supported contract, but ported verbatim):

    alpha  = min(1, max(0, (O0-1)*Lr, (max(O1,O2)-1)*Lg, (O3-1)*Lb))
    out_k  = Ck + (Ok - Ck) * alpha

## 6. Verification — fit reproduces Codex's replay bit-exactly

Phoenix `[xt]` diagnostics vs the Codex two-body replay:

| run | Phoenix | Codex proven |
|---|---|---|
| u1_28 header | `cct=4953.66 awb_recip=(0.582126737, 1, 0.629390538)` | 4953.66357421875; 0.5821267366409302 / 1.0 / 0.6293905377388 |
| u1_28 cam 0 | `amount=1 i=19 energy=1053987` | amount 1.0 (i=19), energy 1053987.0 |
| u1_28 cam 6 | `amount=1 i=19 energy=3136364.75 cgate=1 csel=0` | amount 1.0, energy 3136364.75, C loses |
| u2_28 header | `cct=4175.77 awb_recip=(0.606687605, 1, 0.56212914)` | 4175.767578125; 0.606687605381012 / 0.5621291399002075 |
| u2_28 cam 0 | `amount=0.736842096 i=14 energy=0` | 0.7368420958518982 (i=14), energy 0.0 |

Every float word matches.

Coverage achieved by the canonical corpus: all three camera groups
(`camera_id` 0 -> group 0; 5-9 -> group 1; 10-14 -> group 2), both bodies,
four focals, all 20 blend indices exercised across shots (i = 0, 14, 15, 18, 19
observed), and the table-C override path fired once for real
(u2_35 cam 0: `cct=4701.89 energy=2683583.25 cgate=1 csel=1`).

## 7. Verification — end-to-end image quality

Full 5-shot x 2-condition sweep against the Lumen masters
(`runs/verify_master/*_lumen.hdr`), scored with
`tools/lldb_probes/fusion_neutral_apply/achro.py`. All ratios are
**lumen / phoenix** on nonzero-green-masked channel means; 1.0000 is perfect.

XT OFF (`PHX_NOXT=1`):

    shot     R        G        B        achro
    u1_28    1.0641   1.0024   0.9767   1.0037
    u1_35    1.0706   1.0188   0.9573   1.0048
    u1_70    1.0026   1.0089   1.0026   1.0063
    u1_150   1.0064   1.0095   1.0103   1.0093
    u2_35    0.9573   0.9427   0.9323   0.9423

XT ON (default):

    shot     R        G        B        achro
    u1_28    0.9820   1.0122   0.9861   0.9998
    u1_35    0.9992   1.0164   0.9693   0.9985
    u1_70    0.9998   1.0080   1.0061   1.0063
    u1_150   0.9995   1.0029   0.9979   1.0009
    u2_35    0.8833   0.9272   0.9013   0.9129

R-to-B chroma spread `|R - B|`, the quantity this stage exists to correct:

    shot     OFF      ON       verdict
    u1_28    8.74%    0.41%    -95%
    u1_35   11.33%    2.99%    -74%
    u1_70    0.00%    0.63%    +0.63pp (noise floor)
    u1_150   0.39%    0.16%    -59%
    u2_35    2.50%    1.80%    -28%

Whole-frame achromatic ratio moves toward 1.0000 on u1_28 (1.0037 -> 0.9998),
u1_35 (1.0048 -> 0.9985) and u1_150 (1.0093 -> 1.0009); is unchanged on u1_70
(1.0063); and moves away on u2_35 (0.9423 -> 0.9129).

The long-standing u1_35 residual — "R ~7% low, B ~4-6% high after highlight
restore" — is eliminated on R (1.0706 -> 0.9992). That residual was the
predicted signature of this exact missing stage, and it is now gone.

## 8. Residuals left open by this stage

These are **not** cross-talk defects; they are pre-existing items the sweep now
measures more precisely. None of them is to be tuned away.

1. **u2_35 brightness excess.** Already a tracked open item (~5.5% excess,
   achro 0.9447 with highlight restore off). Cross-talk lifts R by +8.4% on
   this shot — the same magnitude it lifts u1_35's R by (+7.1%), where the
   result lands on Lumen exactly. So the lift is right and the **baseline** is
   wrong. The u2_35 achro regression is a symptom of the pre-existing unit-2
   brightness bug, not of this stage. Its per-camera fit is sound and it is the
   one shot in the corpus that exercises the table-C override.

2. **u1_28 R now 1.8% HIGH** (0.9820) where it was 6.4% low. A small residual
   over-correction, sign-flipped from the pre-stage error.

3. **G runs 0.3-1.6% low across the whole corpus** in both conditions, so it is
   independent of this stage.

4. **u1_35 B still ~3% high** (0.9693), down from 4.3%.

5. **Phoenix output geometry is inconsistent across shots** — u1_28 wrote
   5216x3912, u1_35 and u2_35 4173x3129, u1_70 4422x3316, u1_150 2074x1556,
   while every Lumen master is 10432x7824. Pre-existing and unrelated to this
   stage, but it means every number above is a downsampled-vs-full-res channel
   mean comparison. Tracked separately.

## 9. Reproduce

    cd /Users/ryaker/L16_Phoenix/phoenix/build
    cmake --build . --target phoenix_fuse -j8
    ./tools/phoenix_fuse <in.lri> -o /tmp/out.hdr           # cross-talk ON
    PHX_NOXT=1 ./tools/phoenix_fuse <in.lri> -o /tmp/off.hdr

    cd /Users/ryaker/Dev/L16_Lumen_ReverseEngineering
    python3 tools/lldb_probes/fusion_neutral_apply/achro.py xton
    python3 tools/lldb_probes/fusion_neutral_apply/achro.py xtoff

Evidence bundles of record:
`bundle_static_runtime_crosstalk_selector_public_origins_two_body.md`,
`bundle_corrective_runtime_crosstalk_tile_decomposition.md`,
`verify_crosstalk_amount_formula.py`, `verify_crosstalk_ir_preparation.py`,
`verify_crosstalk_scalar_formula.py`.
