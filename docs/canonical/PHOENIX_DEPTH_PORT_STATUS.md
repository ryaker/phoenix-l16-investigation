# Phoenix Profile-3 Depth — Port Status (Known Spec + Unknown List)

Disciplined drawdown tracker for the profile-3 DEPTH path only (Phoenix's
scope). Each stage lists (a) the EXACT proven formula and its source claim/
bundle — the KNOWN spec to implement — and (b) Phoenix's implementation status.
Comparison is used ONLY as final acceptance, never to derive a formula. When a
KNOWN stage is confirmed exactly implemented, it is marked PORTED. When an
UNKNOWN is closed by a new proven bundle, it moves from the Unknown List into a
stage as PORTED.

Rule: a correct port takes per-camera calibration as input and therefore
behaves identically across both bodies and all four focals. Any unit/focal-
dependent weakness = an incorrect port (an approximation), not an input quirk.

## Reconciliation: is anything truly unknown?

Codex's own current docs already answer this — there is no contradiction:
- `TRUTH.md` (3.0.351): "the earlier checklist-complete state was narrower than
  the project exit criterion" — the earlier all-solved claim was explicitly
  superseded.
- `LUMEN_PARITY_SPEC.md`: "This spec is a scaffold. It is not yet complete."
- `PARITY_BLOCKERS.md` current status: names one active formula blocker.

So exactly one profile-3-depth formula is genuinely UNKNOWN (below), and it is
Codex-tracked. Everything else on the depth path is PROVEN; the remaining work
is porting proven formulas exactly, then acceptance.

## Known Spec (proven; port target) — depth pipeline in order

| # | Stage | Exact formula source (claim / bundle) | Phoenix status |
|---|---|---|---|
| 1 | LRI decode / raw unpack (RAW10, black/white) | CLM-INPUT-001, CLM-LRI-001 | PORTED |
| 2 | Camera participation / firing (wide A1..A5,B1..B5; tele B1..B5,C1..C6; C6 excluded) | CLM-FIRING-001, CLM-C6-001 | PORTED |
| 3 | Focus-dependent K (sort 2 records by focus_hall_code; lerp K{0,2,4,5} at lens_position) | CLM-WARP-003 / lldb_1f0ce0_k_source_trace | PORTED (base K) |
| 4 | Distortion model (Brown-Conrady + 4096 cubic-Lagrange radial table) | CLM-WARP-004 | PORTED |
| 5 | Undistort envelope box (G-38: 30 radial samples, cubic radius eval, 91/121 edge sweeps, SSE-trunc box) | G-38 bundle (0x145980) | PORTED (computeUndistortEnvelopeG38) |
| 6 | Bayer-norm (raw-B)/(W-B); default hot-pixel; highlight-restore; cross-talk; demosaic | CLM-CORRECTION-001, CLM-DEMOSAIC-001/002, CLM-PIPELINE-001 | PARTIAL — depth guidance uses collapse2, not full ISP (see note A) |
| 7 | Guidance collapse2 [R,0.5(G1+G2),B,1] then ConvertToYUV (sensor w=[.21555,.43231,.35214], p=1/awb, matrix, signed fast-pow 1/2.2, +[0,128,128,0], C3=1) | CLM-STEREO-001 guidance_yuv bundle | PORTED (exact constants) |
| 7a | A2/mono source plane = [m,m,m,1], m=(r-B)/(W-B)*V*scale (EV ratio, no rel_b, no gamma, no chroma) | create_stereo_a2_public_reconstruction | PORTED (this session) |
| 8 | Per-source EV normalization: scale=A1_energy/Ai_energy (color: *rel_b_i/rel_b_A1; mono bypasses rel_b) | a2_public_reconstruction + exposure bundles | PORTED |
| 9 | Non-anchor color-match affine: A=chol(cov_t)*inv(chol(cov_s)), b=mean_t-A*mean_s, C3>0.95 gate | CLM-STEREO-001 component_routes | PORTED (fitStereoAffine) — verify exact |
| 10 | src2/anchor stereo-plane resample: projective H + 4096 radial LUT + 4x4 Catmull-Rom(a=-0.5) at 1/64 subpixel, edge-clamp | CLM-RESAMPLE-001 + static_src2_resampler bundle | KERNEL PORTED (Catmull-Rom now unconditional); operand pairing to verify (note B) |
| 11 | Plane-sweep H composition + projection: H=K_src4[R\|t](K_ref4[R\|t])^-1; P=H[u*d,v*d,d,1]+0.25; clamp [o+1,b-3]; pavgb 4x3 patch | CLM-STEREO-001 plane_sweep_correspondence | PORTED |
| 12 | Per-level projection scale fixed (1,1); level lift full=min(step*coord+trunc(step/2),extent-1); steps 32..1 | CLM-STEREO-001 perlevel_projection bundle | PORTED |
| 13 | G-42 cost: per-source SUM, scaled once by (1/27)/source_count, trunc-toward-zero to u16; uint16 modulo per source | index5_sgm_cost_input bundle | PORTED |
| 14 | ColorFusion `f` -> quantized byte -> sqrt-LUT * sqrt(+0xcc) -> float32 square into CNR lane 3 | CLM-DENOISE-002 (formula exact; integration partial) | PORT PRESENT BUT WRONG at commit 2e2625c: scalar lanes/noise, wrong accumulator association, local unnormalized transform, not wired to CNR |
| 15 | G-43 SGM: 8 dirs [(-1,0)(-1,-1)(0,-1)(1,-1)(1,0)(1,1)(0,1)(-1,1)]; saturating-u16 per contribution; init 2000; no pedestal | 08_DETERMINISTIC_EXECUTION + sgm bundles | PORTED |
| 16 | Argmin: ascending abs index, strict `<`, ties keep lowest | 08_DETERMINISTIC_EXECUTION selection | PORTED |
| 17 | Range map / banded coarse-to-fine refinement (local band index per level) | CLM range/STEREO-001 | PORTED — output index is LOCAL-band (note C) |
| 18 | Reciprocal ray-depth ramp (lookup mm); deterministic execution contract | CLM-WARP-003 ramp; 08_DETERMINISTIC_EXECUTION | PORTED |

Notes:
- A. The depth GUIDANCE path is collapse2->YUV (proven), NOT the full display
  ISP (cross-talk/demosaic/CCM/sharpen). Those proven stages belong to the
  COLOR output, not the depth cost inputs. Confirmed: guidance is
  color_correction=NONE.
