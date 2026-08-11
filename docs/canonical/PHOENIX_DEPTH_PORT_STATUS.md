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
| 14 | CNR guide lane-3 = guide^2; guide=sqrt-LUT(byte)*sqrt(cache+0xcc); CNR covariance meanA=mean(lane3) | CLM-DENOISE-002 (consumer proven) | NOT PORTED — Phoenix uses constant-1 (blocked on Unknown #1) |
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

CLOSED + independently verified by disassembly:
- Producer: FusionCacheBayer byte-tile generator 0x407710, LAZY on cache-miss
  (refutes pre-resident hypothesis). Chain: 0x406a10 -> 0x3d69b2 -> 0x407710
  -> 0x1aab40 (render float ROI) -> 0x1bd1e0 (float->u8) -> 0x3d1f90 (insert +0xe0).
- Byte codec (0x1bd1e0, verified insn-by-insn): byte = max(trunc(f*256.0)-1, 0),
  scale 256.0f @ 0x5a9250. Exact inverse of proven consumer guide=sqrt((b+1)/256);
  round-trip f->b->guide^2=f closes. So CNR lane3 = f (linear weight in [0,1]).
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
