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
  output image `[arg0+0x38]`. Score `0x36cde0 = sqrt(factor1·factor2)` — **two factors now decoded**
  (`laneA_prefusion_reducer_static/score_kernel_36cde0_two_factors.md`): **factor1 = single-scale SSIM
  contrast-structure term** `(2σXY+C2)/(σX²+σY²+C2)`, C2=0.03, over a 16×16 window, weighted by the alpha/
  coverage channel mean, affine-remapped `(x−0.8)·(1/0.19)` clamp[0,1] (NO luminance term — not full SSIM);
  **factor2 = 4-scale (1:2:4:8 dyadic, weights `0x5fdb10`) wavelet-detail |Σ|coef|| agreement**, separable
  high-pass helpers `0x371730`/`0x371a90`, abs-mask `0x5a81f0`. lane-3 `=recip·0.2` → guided
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
  `msg_offset`; blk0 cams {0,4,6,8,9}, blk2 {1,2,3,5,7} = 10 fired cams @28mm). Block 0 LightHeader: f1/f2
  = GUID (not timestamps), f3 = date submsg, f5 = reference camera, f18 = hw_info; per-camera exposure/
  gain/focus (no plain EXIF scalars). **Block 4 = per-camera LENS-SHADING / color-shading correction grid**
  (16 cams × 17×13=221 pts × a 4×4 near-identity channel-mixing matrix; 14144B=221×16 f32; radial
  corner-rising; orchestrator-verified; per-body-constant, Unit-1≠Unit-2; 8/8 size tier = 2 lens families).
  **Block 5 = global vignetting falloff** (28 radius samples; finder-only LEAD). Block 1 = ancillary
  (f10/f18=1.5348). ⇒ **all 11 LRI blocks role-mapped; clean-room calibration parser spec complete**
  (intrinsics, distortion+LUTs, per-camera CCM, spectral curves, lens-shading grid, vignetting, AWB, header).