- B. Catmull-Rom is now the only resample kernel. Operand check outstanding:
  Phoenix pairs it with envfit + full per-camera radial table; the captured
  src2 ANCHOR operands were affine 0.991346 + near-identity radial LUT. Whether
  the per-source depth undistort uses the full radial (CLM-WARP-004, per-camera)
  or the near-identity src2 form must be settled by exact formula, not diff.
- C. End-to-end depth acceptance must compare in DEPTH (mm) via each side's
  per-pixel band base, NOT raw index (Lumen index is a local-band offset 0..38;
  Phoenix's is a wider index). Capture Lumen's range map to align.

## Unknown List (genuinely unproven — the drawdown queue)

1. **CNR lane-3 guide BYTE-PLANE PRODUCER** (CLM-DENOISE-002; WSJF rank 1).
   KNOWN: consumer transform (lane3=guide^2, guide=sqrt-LUT(byte)*sqrt(+0xcc),
   covariance meanA=mean(lane3)). UNKNOWN: where FusionCacheBayer+0xe0 (exact
   `lt::TileCache<unsigned char>`) byte plane is PRODUCED upstream, its public
   role, and the +0xcc scalar's public origin; route breadth; complete tile
   replay. Resisted 14 instruments (large job). Until closed, stage 14 stays
   NOT PORTED (Phoenix uses the disproven constant-1).

Out of profile-3-depth scope (do not block depth): CLM-COMPAT-001 (profiles
1/2 + GUI DepthEditor), CLM-DEPTH-001/002 (DepthCache/DepthEditor — inactive on
render path). The IRAMP/prefusion src1/src2 reducer items in PARITY_BLOCKERS
are the COLOR-merge output path (CLM-MERGE-005/006 now PROVEN), not depth.

## Verification method (acceptance only)

Both sides FRESH per LRI, same session, across both bodies x 4 focals (harness
`tools/sidebyside_matrix.sh`). Compare in the correct space (depth mm, not raw
index). A stage is accepted only when it matches on ALL of u1/u2 x 28/35/70/150.

## Drawdown log

### 2026-08-11 (parallel: porting-gap track + unknown track)

PORTING GAPS (exact-formula audit, no comparison):
- GAP: calibration selected by camera_id field-match instead of position
  [camera_key]. REAL gap (decode confirms field-1 camera_id is a hardware id
  != key: key0->12 U1, ->4 U2). This is the per-BODY divergence behind the
  Unit-2 weakness. FIXED -> positional indexing. Phoenix commit c72a102.
  Stages 3-8 calibration inputs now select the correct per-body entry.
- Non-anchor color-match affine (stage 9): audited, CONFIRMED EXACT (chol
  formula, C3>0.95, <100->identity, on YUV floats pre-pack). No change.
- Per-camera vignetting selection/interp (stages 5-8 input): audited,
  CONFIRMED EXACT (single model fixed cams; mirror_position interp movable).

UNKNOWN #1 (CNR byte-plane producer) — ADVANCED, not closed:
- Producer NAMED: `lt::FusionCacheBayer` ctor `$_1` per-tile fill hook
  (generator functor at byte_view+0x70), signature
  void(shared_ptr<Tile<unsigned char>> const&). Owning ctor public inputs:
  `RawImageFactory` + `RendererProfileConfig`. Byte-plane public role =
  SoftISP/AWB per-tile product. `+0xcc` = live 1.0f from RendererProfileConfig
  (public). Evidence: bundle_runtime_cnr_lane3_byteplane_generator_rtti_
  unit1_70mm.md (commit 8af3967).
- STILL OPEN: the exact byte arithmetic (the numeric fill). Proposed next
  instrument was to break setWhiteBalance::$_22 -- BUT prior work already
  corrected an overclaim that `setWhiteBalance::$_22` is CONTEXT, not the
  executing producer frame. RECONCILE before acting: confirm whether the
  numeric write is in $_1, in the $_22 callback, or elsewhere, without
  re-treading the refuted context path.

### 2026-08-11 CORRECTION (unknown track was over-claimed)

The "producer NAMED / ADVANCED" note above is RETRACTED as an advance.
FusionCacheBayer is already documented in 16 evidence bundles, including its
byte plane (+0xe0 TileCache<unsigned char>), its input RawImageFactory (+0x8),
its flag machinery (fusioncachebayer_flag_origin_static/_four_zoom), the +0xcc
scalar, and the entire CONSUMER chain (byte -> sqrt-LUT -> guide -> guide^2).
The subagent re-confirmed known naming; it did NOT extract the one open thing.

PRECISE residual unknown (restated): the exact per-byte ARITHMETIC that FILLS
the +0xe0 byte plane -- the numeric formula mapping the SoftISP/AWB raw input to
each byte weight. That single function's math is the whole unknown; everything
structural around it is proven. Stop re-naming FusionCacheBayer; the only
instrument that counts is one that captures the byte WRITE (input operands ->
output byte) for a tile and yields the formula, WITHOUT re-treading the
already-refuted setWhiteBalance::$_22-is-the-producer path.

### 2026-08-11c/d — UNKNOWN #1 traced to the bottom (byte codec CLOSED; weight formula = ColorFusionBayer, genuinely OPEN)

**SUPERSEDED ARITHMETIC NOTE:** TRUTH 3.0.352 runtime replay disproves the
`lane3=f` identity stated in this chronological section. The byte encoder is
quantizing; the consumer reconstructs `(b+1)/256` for nonzero bytes, applies
the profile scalar, then performs a float32 square. See section 11n and
`PARITY_SPEC/09_COLORFUSION_CNR_GUIDE.md`.

CLOSED + independently verified by disassembly:
- Producer: FusionCacheBayer byte-tile generator 0x407710, LAZY on cache-miss
  (refutes pre-resident hypothesis). Chain: 0x406a10 -> 0x3d69b2 -> 0x407710
  -> 0x1aab40 (render float ROI) -> 0x1bd1e0 (float->u8) -> 0x3d1f90 (insert +0xe0).
- Byte codec (0x1bd1e0, verified insn-by-insn): byte = max(trunc(f*256.0)-1, 0),
  scale 256.0f @ 0x5a9250. The original exact-inverse interpretation here is
  superseded by the runtime correction above.
- f = 2x nearest-neighbor upsample of a half-res float weight map.

GENUINE RESIDUAL UNKNOWN (the real bottom): the half-res float weight `f` is the
per-pixel blending-weight OUTPUT of `lt::ColorFusionBayer` (RTTI-proven at
FCB+0x120; render 0x1aab40 = ColorFusionBayer::process; input = RawImageFactory
raw Bayer). Its per-pixel FORMULA lives in the ColorFusionBayer fusion CORE
0x19C790 -- the L16 multi-module COLOR-fusion weight computation. This is:
- NOT a proven claim (no CLM-COLORFUSION in the ledger; ColorFusionBayer appears
  in only 1 evidence bundle, tangentially);
- distinct from the PROVEN MonoFusion (mono A1/A2) path -- this is the COLOR/Bayer
  fusion sibling;
- a substantial subsystem (the "L16 fusion pipeline"), i.e. the true reason this
  item was always "large job-size".

So the one unknown, fully traced, IS the ColorFusionBayer color-fusion weight
formula. Everything wrapping it (byte codec, guide LUT, CNR consumer, cache
structure) is closed. Phoenix stage 14 (CNR lane3) cannot be exactly ported
until ColorFusionBayer's weight core (0x19C790) is reverse-engineered -- that is
now THE remaining reverse-engineering job for depth parity. Evidence: commits
a114eaa, b0cab04.

### 2026-08-11e — CORRECTION: UNKNOWN #1 is the already-identified missing fusion pipeline (not a fresh find)

Answering "did Codex already RE this?": Codex did NOT close the weight formula,
but had ALREADY named and scoped the whole thing long before this session:
- `colorfusion_weight_probe.py` (Codex WIP, commit e0aece2) docstring already
  states the full chain: FusionCacheBayerC1::$_0 0x407710 -> ColorFusionBayer::
  process 0x1aab40 -> two outputs -> 0x1bd1e0 -> u8 TileCache +0xe0, and defines
  COLOR_FUSION_CORE = 0x19C790.
- docs/LIBRARY_INVENTORY.md: "This is the L16 fusion pipeline you're trying to
  rebuild. ColorFusionBayer and FusionCacheBayer ... the thing L16_PIPELINE_SPEC
  says is missing ... require static RE (Ghidra/IDA)."
- monofusion_source_descriptor bundle: ColorFusionBayer installed at FCB+0x120
  (ctor 0x1aab00); the internal fusion formula (0x1b37a0) explicitly "still open".

So UNKNOWN #1 == the long-identified MISSING L16 COLOR-FUSION CORE
(ColorFusionBayer::process 0x19C790 / worker 0x1b37a0). It is a substantial
STATIC-RE effort (Ghidra-class), deliberately deferred by Codex -- NOT a small
runtime-probe find. This session's ONLY genuinely-new, verified increment was
the byte codec byte=max(trunc(256f)-1,0). The multi-session runtime "producer
hunt" largely re-confirmed Codex's existing scaffolding.

Implication: CNR lane3 cannot be ported until the ColorFusionBayer fusion core
is reverse-engineered by static analysis. That single core is the entire
remaining unknown for depth parity; everything else on the depth path is
proven and (per this doc) ported/confirmed-exact.

### 2026-08-11f — UNKNOWN #1 precisely scoped via whatknown gate (no new RE ordered)

Applying tools/whatknown.sh reframed the unknown in minutes:
- 0x1b37a0 (which I'd wrongly lumped with the open ColorFusion) is lt::MonoFusion's
  worker -- FULLY PROVEN across ~8 monofusion bundles/probes (mode-0 exact replay,
  wavelet formula, confidence callback, mode selector, color wrapper). Its scalar
  weight IS proven: confidence = (256 - sum_k w_k)/256 (Wiener source-retention
  weights, overlap-accumulated; accumulator init 256 @ 0x18da80).
- 0x19C790 (ColorFusionBayer::process core) is a LARGE function (0x53E8=21480-byte
  stack frame, vector-constant tables, multi-image inputs). whatknown = NO HITS in
  any proof artifact -> genuinely unproven. Callers: 0x1aad5d (ColorFusion) and
  0x1b9bb4.

SCOPING (producer shape only; the old `lane3=f` arithmetic is superseded): CNR
lane3 derives from the ColorFusionBayer weight, the COLOR analog of the PROVEN
MonoFusion confidence. Same formula shape ((256-sum w)/256; the 256 also appears
in the proven ColorFusion byte codec x256), but the retention weights w_k are
computed over the Bayer modules by the unproven 0x19C790 core. So:
- TEMPLATE (reuse, do NOT re-derive): MonoFusion mode-0 Wiener confidence +
  wavelet + confidence-callback formulas already prove the weight STRUCTURE.
- GENUINE OPEN (NO HITS): the ColorFusionBayer core 0x19C790 per-module Bayer
  retention-weight computation. Static-RE job, guided by the MonoFusion template.
Do NOT port an approximation; CNR lane3 stays NOT PORTED until 0x19C790 is
reverse-engineered against the MonoFusion template.

### 2026-08-11g — UNKNOWN #1 DRAWDOWN via static structural map (evidence-first, whatknown-gated, boundary-verified)

Disciplined static read of 0x19C790 against the PROVEN MonoFusion template
(no new runtime RE; whatknown already confirmed NO-HITS = investigation justified).

BOUNDARY (verified, to avoid overclaim): 0x19C790 prologue `sub rsp,0x53e8` @
0x19c79d; epilogue `add rsp,0x53e8` @ 0x19d6dc. TRUE body = 0x19c790..0x19d6dc
(~0xf40 bytes of code; the 21480-byte frame is local patch buffers). The
0x5d0070-table + Hann-loop code at 0x19f8xx is a SEPARATE callee, not this func.

WHAT THE TRUE BODY PROVABLY SHARES WITH THE MONO TEMPLATE (portable, do NOT re-derive):
- Half-sample Hann overlap-add window: 0x19C790 calls helper **0x18ce50** (same
  helper MonoFusion uses; 0x18ce50 = C1 - C1*trig((i+C1)*2pi/N), the proven
  half-sample Hann). 114 sites reference it library-wide.
- 16x16 coefficient-weight Wiener table: 0x19C790 references descriptor
  **0x5cedf0** (@0x19c803) -- the SAME descriptor that fronts the proven table
  **0x5d0070** (mono template bundle, line 259: "installed at 0x5d0070 behind
  descriptor 0x5cedf0"). Its Wiener callee (~0x19f4xx) loads 0x5d0070 directly and
  rebuilds the 16-tap Hann via 0x18ce50 (edi=0..15, esi=0x10).
=> The coefficient-domain Wiener blend (w_k = d2/(d2+lambda); S_k = w_k*T_k +
   (1-w_k)*S_k) and the retention/confidence aggregation shape
   (confidence = (256 - sum_k w_k)/256) are the PROVEN mono formulas, now shown
   to execute in the color core too. The color weight `f` (CNR lane3) is the
   per-pixel color analog of the proven mono confidence scalar.

RESIDUAL GENUINE UNKNOWN (now narrowed from "entire core" to two front-end pieces):
1. Color/Bayer patch marshaling: how per-module Bayer inputs become the 16x16
   patches. Owned by color-specific callees 0x18e770 / 0x18eb00 / 0x18ebc0 /
   0x18f690 / 0x18fe00 / 0x19d820 / 0x19d8e0 / 0x19dc30 / 0x19e7d0 / 0x19eb60 /
   0x19f470, and vector-const tables 0x64f2e8 / 0x64f320 / 0x64f398 / 0x64f3c8
   (+ 0x5a8920). These are NOT in the mono template.
2. Per-pixel retention-weight readout that becomes `f`: whether it is literally
   (256 - sum w_k)/256 per pixel (mono-identical) or a color-plane-weighted
   combination. Mono inits its accumulator to 256 @ 0x18da80; 0x19C790 does NOT
   call 0x18da80 (accumulator handled inline / in a callee) -> the exact readout
   is the one formula still to pin.

NET: the unknown is no longer "the whole ColorFusionBayer core is a black box."
The transform + Wiener blend + window are the proven mono template (shared table
0x5d0070 + shared window 0x18ce50). The real open static-RE surface is (a) the
color patch assembly (11 named callees + 5 const tables) and (b) the exact `f`
readout. That is a bounded job, not an open-ended one. CNR lane3 stays NOT PORTED
until (a)+(b) are pinned; no approximation to be committed.

### 2026-08-11h — UNKNOWN #1: the `f` readout is PINNED from disassembly (was the last NO-HITS residual)

Three parallel STATIC-DECODE agents (read-only; no runtime/no pixel compare) +
main-thread instruction spot-check decoded the CNR lane-3 weight `f` end-to-end.
Full evidence: docs/evidence/bundle_static_colorfusionbayer_f_readout_2026-08-11.md

PINNED FORMULA (read from 0x19C790 + 0x18eb00 instructions, addresses in bundle):
  f = [ ((N+1) - Σ_k m_k)^2 + Σ_k m_k^2 ] / (N+1)^2
  N = # Bayer modules intersecting the 16x16 patch; +1 = base/reference term.
  m_k = per-module retention from 0x18eb00 = PROVEN mono Wiener retention
        (w=d^2/(d^2+λ) @0x18eb4d; retention (1-w)×1/256 @0x18ebaf) = the color
        analog of mono confidence (256-Σw)/256, computed per Bayer module.

What this means for parity:
- PROVEN-SHARED (no re-derivation): the Wiener weight + blend + retention shape
  (0x18eb00), 16x16/step-8 geometry, half-sample Hann OLA (0x18ce50), patch-noise H
  (mono-identical). These are the mono template, now shown executing in the color core.
- GENUINELY-NEW color, now DECODED (was the unknown): the cross-module quadratic
  combine f=(A^2+B)/(N+1)^2 (A=(N+1)-Σm, B=Σm^2), two outputs (image ÷(N+1),
  weight ÷(N+1)^2), dual-plane separable-windowed marshaling (0x18ebc0/0x18f690),
  √2-normalized lifting (0x18fe00/0x19eb60).

STATUS: the one genuine depth-parity unknown is no longer unknown — it is a decoded
explicit formula, ready to PORT, pending 2 small bounded confirmations before commit
to Phoenix: (1) m_k lane/λ accounting inside 0x18eb00 (numeric range only, not the
combine); (2) 0x18fe00 fwd-wavelet epilogue boundary (coeffs already known).
CNR lane-3 stays NOT-PORTED (no approximation) until those 2 close, then it is a
direct port of the pinned formula above.

CORRECTION to 2026-08-11g: that entry wrongly attributed the Wiener weight/table to
0x19dc30/0x19e7d0/0x19eb60 (a boundary-crossing signature scan). Corrected: those are
the ÷(N+1)^2 normalizer / ×scale / inverse-lifting helpers; the Wiener weight is in
0x18eb00. 0x5cedf0/0x5cee00 are int ROI masks, not the λ table; 0x5d0470 is a param
block, not a 2nd λ table. See bundle for boundary-correct addresses.

### 2026-08-11i — UNKNOWN #1 CLOSED (both confirmations resolved). Bonus: closes Phoenix G-58.

CONFIRMATION 1 (0x18eb00 m_k) — CLOSED:
- One call consumes the FULL 16x16=256-coeff patch (inner loop @0x18eb30 x16, outer
  @0x18eb20 x16); one call per Bayer module (caller 0x19d096).
- λ_k = coefBuf_k × noiseScale. coefBuf = per-coefficient runtime buffer [rbp-0x1030]
  (built by 0x19d8e0). noiseScale = [rbp-0x52c0]·[rbp-0x53c0], per-patch constant
  (r8=[rbp-0x5300], never advanced). (coefBuf's provenance from table 0x5d0070 not
  asserted at this callsite — honest limit.)
- m_k = (256 − Σw)/256 ∈ [0,1], w=d²/(d²+λ) broadcast to a scalar; accumulator [rsi]
  zeroed @0x18eb05, Σ(1−w) @0x18eb70-79, ×1/256 (0x5cbfc0) @0x18ebaf, stored [rbp-0x52f0].
  => m_k is the mono confidence (256−Σw)/256, per Bayer module. NUMERIC RANGE PINNED.

CONFIRMATION 2 (0x18fe00 fwd wavelet) — CLOSED:
- True body 0x18fe00..0x190790, returns via ret @0x190790 (disassembler falsely split
  at interior push rbp @0x190403; regs xmm8/9/10/12/13 bound once @0x18fe02-22 confirm
  single function). Coeffs: 1/√2 @0x5cbf80, 1/(2√2) @0x5cbf90, √2 @0x5cbfa0, 0.5 @0x5cbfb0
  (corr: not 0x5a92a0), 1.0 @0x5cc050. Separable orthonormal-scaled lifting over 16x16x4.
  Predict stencil = 5/3 (x_odd − ½(x_L+x_R)); normalized (√2) with update weight ≠ 5/3's ¼
  => 5/3-FAMILY, orthonormally normalized (not bit-identical to unnormalized 5/3).

=> UNKNOWN #1 (color weight f / CNR lane-3 producer) is fully DECODED end-to-end:
   f = ((N+1)−Σ_k m_k)² + Σ_k m_k²) / (N+1)², m_k = (256−Σw_k)/256 per Bayer module,
   w = d²/(d²+λ), λ=coefBuf×noiseScale; patch transform = normalized 5/3-family lifting;
   half-sample Hann OLA (0x18ce50). No genuine unknown remains on the profile-3 depth path.

BONUS — closes Phoenix SPEC-GAP G-58: phoenix/engine/merge/monofusion.h documents that
"the exact Wiener combine algebra inside 0x1b37a0 is not admitted" and implements an
APPROXIMATE difference-shrinkage Wiener. The exact algebra is now decoded (same 0x18eb00
family): w=d²/(d²+λ), fused_c = w·T_c+(1−w)·S_c, confidence=(256−Σw)/256. G-58 can be
closed with the exact formula. Remaining work is PORT/IMPLEMENTATION (not RE).

### 2026-08-11j — coefBuf CLOSED → UNKNOWN #1 has ZERO numeric residual (supersedes the 11i "honest limit")

The 11i note "coefBuf provenance not asserted / one unclosed numeric input" is now
RESOLVED (superseded — do not cite it as open). Found the initializer that earlier
greps missed because it uses INDEXED stores `[rbp+rdx-0x1030]`, not the literal disp:

- Prologue copy loop 0x19c860..0x19c954 (runs once): `lea rcx,[rip]→0x5cee10` @0x19c81f;
  16 iters × 0x100 B; final store each iter `movaps [rbp+rdx-0x1030],xmm0` @0x19c93e;
  copies the full 0x1000 B table at VA 0x5cee10 into coefBuf [rbp-0x1030,rbp-0x30).
- 0x5cee10 = the proven mono per-coefficient λ table 0x5d0070[0..255], broadcast to 4
  Bayer lanes (verified byte-identical: min 0.5625 max 8.65008 sum 360.238; all 4 lanes equal).
  (0x5cedf0=(0,0,16,16) and 0x5cee00=(16,16,16,-1) are the int ROI masks of the same
  descriptor block; 0x5cee10 is its float λ payload. Reconciles the 11h correction.)

=> coefBuf_k = 0x5d0070[k].  λ_k = 0x5d0070[k] × noiseScale.
   noiseScale = σ²_sample(patch) × (arg × 8.0)  [σ² via virtual getter @0x19cd2e →
   [rbp-0x52c0]; arg×8 const 0x5a9b0c → [rbp-0x53c0]; product @0x19d069].
   w_k = d²/(d²+λ_k) @0x18eb4d ; m_k = (256−Σw_k)/256 (×1/256 const 0x5cbfc0) ;
   f = ((N+1)−Σ_k m_k)² + Σ_k m_k²) / (N+1)².

FINAL: the profile-3 depth path has NO remaining unknown and NO remaining numeric
residual. The color weight f (CNR lane-3 producer) is fully decoded to static constants
+ decoded instructions. Same λ table (0x5d0070) as mono ⇒ this also gives Phoenix G-58
its exact per-coefficient λ. Remaining work is PURE PORT/IMPLEMENTATION.

### 2026-08-11k — CORRECTION + cross-validation (fixes my 11i/11j "bonus G-58" overclaim)

CORRECTION (per "clean up outdated/incorrect info"): 11i/11j said the decode "closes
Phoenix G-58 / gives Phoenix its exact λ." That is WRONG — I read a STALE sibling copy
(phoenix_arm_pre_unify_20260719). The REAL phoenix/engine/merge/monofusion.h says
"G-58 closed for the algebra AND the table" — Phoenix ALREADY has the exact Wiener +
the 256-float 0x5D0070 table (monofusion_coeff_table.h, SHA 3eebf27f...). My decode adds
nothing to G-58; disregard the "bonus" claim.

CROSS-VALIDATION (genuinely useful): the real monofusion.h item 8 already implements the
SECOND OUTPUT PLANE (gap F1, closed 2026-08-05):
  q_c=(256-Σw)/256; A=Σ(1-q); B=Σq²; scalar=(c0+c1·A·c2)²+c3·B,
  c0=alpha, c1=1-alpha, c2=1/N, c3=(1-alpha)²·C/(N²·R).
My decoded ColorFusionBayer f = ((N+1)-Σm)²+Σm²)/(N+1)² is the SAME STRUCTURE (color
instantiation of that general form). So the decode is independently confirmed by
Phoenix's own proven mono F1 implementation, and Phoenix already has the code template
+ F_k table for the color port.

