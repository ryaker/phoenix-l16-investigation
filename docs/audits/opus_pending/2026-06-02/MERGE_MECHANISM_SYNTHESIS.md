# Merge mechanism — consolidated quarantine synthesis (waves 1–4, 2026-06-03)

**Status:** every line `NEEDS_CODEX_VALIDATION`. Static disassembly only (no runtime), except where it
cites Codex's already-committed runtime evidence under `docs/evidence/`. Weak labels: **OBSERVED** =
re-extracted from the binary (and independently re-extracted by a second agent); **LEAD** = inferred.
This doc only summarizes claims that live in the per-lane packets; it adds no new claim. Authority = the
ledger; this is quarantine, not canonical.

Binary: `libcp.dylib` (Mach-O x86_64, file-offset==VA).

## The two-stage split (the key clarifying result, wave 4)

The "receding accumulator" across waves 1–3 resolved into **two distinct subsystems** that should not be
conflated:

1. **Pixel merge (terminal N→1) = `0x3661b0`** (IRAMP "ImageResolutionAmp", called by
   `PipelineCache::processLevel0 0x3ec770`). **OBSERVED:** N contributors (count `[r13+0x10]`, per-
   contributor weight plane `[r13+0x28]`, where `r13 = [arg0+0x8]`) are accumulated by the weighted add
   at `0x36aa30/0x36aa53/0x36aa57` into a tile buffer, then alpha-blended (`0x36ab88..0x36ac38`) into the
   real output image at `[arg0+0x38]` (`+0x18` stride, `+0x20` data ptr). This is the terminal pixel
   reduction. Both halves of the "is it the merge" gate are met: entry `0x365960` checks
   `count(+0x258 vec)==count(+0x270 vec)` (accepts N>1), and `0x3661b0` reduces N→1 into the output image.

2. **Geometry / warp-record builder = `0x216f60`** (+ the `0x23faf0` State family) — **CANDIDATE.** Its
   `0xe6ba0`/`0x1f0a00`/`0x218390` cluster does keyed record select + 3×3/affine matrix compose + sincos
   rotation build; `0x25e4b0` initializes an identity-homography/affine matrix; the `-0x6c8/-0x6c4` `mulss`
   is a one-shot `coord*scale` (no add-back, no loop). It touches **no pixels** and contains **no N→1
   reduction**. It builds transform/geometry records.

**Reconciliation / correction (verify-before-trust):** a wave-4 finder hypothesized `0x216f60`/`0x23faf0`
produce the `0x3661b0` source/warp vectors. **Codex's committed runtime evidence refutes that link:**
`lldb_src2_descriptor_origin_four_zoom.md` resolves the indirect dispatch at `0x3ebf5d`
(`callq *%rax` via `PipelineCache+0x1d8`, vtable +0x18) to `0x3ebb80 → FusionCacheBayer → 0x406a10 →
worker 0x3ed2e0`. So the IRAMP source/warp-descriptor producer is **FusionCacheBayer**, NOT the
`0x216f60` builder. ⇒ `0x216f60`'s downstream consumer is a **separate open question** (likely the
State/prefusion path, Codex's `0x23faf0` thread); do not assert it feeds the IRAMP merge.

## Inside the pixel merge `0x3661b0` (waves 1–3, OBSERVED unless noted)

- **Args** (from caller `0x3ec7ac..`): `src1=cache+0x238` (geometry ANCHOR — warp coords validated/clamped
  to src1 dims `0x366c77`/`0x36a004`), `src2=cache+0x248` (geometry; `0x374ac0` margin-zero-fills src2's
  own buffer — 4 `__bzero` loops top/bottom rows + left/right columns — NOT a sampling clip),
  warpfield-vec `+0x270`, source-image-vec `+0x258`, scale `+0x1e8`, ROI/dest. **src1/src2 are geometry
  descriptors, not the image buffers being merged.**
- **Contributor loop:** per-contributor index-validity gate (`0x36930f` `0x80000000` sentinel → skip that
  contributor's SAD/score/warp for the tile, write reject `0x80000000_80000000`). Loop bound
  N = source-record vector span `(end-begin)>>7 /5`. Per contributor: SAD block-match motion search
  (`mpsadbw`×16 + `phminposuw`).
- **Score (`0x36cde0`, weights each contributor, stored UNCONDITIONALLY at `0x369e91` — does not gate):**
  `sqrt(hmin(A)·hmin(B))` where both factors are **multi-scale wavelet-domain** reductions over **4 dyadic
  scales** (1:2:4:8, consts `0x5fdb10`), with a **raw** SSIM stabilizer K=0.01 (`0x5fdc50`, NOT (K·L)²)
  applied upstream, then an affine remap `(ssim−0.8)·(1/0.19)` clamped [0,1] (`0x5fdc60`/`0x5fdc70`). I.e.
  a wavelet-domain SSIM-class quality metric. (Earlier A6 "q1=SSIM × q2=wavelet" split is REFUTED.)
- **Reduction operator:** `1/Σscore`-normalized weighted average — Σscore loop `0x36a7d8..0x36a92e` →
  `rcpss 0x36a938` → broadcast scale (`0x19e7d0`) → lane-3 `=reciprocal·0.2` (`0x36aa35`) → separable
  weighted add (`0x36aa30..0x36aa57`). **No `maxps/blendvps` in the pixel path → soft normalized average,
  not hard select.** (H1 "src1/src2 = value/weight pair + per-pixel divide" REFUTED.)
- **Output shaping tail:** lane-3 (the `recip·0.2`) is used as a per-pixel gain on a `2.0`-scaled detail
  delta, clamped ±0.1, added (the A5 guided-detail-transfer), then a **3×3 matrix at `0x36acf0` loaded
  from `__DATA,__bss 0x671980` (S_ZEROFILL, runtime-populated)** — classified (on Codex's committed
  runtime values) as an orthonormal color-decorrelation/PCA rotation — then lane-3 forced to 1.0.

## Acceptance / rejection (Lane D)
`0x218b30` is a **statistics reducer** (mean clamped score → `*(%r14)`; threshold-exceed fraction →
ret xmm0), NOT a record materializer; its sole caller `0x218e20` is an **array-filler** (per-index score/
fraction arrays), dispatched indirectly via `__const 0x6580e0` (gate consumer = runtime). Per-pair accept
= both lanes strictly >0; sentinel `(-1,-1)` rejected; `<8` positive pairs → clean early return skipping
the merge body.

## Residual unknowns — all RUNTIME (Codex's domain) or already in committed evidence
1. IRAMP source/warp producer — **RESOLVED by Codex** (FusionCacheBayer `0x406a10`/`0x3ed2e0`).
2. `0x216f60` geometry-record consumer + record-count==N — runtime (Codex `0x23faf0` thread).
3. Final `sqrt` operand certification at `0x36e511` — runtime tag (low marginal value; static structure
   already strong).
4. `__bss 0x671980` color matrix: written once at init (constant) vs per-image — runtime write-watchpoint
   (clean-room relevance: constant ⇒ calibration; per-image ⇒ Phoenix computes it).
5. `0x218e20` gate consumer behind the `__const 0x6580e0` indirect dispatch — runtime.

**Boundary statement:** the statically-tractable merge-mechanism surface is now comprehensively mapped;
the remaining merge-core unknowns require runtime, and the single most decisive one (the producer link)
is already crossed in Codex's committed evidence. This lane has reached the "runtime / Codex-validation"
boundary.