### Runtime results (I ran renders — Codex offline, sequential, 28mm)
- **`__bss 0x671980` post-merge "color matrix" is a FIXED CONSTANT** = Ohta/PCA **I1I2I3** orthonormal
  decorrelation basis (`[1/√3,1/√3,1/√3]`,`[1/√2,0,−1/√2]`,`[1/√6,−2/√6,1/√6]`). Write-watchpoint: ZERO
  render-time writes; written once at static-init from a literal pool. **Clean-room: reimplement from
  formula (published transform), NOT per-LRI calibration.** (Resolves handoff residual #3.)
- **AWB-gains consumption CONFIRMED** (differential render): Block-8 `B8.19.15` IS consumed by the pixel
  path, as the **reciprocal** (1/gain) form, **coupled into a color matrix** (perturbing R-reciprocal
  collapsed G/B). Forward copies are inert. Site = `DemosaickLightV1(…,Vec3<f>)`/`setWhiteBalance(AWB)`
  (exact VA open — see below). Clean-room: parse B8.19.15, apply 1/gain folded into the demosaic matrix.
- **Runtime-method caveat for your validation:** READ watchpoints are non-functional under this Rosetta
  x86_64 LLDB (positive-control proven); WRITE watchpoints work. Use differential rendering / single-step,
  and hash DECODED pixels (the output file MD5 changes from an embedded timestamp + JPEG entropy offset).

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
5. ~~`0x218e20` gate consumer behind indirect dispatch~~ — **RESOLVED (runtime): it's a pooled parallel-for
   task body; the accept/reject GATE is in spawner `0x216f60` `0x217ab9..0x217af9` — gate1 = 0.25 CEILING on
   the threshold-exceed fraction (reject frac>0.25, OBSERVED live 70mm, accept:reject 3:5); **gate2/gate3 now
   decoded statically** (`laneD_final_acceptance_static/gate2_gate3_reject_semantics.md`): selector = argMIN of
   the score array; accept iff `B[sel]≤0.25` AND `B[sel]≤B[incumbent]` (gate2, exceed-frac) AND `A[sel]≤0.8·
   A[incumbent]` (gate3, ≥20%-better score, guarded by a positive candidate count) — i.e. absolute floor +
   must-clearly-beat-incumbent; gate2/gate3 still UNTRIGGERED at runtime (static-only). accept→`0xf33d0`. See
   `laneD_final_acceptance_static/accept_reject_gate_located.md`.**
6. Illuminant enum `f2.f1∈{0,2,6}` → which illuminant (A/D50/D65); libcp's actual undistort eval order
   (poly vs LUT); Block-8 AWB gains (being mapped next, LRI-side).

## Pipeline ordering — now mapped end-to-end (quarantine synthesis, NEEDS_CODEX_VALIDATION)
1. **Per-camera UNDISTORT** — `lt::LensUndistortCRA::operator()` `0x261940`, pure LUT-indexed radial (4096-entry
   radius LUT at `this+0x10`, radius clamped [0,4095]; 3×3 projective pre-map + (cx,cy) + scale). **Pre-merge
   ordering now OBSERVED at runtime** (70mm: 25 undistort hits before first merge hit) — see
   `laneB2_lri_calibration_origins/undistort_ordering_lut_runtime.md`. Live LUT = a real ±0.18% radial curve
   (NOT identity; pincushion→barrel). LUT-origin = LRI Block-3 f3.3.2.5 radius map (OPEN, not refuted: the raw
   "0 floats near 1.0" scan was range-limited — f3.3.2.5 holds 0..31 px-radius values, not ~1.0 multipliers).
   UPSTREAM of the merge (so the merge projection's radial is identity).
2. **Per-render CALIBRATION/ALIGNMENT refinement** (separate subsystem) — `0x23faf0`/`0x216f60`
   `CalibDataProcessor::State`: build candidates → parallel-score → accept/reject gate `0x217ab9` (0.25
   exceed-fraction ceiling) → accept writes `0xf33d0` into current/factory CalibStage. (NOT the pixel merge;
   does NOT directly feed the merge projection — REFUTED at runtime.)
3. **PIXEL N→1 MERGE** — IRAMP `0x3661b0` (level 0 only; levels 1-4 are resample octaves via dispatcher
   `0x3ec960`). Motion-compensated, index-validity-gated contributors, **1/Σscore-normalized soft weighted
   average** (`rcpss 0x36a938`), wavelet-domain SSIM-class score `0x36cde0`. Driven by a tiled work-queue
   scheduler `0x3adf30` (producer `0x41a7d0` + level-keyed collector `0x3bf820`); no global Laplacian add.
4. **RESAMPLE** — **cubic B-spline `0x2b2be0` CONFIRMED** (consts 1/6, 3, −6, 4, 6, 2 = textbook basis;
   `laneE_fourzoom_topology/resample_kernels_constants.md`). ⚠ The prior **"Catmull-Rom `0x36f800`" label is
   REFUTED** by its constants `{1/6, 9, ±15, −3, −12, 116/3, 1/64, 0.075274}` — neither Catmull-Rom (no
   −0.5/2.5/−4) nor cubic B-spline; it IS a 1/6-normalized piecewise-polynomial spline of unidentified order
   (LEAD: higher-order spline / B-spline derivative). Exact identity = residual.
5. **COLOR/SHAPING** — lane-3 detail-transfer; fixed **I1I2I3** decorrelation matrix (corroborated TWICE:
   `__bss 0x671980` and global `0x670b00` from consts `0x5f2380` = Ohta basis, applied via 3×3 path `0x300570`
   — a DECOY, not the per-camera CCM); **per-camera CCM apply site now LOCATED**
   (`laneB2_lri_calibration_origins/ccm_apply_site_located.md`): the **4×4 apply `0xbfa20`** reached via
   `setColorCorrection $_58 0x3466d0` → `0xa9f20` → worker `0xbf4a0`, matrix = `*[BayerPipelinePayload+0]+0x14`
   → closure+0x20 → apply `[rdi+0x8]`. (This explains the inert entry-time perturbation — CCM comes via the
   closure capture, not the render-entry proto.) **AWB** gains (Block-8) applied as reciprocals folded into the
   demosaic; spectral curves (Block-6 f2.8); per-camera lens-shading grid (Block-4).
6. **OUTPUT ASSEMBLY** — **final compositing consumer now CROSSED** (`laneE_fourzoom_topology/
   final_compositing_consumer.md`): orchestrator `0x3bca90` join-waits `0x3c25a0`, then **gather `0x3bfe60`**
   drains the level-keyed tile container (a **priority-sorted doubly-linked list at `RendererPrivate+0x260`** —
   the prior "RB-tree" anchor is **REFUTED**: 0 `_Rb_tree_increment` binary-wide) into a `vector<TileUpdate>`,
   then filters by level/type and writes each tile via per-tile ImagePyramid/Image-buffer virtual processors
   (`0x401ab0`) — **per-region placement**, not a single N→1 blend at this level (a separate blend path exists
   at cstring "blending weight…<128_u8" file `0x633da7`). Collector `0x3bf820`=requestRenderROI lambda;
   producer `0x41a7d0`=exportImage lambda.

## ⚠ SPIKE-CRITICAL: libcp output is NONDETERMINISTIC
5 baseline renders of the same 28mm seed → ≥3 distinct decoded-pixel hashes (~48% of pixels differ;
per-channel mean stable only to ~0.034 counts) — multithreaded merge/accumulation-order nondeterminism.
**The validation spike CANNOT use exact pixel/byte match against libcp** (libcp doesn't match itself);
acceptance must be statistical (mean/percentile tolerance). Also bounds the differential-render method:
only large effects (e.g. AWB R→249) are trustworthy. (See `ccm_consumption_runtime_INCONCLUSIVE.md`.)
Block-6 CCM consumption + variant{0,2,6} selection remain UNRESOLVED (entry-time perturbation inert — CCM
parsed mid-render; needs break inside `setColorCorrection`/`ImageApplyColorMatrix` = native-arm64/single-step).
All 3 variants share row-sums [0.9642,1.0,0.8252] (don't distinguish them); `setColorCorrection` exists (LEAD CCM IS used).

## Wave 10 + Lane E (un-fenced 2026-06-03 — items I'd wrongly deferred, now investigated)
- **Four-zoom topology (Lane E)** — substantially mapped. PipelineCache level dispatcher `0x3ec960`
  (tile+0x18 level field): level0→`0x3ec770` IRAMP camera merge, level1→`0x3ebb80` resample, levels2-4→
  `0x3d0650` rescale. RUNTIME: only levels 0+1 fire (28mm L0=250/L1=32; 70mm L0=221/L1=48; levels2-4=0,
  zoom-independent). Driver = work-queue scheduler `0x3adf30` → producer `0x41a7d0` (per-tile render/mode
  dispatch) + level-keyed collector `0x3bf820` (gather into level+priority container, NOT a merge). **No
  global Laplacian/cross-resolution add on the bridge path.** A single LRI render = one full bridge image ⇒
  the "four zooms" are 4 separate captures (cross-validation); within a capture the focal-spanning cameras
  fuse via the level-0 merge. Final pixel-assembly one layer deeper (`0x41a7d0→0x3c6ac0`), uncrossed.
- **C6 (`CLM-C6-001`)** — static: classifier `0xf6c60` maps key-15→camera-group-type-2 (mask 0xfc00, btl),
  which SURVIVES the `0x3c90a5` `+0x30` clear and IS consumed at decision points. (C6 image-CONTRIBUTION
  still open; a differential render is low-EV — one camera's effect likely below the ~0.034-count
  nondeterminism floor, same limit that left Codex's watchpoints inconclusive.)
- **CCM apply** — `ImageApplyColorMatrix`/`setColorCorrection` bodies located; the D50 row-sums have ZERO
  f32 hits in the binary ⇒ the CCM is parsed from LRI Block-6 and handed to libcp as a `ColorCorrection`
  struct: **libcp APPLIES, the LRI/parse SELECTS**. Clean-room: Phoenix parses+applies.
- **Geom builder consumer** — `0x216f60` has 2 callers (State ops `0x22aaf0`, `0x22d250`); it receives its
  State, doesn't own it; tail indirect dispatch still uncrossed.

## Status (not a "boundary" — investigation continues)
All 5 parity blockers + the clean-room LRI parser have been investigated across static disasm, LRI parse,
AND runtime renders (no modality is off-limits while you're offline). What's mapped: the merge mechanism,
the complete per-camera LRI calibration/input parser (incl. spectral curves + lens-shading grid), the
four-zoom level topology, C6 group-type survival, the CCM apply/select split. What remains is genuinely
deeper/lower-EV, not off-limits: the per-tile final-pixel-assembly layer (`0x3c6ac0`); the Lane D accept/
reject gate consumer (`0x218e20` behind `__const 0x6580e0` — runtime-resolvable); C6 image-CONTRIBUTION
(differential render is low-EV vs the nondeterminism floor); exact mid-render CCM-variant selection
(needs single-step). I am continuing to work these by WSJF, not holding. The spectral-curve + full
per-camera-calibration map is a substantial clean-room asset ready for your validation (2026-06-07).