REVISED remaining work (accurate): CNR lane-3 is NOT an RE unknown — the f formula is
decoded AND matches Phoenix's existing mono F1. Remaining = PORT: implement the color-f
plane in Phoenix's ColorFusionBayer/color-Bayer-fusion stage (analog of monofusion's F1
second output) and wire it to CNR lane-3 (replacing meanA:=1). Templated by
engine/merge/monofusion.cpp. No RE blocker remains.

### 2026-08-11l — Port integration requirement pinned (producer DONE; remaining = multi-module gather)

Producer: engine/merge/colorfusion.{h,cpp} implements the decoded f exactly + self-test
PASSES (Phoenix commit 2e2625c). Formula/inputs 100% closed.

Integration fact (from src2 source-camera identity bundle + u8_weight_writer probe):
- ColorFusionBayer fuses N RAW Bayer modules (lt::RawImageFactory) that INTERSECT each
  16x16 patch; N varies spatially by module geometry. Output image is anchored to ONE
  tier camera (A1 wide / B4 tele, Active=1), but the WEIGHT f is computed over ALL
  overlapping modules — that weight is CNR lane-3.
- Phoenix TODAY: demosaics the anchor (A1) + MonoFusion A2 luma. It does NOT gather the
  N overlapping color Bayer modules per patch. So colorFuseWeightPlane has no inputs yet.

