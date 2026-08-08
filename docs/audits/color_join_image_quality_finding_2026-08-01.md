# Image-Quality Finding: Color Join Defect (2026-08-01)

**Status:** historical investigation log; the color-join defect is resolved by
the later 2026-08-02 receipts in this file  
**Scope:** Phoenix end-to-end render of Unit-1 exact-28mm
`/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (SHA `2ac51af5…`),
current tree (post color-wrapper wiring, TRUTH 3.0.345 state)

> **Current reading rule (2026-08-08):** sections above the explicit
> retractions are provenance, not current conclusions. The final receipts
> prove the profile-3 fmt-3 master is camera-linear and remove Phoenix's
> invented inverse-CCM/Bradford master join. TRUTH `3.0.347` additionally
> supersedes the later statement that MonoFusion auxiliary and target noise
> views always have identical clipped extents: at reducer-tile remainders they
> intersect their own descriptor domains independently.

## Method

Rendered the LRI end-to-end with the current `phoenix_fuse` (default path,
also with `PHX_ACRE_MASTER=1`, also `PHX_NOMONO=1`) and compared the linear
`.hdr` export against Lumen's own bridge render of the SAME LRI
(`runs/stereolayer_depth_writer/depth_writer_28mm.hdr`, profile 3, fmt 3,
10432x7824 flat RGBE — log in the same dir confirms the input path).

## Results (global channel means, linear)

| Source | R/G | B/G |
|---|---:|---:|
| Lumen merged HDR (ground truth) | 0.5521 | 0.6329 |
| Phoenix camera-linear stage ([post] print) | 0.154 | 0.206 |
| Phoenix final linear-ProPhoto HDR | 0.1892 | 0.0127 |
| ratio Phoenix/Lumen (final) | 0.34x | **0.02x** |

- The merge itself is healthy: geometry/detail/fusion visually match Lumen's
  frame; the exact production flow reproduces the installed rejection count
  (73,073); `PHX_NOMONO=1` changes R/G only 0.154→0.177, so MonoFusion is NOT
  the cause.
- The defect is in the post color chain (square-copy/AWB/CCM/CAT join): red
  reaches ~1/3 of target, blue is nearly destroyed (2% of target) in the
  final linear output. `PHX_ACRE_MASTER` does not correct it (display tone
  cannot fix camera-linear ratios).
- Lumen's own linear output sits AT the public-AWB expectation
  (R/G≈1/awb_r=0.582, B/G≈1/awb_b=0.629), i.e. after its full chain the data
  is camera-gray-balanced; a naive gamma preview of Lumen's HDR looks near
  neutral. Phoenix's "[post] camera-linear" is already ~3.5x off before any
  display stage.

## Repro

```bash
# ours (container or mac build)
phoenix_fuse .../L16_02130.lri -o out.hdr
# stats: decode flat RGBE, mean R/G B/G (see this doc's method)
```

## Pointer for the join audit

This is the concrete pixel-changing defect for the queued "end-to-end
selected color-camera reconstruction" item. The suspect segment is
`phoenix_fuse` post chain: `sq -> *awb_recip -> cap_norm -> CCM^-1(alpha
blend) -> Bradford CAT -> ProPhoto` (the `[post] CCM^-1(cam 0) ok,
alpha=0.245` path) — some factor or direction in that join does not match
the installed pipeline; blue collapse (0.02x) suggests a matrix applied in
the wrong space or direction rather than a scalar gain slip.

## LIVE lldb RECEIPTS (2026-08-01, captured directly on installed libcp b38dc4b3)

Two captures on tools/lri_process + Lumen frameworks, Unit-1 28mm L16_02130.

### Receipt 1 — IRAMP square-copy scale vector (bp 0x3ecaa4)
scale_vec_from_wrapper+0x10 = [0.5821267, 1.0, 0.6293905, 1.0]
== EXACTLY the public AWB reciprocal (1/awb r=0.582 g=1.0 b=0.629).
Near-gray merged pixel (0.494,0.498,0.474) -> (0.288,0.498,0.299): Lumen
introduces the SAME green cast Phoenix does, intentionally. **AWB is NOT the
defect; the earlier "double-application" hypothesis is refuted** — removing
Phoenix square-copy awb only makes it worse.

### Receipt 2 — live interpolated CCM matrix (bp 0x350bc0, 28mm)
target_cct 4953.66 K; endpoints A=2855.63 K, D65=6502.08 K; internal pair (2,7).
Interpolated M (applied), row-major:
  [ +0.7498 -0.1430 -0.0116 ]
  [ -0.3101 +1.0852 +0.2590 ]
  [ -0.0234 +0.2353 +0.4909 ]
Back-solved blend weight (M-D65)/(A-D65) = 0.245 on every element ==
Phoenix ccm_alpha=0.245. **CCM matrix construction + mired alpha are CORRECT
and already match Phoenix.**

### Narrowed defect (was: whole post color chain)
The ONLY divergence is the per-pixel APPLICATION:
  - Phoenix: invert3x3f(M) -> Mccm_inv, apply M^-1, then add a Bradford
    scene->D50 CAT + XYZ->ProPhoto (phoenix_fuse.cpp ~2532-2566).
  - Lumen: builds the same forward M; application direction/space of M on the
    10432x7824 master path is the open receipt.
M^-1 blue row = [-0.143, -0.519, +2.308]: for the green-dominant scene the
-0.519*G term drives blue toward zero -> clamp -> the measured B/G=0.013.

### Remaining capture (the fix-defining receipt)
Trace the per-pixel consumer of the matrix stored by setWhiteBalance 0x342a80
on the master path: does Lumen compute out = M @ cam (forward) or M^-1 @ cam,
and is any CAT/ProPhoto matrix folded in? That single receipt converts the fix
from hypothesis to exact. Runnable with the same lri_process+lldb harness.


## SESSION 2026-08-02: MASTER COLOR TRANSFORM LOCATED IN FUSION (live lldb, proven)

### What was ruled IN/OUT this session (no re-derivation of solved work)
- **AWB double-application** (demosaic + post-square, both = 1/awb reciprocal
  [0.582,1,0.629]) is Codex-PROVEN (CLM-AWB-001) and CORRECT. Not the bug.
- **CCM matrix construction** (interpolated A/D65 color_matrix M, alpha=0.245,
  Robertson chromaticity solver) is Codex-PROVEN (CLM-CCM-002) and CORRECT.
- **Demosaic** multiplies raw by gains=1/awb; Phoenix demosaic is bit-exact to
  Lumen (corrective full-frame bundle). So both demosaic-outs are identical
  (R/G~0.307 green). The green cast at demosaic is intended and shared.
- **Phoenix's Bradford CAT + CCM-inversion (Mccm_inv) + CCM_NEUTRAL + FWDCCM**
  are INVENTED (code comments admit "industry-standard", "as the old code
  assumed"). They cause the blue-collapse (final B/G=0.013). MUST be removed.

### The master color transform is applied in the FUSION (NEW, live-captured)
Breakpoint libcp `0x1ab2d0` (the worker called by `FusionCacheBayer::vfunc[2]`
"neutral color apply", dispatched from `0x406970`) fired on the full
10432x7824 profile-3 master render, thread #11. Captured:

- `obj+0x114 = 4953.66` = neutral_temp (CCT), `obj+0x118 = 0.5476` = neutral_tint
  — **EXACTLY** the proven CCM chromaticity inputs (ccm_chromaticity bundle:
  target_cct 4953.66 K, tint 0.5475). So the master color transform is built
  from the SAME proven temp/tint -> xy -> interpolated color_matrix path.
- The worker writes a color-corrected per-camera half-res image (2080x1560) to
  `img+0x70`. Sampled output chroma: **R/G=0.758, B/G=1.005** (vs demosaic-out
  ~0.307/0.41) — i.e. it DE-GREENS / neutralizes the demosaicked image.

### Structure now proven end-to-end
`demosaic (green 0.307) -> per-camera CCM color-apply (de-green -> ~neutral)
 -> fusion -> square-copy x awb_recip(0.582) -> master`

Verification of the structure against Lumen's own master HDR (ground truth):
- **B channel closes exactly**: per-camera-out B/G(1.005) x awb_recip_b(0.629)
  = 0.632 == Lumen master B/G 0.633.
- R channel: per-camera-out R/G(0.758) x awb_recip_r(0.582) = 0.441 vs master
  R/G 0.552 (sampled single camera/region, not the fused global — expected gap).

So Lumen's master is **camera-neutralized (via the color_matrix) then re-cast by
the single square-copy AWB** — NOT the invented inverse-CCM+Bradford chain, and
NOT a display-only color correction. Phoenix currently: (a) omits the CCM
de-green, (b) adds the invented inverse+CAT. Result: 3.6x green + blue collapse.

### Remaining exact receipt (the only open item)
The per-camera CCM APPLICATION FORM (which of M, M^-1, inv(ProPhoto->XYZ).M[^-1],
plus any per-channel curve). Candidate 3x3 forms tested against the captured
(0.307,1,0.41)->(0.758,1,1.005) do not close B/G (all give ~0.38 vs 1.005),
so the per-camera op is NOT a bare 3x3 on the anchor chroma — it is per-camera
(16 distinct module calibrations) and the worker builds spline/curve objects
(0x1acb30/0x1ad390) plus a scale = C/(hi-lo). Next capture: input+output pixel
PAIRS at `0x1ab2d0` for a single identified camera (defeat lazy-eval by breaking
at the materialized consumer), to solve the exact per-pixel operator.

Probes added: tools/lldb_probes/fusion_neutral_apply/{probe,probe2,probe3}.py.

## SESSION 2026-08-02 (cont): per-camera capture + 4-focal verification

Captured input->output at worker 0x1ab2d0 (FusionCacheBayer neutral-color path):
- INPUT descriptor ([rbp-0xc8]) = 4160x3120 SINGLE-CHANNEL Bayer (full sensor).
- OUTPUT (img+0x70) = 2080x1560 RGBA (half-res). So 0x1ab2d0 is a HALF-RES
  demosaic+color reconstruction (distinct from the master DemosaickLightV1 at
  0x2eb560), built from the proven neutral_temp/tint.

4-focal verification of the color-apply OUTPUT chroma (Unit-1):
| focal | out R/G | out B/G | n |
|---|---:|---:|---:|
| 28mm  | 0.9689 | 0.9624 | 971 |
| 35mm  | 0.6404 | 0.7635 | 26672 |
| 70mm  | 0.4958 | 0.4934 | 23114 |
| 150mm | 0.8046 | 0.9398 | 6859 |

=> output chroma is SCENE-DEPENDENT (not a forced neutralize). It is a genuine
colorimetric CCM transform; the 28mm "looks neutral" only because that scene is
near gray-world. The earlier single-scene "master = neutralized x awb" was an
over-read of the gray 28mm case; B-channel still closed exactly for 28mm.

### OPEN DISAMBIGUATION (must resolve before implementing)
Is 0x1ab2d0's half-res color output on the MASTER pixel path, or is it a
preview/stats surface feeding only the neutral-color estimate? Its half-res +
Bayer input suggest a stats/guide role. Next capture: watch whether 0x1ab2d0's
output buffer (img+0x70 data ptr) is read by the final RGBE writer input chain,
vs only by a stats/neutral consumer. If stats-only, the master color transform
is a separate full-res worker still to be located (candidate: the ImageApplyColorMatrix
Stage-12 body 0x2c6390 that loads a 3x3 and loops pixels).

### SOLID, ACTIONABLE NOW (independent of the above)
- Phoenix's Bradford CAT + CCM-inversion + CCM_NEUTRAL + FWDCCM are invented and
  cause the blue collapse; remove them.
- The color transform is CCM-family built from the PROVEN temp/tint -> color_matrix;
  no Bradford CAT, no ad-hoc inversion.

### Worker disambiguation results (2026-08-02)
- 0x2c6390 (Stage-12 ImageApplyColorMatrix, loads 3x3 + loops pixels): breakpoint
  0x2c64f5 does NOT fire during the profile-3 master render (render completes,
  zero hits). => confirmed DISPLAY-only; NOT the master color transform.
- 0x1ab2d0 (fusion neutral path): half-res (2080x1560) Bayer->color; scene-dependent
  output. Preview/stats/guide role, not the full-res master pixel transform.

### Net: the full-res master de-green worker is still unlocated.
Master IS de-greened (R/G 0.307 demosaic -> 0.552 master) at full res, but neither
obvious color worker does it on the master path. Remaining candidates to probe:
the IRAMP/merge color composition (0x3ec770/0x2d7320 square-copy chain applies the
awb x-vector; a color matrix may ride the same IRAMP composition), or a full-res
color stage under the RGBE writer input chain. Next: watch-read the RGBE-writer
input buffer backward to its producer.

## SESSION 2026-08-02 (final consolidation)

### CORRECTION: 0x1ab2d0 IS the master color transform (not a preview)
Writer-custody (bundle_lldb_final_case3_to_hdr_writer_custody) shows the master
10432x7824 descriptor is assembled by compositing case-3 from already-color-
processed src contributors. Per-payload stage order (per_payload bundle) shows
NEITHER the Bayer NOR the Color payload pipeline contains a separate color_matrix
stage. Therefore the ONLY color_matrix application in the whole chain is the
per-camera worker 0x1ab2d0 (built from the proven neutral_temp/tint). Its half-res
(2080x1560) is the fusion's per-camera working resolution; the de-greened per-camera
images are then stitched to the 10432x7824 master. Scene-dependent output (28mm
neutral vs 35mm/70mm greener) is just scene color through a real colorimetric CCM.

So the master de-green = per-camera 0x1ab2d0 CCM(temp/tint), then fuse, then the
single square-copy x awb_recip. This is now internally consistent with every
receipt (B channel closes exactly at 28mm; writer custody; stage-order; temp/tint).

### DONE this session (implemented + built + rendered on the Mac)
phoenix_fuse.cpp: removed the invented color math from the DEFAULT master path.
- Bradford CAT: default OFF (was default ON) -> PHX_CAT=1 for A/B.
- CCM inversion (Mccm_inv=M^-1): default OFF (identity) -> PHX_INVCCM=1 for A/B.
- CCM_NEUTRAL / FWDCCM already gated OFF.
Default master is now CAMERA-LINEAR (sq x awb_recip), no invented color math, and
the blue-collapse is GONE (final B/G 0.013 -> camera-linear 0.206). Build clean,
render prints "master color apply=IDENTITY(camera-linear)".

### LAST RECEIPT to finish the fix
Exact FORM of the per-camera CCM application in 0x1ab2d0 (a fused half-res
demosaic+color+2x-downsample worker; input is full-res Bayer). To solve it:
capture 0x1ab2d0 materialized OUTPUT (RGB) and reconstruct its input by applying
the proven half-res demosaic to the same Bayer, then solve output = form(M, input)
over the well-conditioned full frame -> pick M vs M^-1 vs inv(ProPhoto->XYZ).M[^-1].
Then apply that same colorimetric M (from temp/tint) post-merge in Phoenix before
x awb_recip, and verify vs Lumen master across both bodies x four focals.

---

## 2026-08-02 — RESOLVED: the master is CAMERA-LINEAR. Verified 2 bodies x 4 focals.

### RETRACTION (read this first)
The section above titled "the master de-green = per-camera 0x1ab2d0 CCM(temp/tint)"
is **WRONG and hereby retracted**. It rested on a memory-format misparse: the
`0x1ab2d0` buffers were read as float32-RGBA (16 B/px). They are not.

Proven pixel formats (lldb byte-level dump, `probe4.py` / `probe5.py`):
* fusion **input** Bayer plane  = `uint16`, **2 bytes/pixel**, 4160x3120.
* fusion **color surface** at `r14+0x70` = **float16 RGBA, 8 bytes/pixel**, 2080x1560.

Descriptor layout confirmed unchanged: W `+0x08`, H `+0x0c`, stride-in-PIXELS
`+0x10`, data pointer `+0x20`.

Re-read correctly, the claimed de-green does not exist:
* the surface reads R/G=0.5201 B/G=0.6514 — i.e. **camera-linear**, not 0.758/1.005;
* `post` == `pre` **byte-identical** across the whole 2080x1560 surface, so
  `0x1ab2d0` does not write it at all — `r14+0x70` is an *input*.
The companion `pairs.py` 2x2 block-average methodology is invalidated by the same
bug (it averaged uint16 Bayer bytes reinterpreted as float32 vec4) and is retired.

### The actual finding
**Lumen's profile-3 fmt-3 HDR master carries NO AWB gains and NO colour matrix.**
It is the merged camera-linear radiance field. `awb_rgb` and the 3x3 are real and
are really supplied (CLM-AWB-001 / CLM-CCM-002 both stand) — they are consumed by
the **display** colour pipeline (stage-12 ColorCorrection / `ImageApplyColorMatrix`
`0x2c6390`), which was already proven never to fire on a master render.

Three independent receipts:

1. **Memory.** Per-channel linear fit of the RGBA16F surface against its own Bayer
   source gives slopes **0.00216156 / 0.00219204 / 0.00221480** — equal within
   2.5%. Folding `awb_rgb=(0.582, 1, 0.629)` in would spread them ~40%.
2. **The master itself.** `u1_28_lumen.hdr` (10432x7824) measures mean
   R=0.134371 G=0.243388 B=0.154058 -> R/G=0.5521 B/G=0.6330, matching the
   camera-linear surface (G=0.2449) in chroma **and** absolute radiometric scale
   (0.6% on G).
3. **Form sweep** (`forms.py`) vs the master: identity 4.9%/2.2%; one AWB
   44.7%/35.7%; raw/g 63.3%/62.4%; M.raw 5.5%/43.3%; M.(raw*g) 27.9%/95.1%;
   M^-1.(raw*g) 71.8%/0.9%; PP^-1.M.(raw*g) 60.9%/95.4%. Identity wins outright.

Bonus, proven live at demosaic driver `0x2eb560`: the colour-params struct is
`[0..2]` awb triplet, `[3,4]` scene xy, `[5..13]` 3x3 M, `[14,15]` ProPhoto D50
white. M has row sums `[0.96422, 1.0, 0.82521]` and `PP^-1.M` has row sums exactly
`[1,1,1]`, so **M = ProPhoto_from_XYZ . CCM** — the display-path camera->ProPhoto
transform, not a master-path one.

### Implementation
`phoenix/tools/phoenix_fuse.cpp`: AWB default flipped **OFF** for the master path
(`const bool no_awb = (std::getenv("PHX_AWB") == nullptr);`), receipt comment
inline. `PHX_AWB=1` restores the legacy double-apply for A/B only. Bradford CAT
and CCM inversion remain default-OFF from the prior session. Master colour apply
is IDENTITY. Built clean.

### VERIFICATION — both bodies x four focals (the last outstanding receipt)
Corpus: U1 28mm `L16_02130`, U1 35mm `L16_03041`, U1 70mm `L16_03434`,
U1 150mm `L16_02285`, U2 35mm `L16_01956`. Each rendered twice: Lumen
`lri_process --profile 3 --export-fmt 3` and the rebuilt `phoenix_fuse`.
Artefacts in `runs/verify_master/` (`verify.json`, `spatial.json`).

Whole-frame means, plus the counterfactual "AWB had been applied" chroma:

| shot | lumen R/G | phx R/G | err | lumen B/G | phx B/G | err | awb_rgb | AWB-applied err |
|---|---|---|---|---|---|---|---|---|
| u1_28  | 0.5521 | 0.5248 | 4.9% | 0.6330 | 0.6079 | 4.0% | 0.58213,1,0.62939 | 44.7% / 39.6% |
| u1_35  | 0.5108 | 0.6237 | 22.1% | 0.7247 | 0.8212 | 13.3% | 0.58170,1,0.62420 | 29.0% / 29.3% |
| u1_70  | 0.5078 | 0.5165 | 1.7% | 0.5506 | 0.5543 | 0.7% | 0.55163,1,0.63166 | 43.9% / 36.4% |
| u1_150 | 0.4948 | 0.4962 | 0.3% | 0.6862 | 0.6858 | 0.1% | 0.56701,1,0.62471 | 43.1% / 37.6% |
| u2_35  | 0.5660 | 0.5699 | 0.7% | 0.5682 | 0.5063 | 10.9% | 0.56440,1,0.58370 | 43.2% / 48.0% |

AWB-free beats AWB-applied on **every shot, in both chroma axes, by 4-100x**.

Both masters are 4:3, so `spatial.py` box-downsamples each to a common 128x96 grid
and compares tile-by-tile. This separates colour error from framing/weighting:

| shot | phx/lumen tile ratio R / G / B | centre R/G err | centre B/G err | edge R/G err | edge B/G err |
|---|---|---|---|---|---|
| u1_28  | 0.7377 / 0.7488 / 0.7077 | +2.5% | +0.7% | -6.0% | -4.5% |
| u1_35  | 0.7101 / 0.7008 / 0.7288 | +0.8% | +2.0% | -1.6% | +8.0% |
| u1_70  | 1.3844 / 1.3711 / 1.3760 | +1.1% | +1.0% | +0.5% | +0.8% |
| u1_150 | 1.0508 / 1.0452 / 1.0452 | +0.9% | +0.0% | +0.2% | +0.0% |
| u2_35  | 0.8456 / 0.8240 / 0.7237 | -3.7% | -11.0% | +19.7% | -4.9% |

Two things fall out of this table:

* **The per-tile R, G, B ratios are equal to each other on every shot** (u1_70:
  1.3844/1.3711/1.3760; u1_150: 1.0508/1.0452/1.0452). The remaining Phoenix-vs-
  Lumen difference is therefore **achromatic** — a per-shot exposure/normalisation
  scale, not a colour error. The colour question is closed.
* **Centre chroma agrees to ~1-2.5% on 4 of 5 shots.** The u1_35 whole-frame 22%
  "error" was a spatial-weighting artefact: centre agrees to 0.8%/2.0%. Error
  grows monotonically toward the frame edge, which is the signature of lens
  shading / colour-shading, not of a missing matrix.

### Remaining open items (both now well-characterised, neither is colour)
1. **Per-shot achromatic scale.** phx/lumen mean-G ratio is 0.753 / 0.651 / 1.442 /
   1.072 / 0.762 across the corpus — shot-dependent, so it is a normalisation term
   Phoenix derives differently (exposure/gain normalisation or contributor
   weighting), not a constant. Next: trace Lumen's master-write scale factor.
2. **Lens / colour shading.** Centre-to-edge chroma drift up to ~6% (u1_28) and
   ~20% (u2_35, a very dark frame, mean G 0.064). Next: capture Lumen's per-module
   shading surface.

Also still to do: strip the temporary `PHX_DBG` instrumentation from
`phoenix_fuse.cpp` (~line 2701).

Tooling added under `tools/lldb_probes/fusion_neutral_apply/`: `fmt.py`,
`probe4.py`, `probe5.py`, `probe6.py`, `an5.py`, `an6.py`, `forms.py`,
`hdrstat.py`, `sweep.sh`, `getawb.sh`, `verify.py`, `spatial.py`.

### Addendum — characterising open item 1 (the per-shot achromatic scale)

Four candidate explanations tested and settled, so the next session starts from
facts rather than guesses (`align.py`, `transfer.py`, `modexp.sh`):

* **Not framing.** `align.py` searches a centre-zoom factor z in [0.30, 1.60]
  maximising log-luminance NCC between the two masters. Every shot peaks at
  **z = 1.00** with NCC 0.9964 / 0.9809 / 0.9375 / 0.9991 / 0.9632. The two
  masters cover the identical field of view, so the measured gain is real.
  Aligned median gains: 0.7418 / 0.6983 / 1.3713 / 1.0473 / 0.8260.
* **Not a tone curve.** `transfer.py` bins aligned tiles into lumen-luminance
  deciles. The phx/lumen ratio is **flat across deciles** on every shot (u1_70:
  1.13/1.29/1.45/1.40/1.40/1.35/1.40/1.50/1.40/1.35; u1_150: 1.07/1.03/1.02/
  1.01/1.03/1.05/1.04/1.04/1.07/1.12). Only the top decile droops on the two
  brightest wides (u1_28 0.685, u1_35 0.526) — that is Lumen's separate highlight
  shoulder, already on the ledger, not the main gain.
* **Not the capture normalisation.** `scale = (integration_time_ns*image_gain) /
  (sensor_exposure*analog_gain)` measures **2.0001 / 2.0110 / 2.0065 / 1.9966**
  across the corpus — essentially constant, so it cannot produce a 0.70..1.37
  spread. TRUTH 3.0.314 (cap_norm is display-only) stands.
* **Not absolute exposure.** The three wide shots span a ~100x exposure range
  (anchor exp*gain 1.12e7 / 1.30e6 / 1.55e8) yet cluster at k = 0.74 / 0.70 /
  0.83. The master is raw-referred, not radiance-referred.

New structural fact from the header dump (`modexp.sh` + `lri_field_inspect.py`,
float bit-patterns decoded): in **every** shot the contributor modules are
exposed almost exactly **2x** the anchor —

| shot | anchor exp*gain | contributor exp*gain | ratio |
|---|---|---|---|
| u1_28  | 1.1239e7 (id0, g=1.0)     | 2.1961e7 (id4/6/8/9, g=1.5)  | 1.954 |
| u1_35  | 1.3013e6 (id0, g=1.0)     | 2.6116e6 (g=1.0)             | 2.007 |
| u1_70  | 0.8815e6 (id8/B4, g=1.0)  | 1.7623e6 (id6/9/14, g=1.0)   | 1.999 |
| u1_150 | 0.2559e6 (id8/B4, g=1.0)  | 0.5095e6 (id6/9/14, g=1.0)   | 1.995 |
| u2_35  | 1.5485e8 (id0, g=3.875)   | 3.0963e8 (g=7.75)            | 1.999 |

k also tracks the merge accumulation density loosely (wide 0.95-0.96
accumulations/block -> k<1; tele 1.07 -> k>1), which points at **contributor
exposure equalisation inside the merge** as the prime suspect: Phoenix merges
contributors that are physically 2x-exposed relative to the anchor, so the
merged level depends on how much of the frame a contributor actually covered.
Lumen presumably equalises first. That is the hypothesis to test.

**Next receipt to capture (lldb, not inference):** the scale Lumen applies to a
contributor tile as it enters the merge accumulator, and the final scale on the
master-writer input buffer. Compare per shot against the anchor/contributor
exposure ratio above.

---

## 2026-08-02 — ROOT CAUSE FOUND: lens shading was selecting the wrong calibration record

Open item 1 (per-shot achromatic gain deficit) and the tele over-brightness item
are both closed by a single defect, and the defect was already proven by Codex.
No new derivation was required; the fix is the bundle applied verbatim.

### The law (Codex, already proven)

Bundle:
`docs/evidence/bundle_static_runtime_create_stereo_color_normalization_vignetting_two_body.md`

> "The selected public calibration is vector entry
> `LightHeader.module_calibration[camera_key]`; its own public `camera_id` is
> not assumed to equal that vector index."

Receipts in that bundle, all bit exact over 196,608 RGB lanes:

| unit / camera | camera key | selected record `camera_id` | models | position field |
|---|---|---|---|---|
| Unit-1 A1 | 0 | 12 | 1 | `lens_position=10640` |
| Unit-2 A1 | 0 | 4  | 1 | `lens_position=12144` |
| Unit-1 movable | 6 | 9 | 4 | `mirror_position=400` |

Pinned installed ranges: `0x350ff0..0x3510c3` (normalization wrapper),
`0x352ce0..0x352ec4` (executor construction), `0x353330..0x35380f`
(normalization row worker), `0x108080..0x10827e` (`vec4x32f,true` vignetting
row worker). Thunk `0x340a30 -> 0x350ff0`; vtable slots
`0x65ae40/+0x30 = 0x340a30` and `0x65ca18/+0x30 = 0x345d50`.

### What Phoenix was doing

`extractCamGeom` keyed the vignetting grid off the merged record's own
`camera_id`. The LRI's field-13 vignetting fragment group is *permuted*, so
camera key 0 was being handed the grid belonging to camera_id 0 — which sits at
wire index 1, not 0.

### The fragment-group ordering law (new receipt, `[cblk]` dump)

`dumpCalibrationVectorIds` was extended to print every LELR block's field-13
records with the sub-message each fragment carries (C = color f2,
G = geometry f3, V = vignetting f4). On `L16_02130` (Unit-1 28mm):

```
[cblk] block  4 n=16: 0G 1G 2G 3G 4G 5G 6G 7G 8G 9G 10G 11G 12G 13G 14G 15G
[cblk] block  5 n=16: 12V 0V 4V 1V 8V 5V 9V 13V 2V 6V 14V 15V 10V 7V 3V 11V
[cblk] block  7 n=42: 0C 0C 0C 5C 5C 5C 2C 2C 2C 6C 6C 6C 3C 3C 3C 7C 7C 7C
                      4C 4C 4C 8C 8C 8C 13C 13C 13C 9C 9C 9C 14C 14C 14C
                      10C 10C 10C 11C 11C 11C 12C 12C 12C
