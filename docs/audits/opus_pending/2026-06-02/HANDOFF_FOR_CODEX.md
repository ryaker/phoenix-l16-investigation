# Opus quarantine → Codex handoff (2026-06-03, waves 1–7)

**Everything here is `NEEDS_CODEX_VALIDATION`** — quarantine, weak-labeled, never promoted to canonical.
Method: static disasm + deterministic LRI byte-parse, via WSJF finder+independent-verifier Workflow
fan-outs (7 waves). Authority = the ledger; this is input for your validation pass, not truth.

## What is now mapped (read the per-lane packets; this is just the map)

### Merge mechanism (#1 blocker CLM-PREFUSION-002) — `MERGE_MECHANISM_SYNTHESIS.md`
Two-stage split:
- **`0x3661b0` = terminal pixel N→1 merge** (OBSERVED): contributors from the source-image vector,
  index-validity gate (`0x36930f` `0x80000000`), motion-compensated, **`1/Σscore`-normalized SOFT
  weighted average** (`rcpss 0x36a938`; no maxps/blendvps ⇒ not hard select) → tile → alpha-blend into
  output image `[arg0+0x38]`. Score `0x36cde0 = sqrt(hmin·hmin)`, **multi-scale wavelet-domain SSIM-class**
  (4 dyadic scales, raw K=0.01, affine remap `(ssim−0.8)/0.19`). lane-3 `=recip·0.2` → guided
  detail-transfer; 3×3 color matrix from `__bss 0x671980`.
- **`0x216f60` = geometry/warp-record builder** (CANDIDATE), no pixels. **Its consumer + the IRAMP source/
  warp producer are NOT `0x216f60`** — your committed `lldb_src2_descriptor_origin_four_zoom.md` resolves
  the producer to **FusionCacheBayer `0x406a10`/`0x3ed2e0`**.
- `src1`(cache+0x238)/`src2`(cache+0x248) are **geometry descriptors** (anchor frame + ROI/margin-zero
  box), NOT the image buffers being merged. Acceptance (`0x218b30`) = statistics reducer; `<8` positive
  pairs → clean merge skip.

### LRI calibration origins (#2 blocker, input side) — `laneB2_lri_calibration_origins/` + `lane-b2` memory
All per-camera calibration is **LRI-resident** (clean-room Rule #0 OK):
- **Block 3** = per-camera intrinsics: K matrix `f3.2.2.1` has per-camera **fx** → **5+5+6 tiers**
  (28/70/150mm); distortion `f3.3.1.3` = **Brown-Conrady pure-radial** (p1=p2=0 all 16 cams) + 101-pt/30-pt
  LUTs (poly + LUT are COMPLEMENTARY, poly valid only [0,~1.14]). All 16 cams have full distortion (the
  "8/8 simple-vs-full" split was an artifact).
- **Block 6** = per-camera color/shading: 14 cams × 3 illuminant variants (`f2.f1∈{0,2,6}`; ids **1,15
  excluded** — one per outermost tier). `f2.2` = white-point CCM (invariant row-sums [0.9642,1.0,0.8252]);
  `f2.3` = second per-camera matrix; `f2.6` = 24 ColorChecker-like triplets; **`f2.8` (1472B variant only)
  = per-camera per-channel SPECTRAL SENSITIVITY CURVES (3ch × 76 float32, 380–755nm, R@595/G@525/B@470)**.
- **Corpus-validated (4-zoom × 2-unit):** spectral curves, distortion, excluded-pair {1,15} all hold;
  calibration is per-body-constant (identical across a unit's 4 zooms) and Unit-1 ≠ Unit-2.
- **Clean-room LRI input map (wave 8):** per-capture **AWB/WB gains = Block 8 `B8.19.15`** =
  [R 1.7178, G 1.0, G 1.0, B 1.5888] (Bayer RGGB, global, distinct from Block-6 per-camera scalars/CCM; no
  standalone CCT). Full **11-block inventory**: Block 0+2 = raw sensor planes in the block *body* (pre
  `msg_offset`; blk0 cams {0,4,6,8,9}, blk2 {1,2,3,5,7} = 10 fired cams @28mm); Block 4 = per-module cal,
  Block 5 = vignetting/falloff. Block 0 LightHeader: f1/f2 = GUID (not timestamps), f3 = date submsg,
  f5 = reference camera, f18 = hw_info; per-camera exposure/gain/focus (no plain EXIF scalars).

### Runtime results (I ran renders — Codex offline, sequential, 28mm)
- **`__bss 0x671980` post-merge "color matrix" is a FIXED CONSTANT** = Ohta/PCA **I1I2I3** orthonormal
  decorrelation basis (`[1/√3,1/√3,1/√3]`,`[1/√2,0,−1/√2]`,`[1/√6,−2/√6,1/√6]`). Write-watchpoint: ZERO
  render-time writes; written once at static-init from a literal pool. **Clean-room: reimplement from
  formula (published transform), NOT per-LRI calibration.** (Resolves handoff residual #3.)
- AWB-gains consumption probe (does libcp read `B8.19.15` in the pixel path) — RUNNING.

## Verify-before-trust catches (so you know what was corrected, not just asserted)
1. A finder fabricated a **"zero rcpss" negative** — rcpss exists at `0x36a938` (re-extracted).
2. A finder fabricated **specific SHA-256 digits** for the spectral blobs — verifier recomputed the real
   ones; the per-body-constant / U1≠U2 conclusion held, digits didn't.
3. A **`reliable=True` result was still WRONG** (finder+verifier shared a wrong-field blind spot): both read
   `f3.2.1` (per-scale const 818) as "fx" and falsely "refuted" the 5+5+6 tiers. Orchestrator re-parsed the
   K matrix `f3.2.2.1` (real per-camera fx) and corrected it. ⇒ when two "reliable" results contradict,
   independently re-extract on a different path.

## Residual unknowns — RUNTIME (your domain), prioritized for your validation pass
1. **Producer link** — already crossed in your committed evidence (FusionCacheBayer); just confirm it feeds
   the IRAMP `+0x258/+0x270` vectors.
2. `0x216f60` geometry-record consumer + record-count == fired-camera N (your `0x23faf0` thread).
3. ~~`__bss 0x671980` color matrix constant-vs-computed~~ — **RESOLVED by runtime probe: fixed I1I2I3
   constant (see Runtime results above).**
4. Score final-operand certification at `0x36e511` (low marginal; static structure already strong).
5. `0x218e20` gate consumer behind `__const 0x6580e0` indirect dispatch.
6. Illuminant enum `f2.f1∈{0,2,6}` → which illuminant (A/D50/D65); libcp's actual undistort eval order
   (poly vs LUT); Block-8 AWB gains (being mapped next, LRI-side).

## Boundary
The high-value statically/LRI-tractable surface for both blockers is comprehensively covered. Remaining
merge-core unknowns are all runtime (your domain); remaining LRI items are lower-marginal or runtime. The
spectral-curve + full per-camera-calibration map is a substantial clean-room asset ready for your
validation when you return (2026-06-07).