REMAINING WORK (engineering, no RE unknown): build the per-patch multi-module Bayer
gather in phoenix_fuse — for each patch, select the modules whose calibrated footprint
covers it (Phoenix already parses all modules + FactoryModuleCalibration geometry),
DC-align/warp their raw Bayer to the anchor (Phoenix already has the undistort/flow),
feed ref + the N module patches + per-module noiseScale (σ²_patch·arg·8, from the same
VST/vign path MonoFusion uses for V) to colorFuseWeightPlane, then route f → applyCNR
lane-3 (replace meanA:=1). Validate with tools/parity/verify_cnr_alpha_lane.py against
captured Lumen lane-3. This is a real fusion-gather subsystem, not a wiring one-liner.

### 2026-08-11m — PROBE: N is small + FIXED per tier (de-risks the gather)

Runtime probe (lldb break @0x19c790, read arg4=module vector size, --profile 3, HL_NUM_THREADS=1;
tools/lldb_probes/colorfusion_N/, runs/colorfusion_N/):
- WIDE u1_28 (2018-07-23/L16_02130): N = 3 for ALL 48 tile invocations (N_hist {3:48}).
- TELE u2_70 (2017-12-01/L16_00010): N = 4 for ALL 44 tile invocations (N_hist {4:44}).
- 0x19C790 is called PER OUTPUT TILE (~46/frame), not per patch; the 16x16/8-step patch
  loop is INSIDE it. Each of the N module descriptors (0x30 B) carries dims ~2080x1560
  (= HALF-RES) + a data pointer. So ColorFusionBayer fuses N HALF-RES planes; the f/guide
  plane is half-res (matches the "guide is half-res, pixel-doubled" note).