```

Consequences, each decided by the receipt rather than by extending the §5.6
wording speculatively:

- **Geometry** is in plain `camera_id` order, so positional == camera_id.
  Phoenix's geometry lookup was already correct; unchanged.
- **Vignetting** is permuted, so positional selection is observable and matters.
  Fixed.
- **Color** carries 42 fragments over only **14** distinct camera_ids (ids 1 and
  15 — the two mono cameras — are absent). Fourteen records cannot fill sixteen
  positional banks, so the CCM lookup must be camera_id-keyed. Phoenix's CCM
  path is correct; **no change made**. This was a speculative edit I was about to
  make and the dump killed it.

Also measured: `[mcorder] merged camera_ids: 0 1 2 3 ... 15`. Phoenix's
post-merge `module_calibration` order (from
`mergeFactoryCalibrationByCameraId`, first-appearance order over ~74 fragments)
is the identity permutation, so `FactoryModuleCalibration::vector_index` is
**not** the 01 §5.6 positional selector. The selector lives in the raw
vignetting fragment group's wire order, which is why
`findCalibrationVignettingVector` (which walks the un-merged blocks) is the
correct source. `engine/lri/captured_image.cpp` still carries a comment claiming
`module_calibration_index` is positional while the code keys by camera_id; that
member is not consumed by the fixed path, but the inconsistency is now
understood and should be reconciled.

### Second fix: grid spacing is `W/16`, not `(W-1)/16`

The same bundle pins the sampling domain:

> "The post-demosaic lens worker samples the shaped `17x13` profile in the fixed
> half-resolution domain `W=2080`, `H=1560`, so both grid spacings are exactly
> `130`. This domain is selected by the exact replay; the full-sensor
> `4160x3120`/spacing-260 alternative does not describe the captured worker."

`2080/16 = 1560/12 = 130`. Scaled to Phoenix's full-res `4160x3120` plane that
is `260`, which also matches the independently bit-exact
`merge::monoVignettingPlane` builder (`step = floor(W/16)`). Phoenix's colour
path had been using `(kW-1)/(width-1)`, i.e. spacing `259.9375`, which over-ran
the last cell. Now `(kW-1)/width`.

### Receipt: the corrected grid is bit-identical to Lumen's own operand

```
[vign] cam 0 mean=1.753298 min=1.000000 max=3.819754
```

Lumen's captured MonoFusion `auxiliary_full.f32le` operand:
mean `1.753298`, min `1.000000`, max `3.819754`. Exact match.

Before the fix, camera key 0 received wire index 1, whose grid mean is
`1.791445`. Camera 8 is the clearest illustration: it had been receiving a
28mm-module grid (mean `1.842372`, max `3.69`) and now receives its true tele
grid (mean `1.238666`, max `1.78`) — which is precisely why the tele shots were
grossly over-bright.

This also retires the "positional A1=0 / A2=1" rule in MonoFusion as a quirk.
It is the same law: the anchor's camera key is 0 and the mono partner's is 1.

### Whole-corpus result (Ohta-luma achromatic ratio, lumen / phoenix)

Weights wr=0.2155500054359436, wg=0.43230700492858887, wb=0.35214298963546753.
Decoded with `tools/lldb_probes/fusion_neutral_apply/hdrmean.py`.

| shot | module | before | after |
|---|---|---|---|
| `L16_02130` u1 28mm  | A1 | 1.3538 | **1.0113** |
| `L16_03041` u1 35mm  | A1 | 1.4323 | 1.1644 |
| `L16_03434` u1 70mm  | tele | 0.6905 | **1.0103** |
| `L16_02285` u1 150mm | tele | 0.9329 | **1.0093** |
| `L16_01956` u2 35mm  | A1 | 1.3489 | **0.9714** |

Raw channel means after the fix (phoenix / lumen):

| shot | R | G | B |
|---|---|---|---|
| u1_28  | 0.125426 / 0.134371 | 0.241095 / 0.243388 | 0.156367 / 0.154058 |
| u1_35  | 0.165816 / 0.170180 | 0.266237 / 0.333162 | 0.219748 / 0.241430 |
| u1_70  | 0.103105 / 0.103357 | 0.200361 / 0.203522 | 0.111738 / 0.112054 |
| u1_150 | 0.116317 / 0.117056 | 0.234357 / 0.236589 | 0.160697 / 0.162347 |
| u2_35  | 0.037106 / 0.036250 | 0.065820 / 0.064048 | 0.037794 / 0.036391 |

Three of the five shots now sit at `1.0093 – 1.0113`, a tight cluster that
points at one remaining common ~1% factor rather than five separate errors.
Unit-2 overshoots slightly (`0.9714`). Unit-1 35mm is the sole real outlier.

### Green-channel progression on u1_28 (Phoenix G mean, Lumen = 0.243388)

| state | G mean |
|---|---|
| before the mode-0 source-operand fix | 0.214873 |
| after the mode-0 source-operand fix | 0.229460 |
| after the positional-calibration + spacing fix | **0.241095** |

### Carried-forward receipts from the prior session

- **Target identity.** Phoenix's MonoFusion *target* tile is the same image as
  Lumen's captured target tile (NCC ≈ 1 after alignment); the disagreement was
  never a framing or registration error.
- **`vign_a1` is bit exact.** `|phx_vign_a1 - auxiliary_full|` max = `0.0` over
  the full plane, confirming the A1 grid Phoenix builds is the operand Lumen
  feeds MonoFusion.
- **`source0` formula.** Lumen's mode-0 source operand is
  `42 + (raw_A2 - 42) * mono_mult * vign_A2`, reproduced bit exact.
  u1_28: `Q = 0.511815608`, `reference_scale = 4.52963924`,
  `mono_mult = 0.220768124`.
  u1_35: `q = 0.49920249`, `reference_scale = 4.64408731`,
  `mono_mult = 0.215327561`.
  `reference_scale = R / Q` with `R = lri::kSensorAr1335MonoResponse = 2.31834`.
- A residual ~2.5% per-pixel scatter between `42 + sca*V_A1` and Lumen's
  captured target tile is still unexplained.

### Remaining open: `L16_03041` (Unit-1 35mm), achromatic 1.1644

Green-specific: G ratio `1.2514`, R `1.0263`, B `1.0987`. It splits in two:

- `PHX_NOMONO=1` gives R `0.186516`, G `0.292917`, B `0.244209` → achromatic
  `1.0510`. So **MonoFusion costs ~10.8%** on this shot and a residual chroma
  tilt costs ~5%.
- `[mono] DN means: target=306.9340 mono=184.0075 fused=282.2812
  (fused/target=0.919680)`. The mono source is 40% *dimmer* than the target.
  For comparison u1_28: `target=227.3043 mono=243.0229 fused=226.0186`, ratio
  `0.994344`. The mono/target relationship differs by ~2.3x between the two
  shots, which the scene spectrum alone cannot plausibly explain.
- Exposure bookkeeping is correct: `[nrg] ref cam0 energy=1.30133e+06` against
  ≈`2.61e6` for every other camera, so `q = 1301331/2606820 = 0.499202` matches
  the reported `q=0.49920249`. The anchor really is at half exposure.
- `[lvl] cam 7 pre-vign R=543.18 G=710.22 B=668.72` — 3–6x brighter and far
  less saturated than every sibling in this capture. Suspicious.
- The chroma tilt direction is **not** consistent across shots (u1_28 has
  Phoenix R too low at `1.071`; u1_35 has Phoenix R too high at `0.912`), so it
  is not a fixed CCM error.

**Next receipt to capture (lldb, not inference):** run the existing mode-0
operand probe against `L16_03041` to produce
`runs/prefusion_monofusion_mode0_tile/unit1_35mm/` — Lumen's own
`source0_full.f32le`, `auxiliary_full.f32le` and `target_tile.f32le` — and
compare against Phoenix's `/tmp/phx_*.f32le` dumps for the same shot, exactly as
was done for `unit1_28mm/`. Do not infer why `mono=184.0075` sits 40% below
`target=306.9340`; measure what Lumen actually hands the fuser.


---

# 2026-08-02 — MonoFusion patch noise: `mu` is the AUXILIARY plane mean, not the patch mean

## Summary

Two MonoFusion questions were adjudicated by direct lldb measurement of Lumen.
One (the Wiener blend direction) confirmed the installed Phoenix code and
resolved an apparent contradiction with the byte-pinned Codex bundle. The other
found and fixed a real ~250x defect in Phoenix's patch-noise variance `V`,
which was the dominant cause of the `u1_35` achromatic outlier.

## 1. Wiener blend direction — CONFIRMED, no change

`tools/lldb_probes/prefusion_monofusion_mode0_tile/wfit.py` fits both candidate
Wiener forms against Lumen's own captured pre-Wiener (`patch_source_coeff_pre`),
post-Wiener (`patch_source_coeff_post`) and target (`patch_target_coeff`)
coefficient buffers, by solving for the measured source weight
`w = (F - T) / (S - T)` and asking which form makes `Lambda = lambda_k / F_k`
a per-patch constant.

```
F_k table: n=256  F[0]=2.112103 F[1]=1.312500 min=0.562500 max=8.650076
well-conditioned coefficients: 255 / 256
w: min=0.041165 max=0.999995 median=0.993158
spearman(w, d2) = -0.9548