CONSEQUENCE (re-sizes the port): the gather is NOT a general per-patch geometric overlap.
It is a FIXED small-N fuse: 3 half-res module planes at wide, 4 at tele, per output tile.
So colorFuseWeightPlane runs at half-res (2080x1560) over a fixed module set. The build is
bounded: produce the N half-res module planes (DC-aligned) + reference, run the producer,
pixel-double the f plane to the CNR resolution, route to lane-3. Remaining detail for the
gather: identify which N cameras (data-ptr -> module map) and confirm reference vs the N
vector entries (decode indicates reference T is built separately; the N vector are the
sources; +1 base term = the reference).

### 2026-08-11n — Runtime bit replay + selector closure; current Phoenix port fails

This supersedes the earlier claims that `m_k` is lane-independent before
reduction, that the byte codec is an exact inverse, and that `lane3=f`.

- A retained Unit-1 `28mm` packet captures three complete transformed
  `256xvec4` source/reference/coefficient blocks, the live four-float noise
  vector, all three `m_k`, and `A/B/A^2+B`. The repo verifier reproduces every
  captured result bit-for-bit.
- `0x18eb00` computes four Bayer-lane Wiener weights per coefficient, takes an
  x86 max across the four, broadcasts that scalar, and accumulates ordered
  `1-max(w)`. Every lane wins dozens of coefficients in the live packet.
- The reference descriptor is separate from the N-entry source vector. The
  installed selector is enabled, non-target, same camera group, and
  nonnegative public Bayer override: A1 with A3/A4/A5 at wide; B4 with
  B1/B2/B3/B5 at tele.
- Profile 3 plus public `SENSOR_AR1335(2)` selects tuning key 2; all five
  installed gain rows set `FusionCacheBayer+0xcc=1.0f` exactly.
- The byte boundary is quantized. Captured patch `f=0x3e8e8cf6` encodes to
  byte 70 and decodes/squares to lane3 `0x3e8dffff`, not raw `f`.
- A direct replay compiled against live Phoenix commit `2e2625c` yields wrong
  `m` words (`3f63f1c3`, `3f6ea0db`, `3f6cc4ea`) and a one-ULP combine error
  even when fed Lumen `m`. The API must carry `256xvec4` plus four-lane noise,
  max the lanes, preserve installed accumulator order, and reuse the
  normalized lifting implementation already in `monofusion.cpp`.

Implementation contract:
`docs/canonical/PARITY_SPEC/09_COLORFUSION_CNR_GUIDE.md`. Parent claim remains
PARTIAL pending a direct runtime ID-vector join, ColorFusion raw-transform
checkpoint, complete wide/tele CNR tile replay, and two-body/four-focal
integration.

### 2026-08-11o — Direct ordered vectors + raw transform CLOSED

This supersedes 11n's first two pending items and corrects 11m's unordered
camera-set wording.

- Unit-1 `28mm` direct owner fields: target A1/key `0`, sources
  `[A5(4), A3(2), A4(3)]`.
- Exact-focal Unit-2 `70mm` direct owner fields: target B4/key `8`, sources
  `[B2(6), B5(9), B1(5), B3(7)]`.
- These are the admitted RawImageFactory first-occurrence orders after target
  and rejected records are filtered. Do not sort the source IDs.
- Raw and post-`0x18fe00` `16x16xvec4` source buffers were retained on both
  runs. The normalized 5/3-family clean-room replay differs at zero of 1024
  float32 words on each body/tier packet.
- Current Phoenix `colorfusion.cpp` is therefore directly disproven at two
  boundaries: its scalar Bayer API loses the four-lane max, and its local
  `0.5/0.25` lifting is not the installed normalized transform.

Remaining admission gate: complete wide/tele ColorFusion-to-CNR tile replay
and sufficient two-body/four-focal Phoenix integration. Wiring contract:
`docs/canonical/PARITY_SPEC/09_COLORFUSION_CNR_GUIDE.md`.

### 2026-08-11p — Public target-noise origin CLOSED at two bodies/two tiers

The complete target-side input to the ColorFusion noise callback is now
reproducible from public LRI fields with exact binary32 agreement on Unit-1
`28mm` and exact-focal Unit-2 `70mm`:

- RAW10 is passed through the admitted hot-pixel correction and then
  `RestoreHighlightsBayer`; the resulting float plane is `float(u16)-42`.
- `RestoreHighlightsBayer` does not use the reciprocal of public RAW AWB.
  `ColorFusionBayer::initialize` passes the public AUTO neutral temperature and
  tint through the installed Robertson interpolation and `0x350820` matrix
  sequence. That sequence produces the exact three-channel scene-neutral gain.
- The full-frame halo is same-CFA parity extension, not ordinary clamp or
  reflection: negative coordinate `q -> q&1`; upper coordinate
  `q -> n-2+(q&1)`.
- `0x18e150` reduces each `16x16` Bayer block to fixed spatial lanes
  `[top-right, top-left, bottom-left, bottom-right]`, with 64 samples per lane,
  ordered pairwise accumulation, and multiplication by `1/256`.