form A (w = d2/(d2+lam), source weight RISES with disagreement)
  Lambda = lam_k/F_k : mean=819.158216 std=12950.959517  relspread=15.8
  reconstruct F: maxabs=119.876 rms=8.23147  (|F|max=887.6022)

form B (w = lam/(lam+d2), source weight FALLS with disagreement)
  Lambda = lam_k/F_k : mean=382.937290 std=0.543639  relspread=0.00142
  reconstruct F: maxabs=0.0141148 rms=0.000883616  (|F|max=887.6022)
```

Form B wins by four orders of magnitude in reconstruction error and by four in
`Lambda` spread. `spearman(w, d2) = -0.955` says the same thing directly: the
measured source weight *falls* as source/target disagreement rises.

The bundle
`bundle_static_runtime_prefusion_monofusion_wavelet_formula_two_body.md` reads
`w_k = delta2_k/(delta2_k + lambda_k); T_k = (1-w_k)*T_k + w_k*S_k`, which
*looks* transposed relative to Phoenix's line. It is not. The bundle's `T_k` is
the buffer that is UPDATED IN PLACE, and Lumen updates the SOURCE patch buffer
— proven independently by `inv2d(patch_source_coeff_post) ==
patch_source_spatial_post` to 4.2e-05 while `inv2d(patch_source_coeff_pre)`
misses by 11.25. So the bundle's `T` is Phoenix's `S` and vice versa;
substituting gives exactly the installed line. **Codex is not contradicted, and
Phoenix is not changed.** A receipt block recording this reconciliation was
added above the blend line in `engine/merge/monofusion.cpp`.

## 2. Patch-noise `mu` — REAL DEFECT, FIXED

### What was measured

Helper `0x18e940` (called from the mode-0 reducer at `0x1a464d`) was decoded
from `libcp.dylib` disassembly as

```
float helper(view_t *rdi, const float *rsi, float mu /*xmm0*/)
    rsi[0]=a  rsi[1]=b  rsi[2]=black  rsi[3]=white