- The selected public `17x13` vignetting table is bilinearly expanded to the
  `260x195` block grid. The exact mixed-precision boundary and bit order are in
  the implementation contract.
- The noise callback takes valid-only `2x2` means at the requested block
  coordinate and computes, per lane,
  `H^2 * max(1e-5, ((42 + 1/D)*a/1023)+b) * 1023^2`; the ColorFusion core then
  multiplies this result by `8`.
- Sensor noise coefficients are selected from the first installed public
  `SensorGainVars` row whose gain key is at least
  `int(float32(analog_gain*100))`, in lane order `[red,green,blue,green]`.

The combined verifier checks all 12,979,200 target-plane words, all 202,800
signal words, all 50,700 shading words, the scene-neutral gain words, and live
noise callback outputs on both captures. Current Phoenix still requires three
specific corrections before this boundary can match: implement the exact
temperature/tint scene-neutral sequence, parity-pad the full frame before the
highlight kernel, and preserve the fixed spatial four-lane signal/noise API.

This closes only the target/noise origin. The source-camera half-resolution
plane construction, sidecar/overlap policy, complete ColorFusion-to-CNR tile
replay, and broader integration remain open under `CLM-DENOISE-002`.

### 2026-08-11q — Phoenix ColorFusion port: arithmetic core + signal/shading DONE (bit-exact)

Shipped + pushed to phoenix-l16-build (commits 5a68d54..bef35e2), each validated
against Lumen ground truth (no synthetic-only tests, no tuning):

- Producer (spec 09 changes 1-4): colorfusion.{h,cpp} — 256xvec4 Wiener, per-coef
  4-lane x86 MAX, installed-order combine A=1;A+=1-m, normalized 5/3 lifting.
  BIT-EXACT vs verify_colorfusion_f_runtime u1_28 (m=3f40e9fe/3f58699a/3f51ea60,
  A^2+B=408e8cf6, f=3e8e8cf6). FMA off (project-global -ffp-contract=off).
- Selection (change 6a): colorfusion_select.h — enabled && !=target && same group
  && Bayer override x|y>=0, first-occurrence order. Validated on real LRIs:
  u1_28 A1->[A5,A3,A4]; u2_70 B4->[B2,B5,B1,B3].
- Byte/CNR codec (change 7 conversion): colorFusionByte + cnrLane3FromByte.
  Checkpoint f=3e8e8cf6->byte 70->lane3 3e8dffff + byte-zero case. Exact.
- reduce_signal (change 5 signal table): colorfusion_noise.cpp — x86_rcpps(max(0.1,
  tgt)); 8x8 parity-subset sums *1/256; lanes [TR,TL,BL,BR]. BIT-EXACT 0/202800 vs
  captured u1_28 target->signal.
- public_shading_plane (change 5 shading table): 17x13 profile -> 195x260. BIT-EXACT
  0/50700 by equivalence to the Lumen-proven verifier oracle.

REMAINING (rank 1), a coherent target-plane build (reuses Phoenix hotpixel/highlight/
AWB/CCM kernels), then integration:
- Target RAW plane: RAW10 -> selected hot-pixel -> RestoreHighlightsBayer -> scene-
  neutral gain (Robertson/0x350820, checkpoints 3f150644.../3f1c02e7...) -> parity
  halo -> float(u16)-42. Oracle: verify_colorfusion_noise_public_origin.py.
- Noise provider (H,D,SensorGainVars -> core_noise=noise*8). Oracle: same verifier
  (captured core_noise, e.g. u1_28 noise_product 6372.87/11981.97/7209.00/12217.11).
- Source half-res Bayer planes for the ordered vectors (change 6b; source-plane
  construction is the one still-open RE item).
- 2x pixel-double + CNR lane-3 wiring (replace meanA:=1); full wide/tele + two-body
  tile replay (gate 6, the promotion gate for CLM-DENOISE-002).

### 2026-08-12 — ColorFusion source planes + CNR lane-3 wiring; gate-6 boundary pinned

Phoenix work (branch master, pushed): built the source half-resolution plane
constructor, the full half-res f->lane3 assembly, and the gated CNR lane-3 hook.
Validated at every step that has an oracle; the FIRST unreachable step is named
precisely below (no faked parity).

WHAT IS VALIDATED (oracle-pinned):
- Target-route refactor (engine/merge/colorfusion_target.{h,cpp}): factored the
  proven RAW10->hotpixel->RestoreHighlightsBayer(c)->f32(u16)-42 route into
  `colorFusionRoutePlane(camera_key,c)` so sources reuse the EXACT target path.
  Non-regressive: validate_colorfusion_target on L16_02130 = target plane
  0/12,979,200 words differ (BIT-EXACT) vs u1_28 target_pre_vignette_f32.bin.
- f16 pack quantization (engine/merge/colorfusion_source.cpp `f32ToHalfToF32`):
  IEEE-754 binary16 round-to-nearest-even, matches an independent reference
  bit-for-bit (608.3349609->608.5, 974.7729->975.0, 65504 and 2^-24 subnormal
  round-trip exact). This is the installed vec4x16f pack (static custody
  verify_colorfusion_source_plane_static.py: half-res vec4x16f, lanes
  [TR,TL,BL,BR], flow retained separately at owner+0x128).
- phoenix_merge builds clean with colorfusion_source.cpp added; the per-patch
  producer f, camera selection, signal/shading/noise, and byte/lane3 codec remain
  bit-exact (unchanged; prior entries).

WHAT IS BUILT BUT NOT ORACLE-PINNABLE (honest):
- engine/merge/colorfusion_source.{h,cpp}: `colorFusionSourceFullPlane` (route
  per source + shared anchor gain c) and `colorFusionHalfResPack` (2080x1560 vec4,
  lanes [TR,TL,BL,BR], f16-quantized).
- engine/merge/colorfusion.cpp `colorFuseLane3Plane`: ref + ordered source half-res
  planes -> per-patch four-lane core_noise (colorFusionNoiseProvider over the
  260x195 signal/shading neighborhood means) -> per-patch producer f -> half-sample
  Hann-16 OLA -> f->byte->lane3. Links + runs (finite lane3 in [0,1]).
- tools/phoenix_fuse.cpp applyCNR: CnrParams gains a pixel-doubled (nearest 2x)
  lane-3 plane; the constant `meanA:=1` (divergence D1) is replaced by the
  per-tile lane-3 mean. BIT-IDENTICAL to the proven default when the plane is
  empty/disabled; armed by env PHX_CFLANE3. Compiles clean (build-x86 phoenix_fuse
  links only against the known libtiff/x86_64 gap).

*** GATE-6 BOUNDARY — FIRST PLACE VALIDATION IS IMPOSSIBLE (not faked) ***
The source plane the transform actually consumes (`source_before_vec4`, captured)
is the f16 half-res source plane SUB-PIXEL FLOW-RESAMPLED (DC-aligned) to the
anchor. Evidence it is a resample, not a direct read: 1019/1024 captured
source_before words are NOT binary16-representable, so they fall between f16 grid
points -> interpolation happened. Reproducing source_before bit-exact needs the
per-source FLOW field (vec2 f32, owner+0x128). Its ONLY oracle is
`runs/colorfusion_source_planes/` produced by
`tools/lldb_probes/colorfusion_source_planes/probe.py` — that probe EXISTS but was
NEVER RUN (no run directory on disk). The transform captures
(runs/colorfusion_f_runtime/u1_28_transform/) additionally record no patch
plane-origin, so even the extraction coordinate is unknown. Therefore:
  1. Source-plane spot-validation vs source_before_vec4 CANNOT be computed
     bit-exact (missing flow field + missing patch origin). Words-differ is
     undefined, not zero — reporting a number here would be fabrication.
  2. Downstream lane-3/guide OUTPUT captures DO exist -- runs/cnr_lane3_producer/
     guide_seq1_524x520_str532.f32 / guide_seq2_522x522_str522.f32 are captured
     CNR guide planes (unit1 70mm tele; values 0.586..1.0, pairwise-duplicated =
     pixel-doubled from half-res) plus byte-cache/byte-tile producer probes. But
     they are NOT a replayable oracle for us: (a) no matching INPUT byte plane is
     dumped as a paired file (the byte plane is FusionCacheBayer+0xe0, only its
     cache structure/allocation was probed, no .bin), and (b) reaching guide_seq
     requires first producing the flow-aligned f->byte plane, which is blocked by
     (1). The byte->guide->lane3 LUT itself is already proven exhaustively
     (0..255, gate 5); what is missing is the ability to PRODUCE the byte plane.
     No captured full ColorFusion f/byte plane exists, and the spec's own gate 6 /
     "Known exclusions" states whole-tile ColorFusion + CNR tile output remain
     validation work. So the pixel-doubled lane-3 -> CNR meanA replacement cannot
     be validated end-to-end either.

TO CLOSE GATE 6 (capture work, not code): run the colorfusion_source_planes probe
to dump the reference/ordered-source/flow descriptors for u1_28 (wide) and u2_70
(tele); add a probe that dumps one full ColorFusion f/byte plane and the matching
CNR source lane-3 tile; then replay on a second physical body. Until those exist,
`CLM-DENOISE-002` stays PARTIAL/BLOCKER and the PHX_CFLANE3 path stays armed-but-
inert by design.

### 2026-08-12b — Flow field captured -> source resample CLOSED (bit-exact); vignette is the last plane step

The coordinator ran the colorfusion_source_planes probe on both bodies, so
runs/colorfusion_source_planes/{u1_28,u2_70}/ now hold the reference/ordered-
source vec4 f16 planes AND the per-source flow_vec2_f32 fields. With those, the
source DC-alignment that was the gate-6 blocker is now SOLVED and validated
bit-exact.

CLOSED (bit-exact, verify_colorfusion_source_flow_resample.py = 0/1024):
- Flow layout: flow is PER-PATCH on the 259x194 grid (= 16x16 step-8 patches on
  2080x1560: (2080-16)/8+1=259, (1560-16)/8+1=194), vec2 f32. Valid flows are
  sub-pixel (dx in [-0.23,0.53]); rejected patches carry -FLT_MAX / NaN.
- Resampler (no interpolation): the transform's DC-aligned source patch is an
  INTEGER read of the f16 source plane, scaled by 981:
      source_before[j,i,l] = f32( 981.0f * plane_f16[oy+j, ox+i, l] )
      (ox,oy) = ( floor(px*8+dx), floor(py*8+dy) ),  (dx,dy) = flow[py,px]
      scale 981 = white(1023) - black(42).
  u1_28 cam4: flow cell (7,91)=(-0.1136,-0.0607) -> origin (55,727); 0/1024 words
  differ vs captured source_before_vec4. The earlier "1019/1024 non-f16-
  representable" red herring is fully explained by the *981 scale, NOT a Catmull-
  Rom/bilinear kernel -- there is none.
- Pack normalization: the plane stores f16(route_out / 981). f16(source_before/981)
  == captured source_vec4_f16 plane, 0/1024.

WIRED: colorFuseLane3Plane now consumes per-source flow fields and applies
origin=floor(px*8+dx,py*8+dy) with *981; colorFusionHalfResPack stores
f16(quad/981). phoenix_merge builds clean.

*** REMAINING for a FROM-SCRATCH plane: per-pixel VIGNETTE gain (formula gap, NOT
a missing capture) ***
Building the plane from L16_02130 via colorFusionSourcePlane does NOT yet equal
the captured plane: captured_plane*981 / my_route is a smooth SCALAR radial field
= 1.0 (center) -> ~3.8 (corners), identical across all four Bayer lanes = a lens
vignette the route omits (the route is pre-vignette, itself bit-exact vs
target_pre_vignette). That field matches the coarse shading table block-for-block
(colorShadingPlane / captured shading_plane_f32): 3.708/2.476/0.999/3.768 at
(0,0)/(0,95)/(130,97)/(259,194). So the plane build is:
    route(4160x3120) * vignette_gain(17x13 profile -> full res)  ->  /981  ->
    2x2 f16 pack [TR,TL,BL,BR].
All pieces exist in Phoenix (premerge/vignetting.h parseVignetting/interpolateHall/
shapeProfile + colorShadingPlane); closing it is a formula-SELECTION pass (m/q
shaping flags, sample origin/spacing, colorShadingPlane vs premerge bilinear)
validated against the now-captured plane. This is the exact first divergence for
from-scratch construction and needs NO new capture.

GATE 6 still open on CAPTURE: no full ColorFusion f/byte plane and no CNR source
tile were captured (only source_planes were run this pass; runs/cnr_lane3_producer
holds only downstream guide output with no paired input-byte plane). Those remain
the promotion-gate captures for CLM-DENOISE-002.