```

`mu` **arrives as an argument**. It is not computed from the target patch. The
caller computes it at `0x1a4515..0x1a4549`.

A three-breakpoint probe
(`tools/lldb_probes/prefusion_monofusion_mode0_tile/noise_probe.py`, driven by
`noise_unit1_35mm.lldb`) captured, per call: the incoming `mu`, the `{a,b,black,
white}` struct, the target view descriptor and its pixels, and the *source
window descriptor still live at `rbp-0x1600`* (breakpoint `0x1a4524`, placed
before the view destructor at `0x1a4533` zeroes the slot), plus the return value
(`0x1a4652`). Records are keyed by thread id — the reducer is multithreaded and
a single pending slot mis-pairs entry with return.

Receipts, `runs/prefusion_monofusion_mode0_tile/unit1_35mm/noise_helper.json`,
24 hits:

- `max|muview_mean - mu| = 1.05e-06` over 24 hits, 23 distinct window pointers.
- The window lives on a **4160x3120 float map, stride 4160, values in
  [1.0, 3.82]**. `4160*3120*4 = 51,916,800 B` — exactly the size of the captured
  `auxiliary_full.f32le`, whose range is min 1.000000 / max 3.819754. That is
  the AUXILIARY / vignetting gain plane, which `tools/phoenix_fuse.cpp` already
  proves equal to Phoenix's `vign_a1` with `max diff 0.0`.
- Window x-offsets are all multiples of 8 (the patch lattice) and window `w,h`
  equals the target view's `w,h` — so it is the UNSHIFTED patch rect, clipped to
  frame bounds. The flow displacement applies only to the source gather.
- Windows are genuinely CLIPPED, not edge-replicated: observed `w,h` of
  8x8, 12x8, 14x8, 16x8, 16x16, with `P = w*h`.
- Measured `a = 2.2371266823029146e-05`, `b = -9.366336826133193e-07`, exactly
  Phoenix's `a_s = mono_noise.a/(kR*kC)`, `b_s = mono_noise.b/(kR*kC)`. **The
  `(a,b)` scaling Phoenix had was already right** — the bundle left it as
  "scaled panchromatic model" without pinning it numerically, so it was
  genuinely open, and it is now closed by measurement.
- `black = 42.0`, `white = 1023.0`. The `a*z+b` term clamped to `1e-5` in all 24
  patches.

`ncheck.py` re-derives `V` from the captured inputs:

```
H = sqrt(P / sum_j 1/(I_j + 0.1)^2)   over the CLIPPED target window
z = max(black/white, (black + (H-black)/mu)/white)
V = (white*mu)^2 * max(1e-5, a*z + b)
```

> `24/24 ratio = 1.00000`, `mismatches (>0.2%): 0`

Independent cross-check: hit 3 returned `V = 140.52275`; `wfit.py`'s Wiener fit
on the same tile gives `Lambda = 382.937 -> V = Lambda/kNoiseScale = 140.508`.
Two unrelated measurements agree to 1e-4 relative.

### The bug

The Codex bundle's prose calls `mu` the "patch arithmetic mean". That is a
**mislabel**, and Phoenix implemented the prose: `patchNoiseV` used the target
patch mean (~58) where Lumen uses the vignette window mean (~3.66). Phoenix's
`V` was therefore ~250x too large. Since `lambda_k = V * noise_scale * F_k` and
the source weight is `lambda/(lambda+d2)`, an inflated `V` drives the source
weight toward 1 — Phoenix was pulling the mono source in far harder than Lumen
does. Symptom: `[mono] fused/target = 0.941829` against Lumen's tile-level
`out/target = 0.999937`.

Bonus: the 64-byte struct at `rsi` also carries `[8] = 0.6330776214599609`
(`kAlpha`), `[9] = 0.36692237854003906` (`1-kAlpha`), `[10] = 1.0` (`kN`) and
`[11] = 0.23229040205478668` — the previously unexplained
`parameters.bin[13]` / `relative_brightness` lead, now located in a concrete
runtime struct.

### The fix

- `engine/merge/monofusion.cpp`: `patchNoiseV` now takes the target image, the
  vignetting plane and the clipped window bounds; `mu` is the vignette mean and
  `H` runs over the same clipped rect with `P = w*h`. The old form is retained
  as `patchNoiseVPatchMean` for callers that supply no plane.
- `engine/merge/monofusion.h`: `monoFuseLuma` gained a trailing
  `const std::vector<float>* vign = nullptr`.
- `tools/phoenix_fuse.cpp`: passes `&vign_a1` — the plane proven bit exact
  against Lumen's captured `auxiliary_full.f32le`.

### Result

`[mono] fused/target`, before and after:

```
shot     before     after      Lumen tile-level reference
u1_28    (n/a)      1.000010   0.999937
u1_35    0.941829   0.999920   0.999937
u2_35    (n/a)      0.999999   0.999937
```

Ohta-luma achromatic ratio `lumen/phoenix` over the 5-shot corpus
(`hdrmean.py`, nonzero-green-masked channel means):

```
shot     phoenix R/G/B                lumen R/G/B                  achro    R       G       B
u1_28    0.126281 0.242798 0.157731   0.134371 0.243388 0.154058   1.0038  1.0641  1.0024  0.9767
u1_35    0.186617 0.292824 0.244145   0.170180 0.333162 0.241430   1.0512  0.9119  1.1378  0.9889
u1_70    0.103105 0.200361 0.111738   0.103357 0.203522 0.112054   1.0103  1.0024  1.0158  1.0028
u1_150   0.116317 0.234357 0.160697   0.117056 0.236589 0.162347   1.0093  1.0064  1.0095  1.0103
u2_35    0.038003 0.067515 0.039098   0.036317 0.064167 0.036459   0.9464  0.9556  0.9504  0.9325
```

Progression of the achromatic ratio across the last three states:

```
shot     pre-Wiener-audit   post-Wiener-audit   post-mu-fix (now)
u1_28    1.0113             1.0242              1.0038
u1_35    1.1644             1.1244              1.0512
u1_70    1.0103             1.0103              1.0103
u1_150   1.0093             1.0093              1.0093
u2_35    0.9714             0.9718              0.9464
```

`u1_70` and `u1_150` are unchanged because those captures carry no mono partner
— their logs emit no `[mono]` lines at all, so the change provably cannot touch
them. That is a useful control: the two shots that moved are exactly the two
that run MonoFusion, plus `u2_35`.

### Honest accounting of the `u2_35` regression

`u2_35` moved from `0.9718` to `0.9464`, i.e. further from 1.0. The change is
proven correct against Lumen's own bytes (24/24, ratio 1.00000), so it stays;
what this exposes is that `u2_35` carried a **compensating** error. Phoenix was
over-weighting the (darker) mono source, which was pulling `u2_35` down toward
Lumen's level and masking a separate ~5% brightness excess. Removing the mono
over-weight unmasked it. That excess is now the leading `u2_35` item.

## Remaining open items after this fix

1. **`u1_35` chroma deficit — now the largest single error.** Phoenix's
   camera-linear `R/G = 0.637` against `0.522` (`u1_28`), `0.514` (`u1_70`),
   `0.498` (`u1_150`); Lumen's `u1_35` output `R/G` is `0.5108`, in family with
   its siblings. So Phoenix's `u1_35` G is ~14% deficient (and R ~9% hot)
   *before* MonoFusion — it is visible with `PHX_NOMONO=1` and is therefore not
   a fusion defect. This is a merge/demosaic/per-camera-gain question, not a
   CCM one: the tilt direction is not consistent across shots.
2. **`u2_35` ~5% brightness excess**, unmasked as described above.
3. The shared ~1% achromatic deficit on `u1_70`/`u1_150` (`1.0103`, `1.0093`),
   unchanged and untouched by MonoFusion.
4. Edge-window semantics are now correct for `mu`/`H`, but the patch gather
   itself is still edge-replicated in Phoenix. Lumen clips. This affects only
   the frame border and is second-order against the items above.
