> **GRADUATED (2026-06-04) → `../../opus_findings_for_codex/color_consumption_FOURZOOM.md` §1.** The CCM
> consumption is NO LONGER inconclusive: `0xa9f20` was read live on all 4 tiers and carries a REAL per-camera
> 3×3 CCM, row-sums EXACTLY [0.9642,1.0,0.8252] (= LRI Block-6 f2.2), NOT I1I2I3. The earlier entry-time
> (`0x390180`) perturbation was inert because the CCM is delivered via payload+0x14, not the entry proto
> buffer. The §1 multithread-nondeterminism finding (spike-acceptance: validate statistically not by hash)
> remains a first-class keeper.
>
> **UPDATE 2026-06-03 — the CCM apply site is now LOCATED statically** (`ccm_apply_site_located.md`): per-camera
> CCM = 4×4 apply `0xbfa20` via `setColorCorrection $_58 0x3466d0` → `0xa9f20`; matrix = `*[BayerPipelinePayload
> +0]+0x14` delivered through the closure capture (+0x20), NOT the render-entry proto buffer — which is exactly
> why the entry-time perturbation below (`0x390180`) was inert. Codex now has a concrete BP target (`0xbfa20`).
> The nondeterminism finding (§1) and structural CCM corrections (§2) below still stand.

# Lane B2 — RUNTIME (INCONCLUSIVE): Block-6 CCM consumption + a spike-critical nondeterminism finding

**Status:** `NEEDS_CODEX_VALIDATION`. Method: runtime differential rendering (28mm Unit-1 seed). The CCM
question is **NOT resolved** (honest negative, method-bound), but the probe produced two findings worth
keeping. Single seed; profile 3; `--export-fmt 4` (JPEG-as-.dng).

## 1. CRITICAL (spike-relevant): libcp output is multithreaded-NONDETERMINISTIC
5 baseline CLI renders of the SAME seed produced **≥3 distinct decoded-pixel SHA-256 states**
(`7f73c7ce`, `c1a401b8`, `35ec5ff3`); ~**48% of pixels differ** between states (up to 17 counts/8-bit),
consistent with merge/accumulation-order nondeterminism across threads. The global **per-channel MEAN is
stable only to a floor of ~0.0344 counts**.
- **Spike acceptance implication:** Phoenix output CANNOT be validated by exact pixel match against
  libcp — libcp does not match itself. Acceptance must be **statistical (mean/percentile tolerance)**, not
  byte/hash equality. This is a design fact for the eventual validation spike.
- **Differential-method bound:** only LARGE perturbation effects are trustworthy. (The earlier AWB probe's
  effect — R mean 150→249, G/B→~0.06 — is orders of magnitude above this 0.034 floor, so that CONFIRMED
  result stands. Small-effect differential tests are unreliable.)

## 2. CCM consumption — NOT CONFIRMED (method limit), with structural corrections
- **Entry-time perturbation inert (OBSERVED negative):** overwriting the heap protobuf CCM copies at
  `Renderer::render` entry (`0x390180`) — including ×20 extreme on all 14 variant-0 matrices, writes
  verified landed — produced NO decoded-pixel change above the noise floor. ⇒ the located proto-buffer copy
  is **not** the buffer the pixel path reads. The CCM is parsed into a runtime structure DURING `render()`
  (after the entry breakpoint), from another source (likely a separate deserialized/`.lris`-state copy).
- This is a METHOD-bound negative, NOT "CCM is unused." Strong LEAD it IS consumed: libcp strings
  `lt::ImageApplyColorMatrix` (`Matrix<f,3,3>` and `<f,4,4>`) and
  `lt::Internal::Pipeline::setColorCorrection(PipelineBase::ColorCorrection)` (anonymous-namespace, no
  exported symbol — can't breakpoint by name).
- **Brief corrections (OBSERVED, deterministic re-parse):**
  - **All THREE variants `{0,2,6}` share the row-sums `[0.9642, 1.0, 0.8252]`** — row-sums do NOT
    distinguish the variants (earlier packets implied only variant 2 had them).
  - Per-camera variant order in Block 6 = **2, 0, 6**; camera-id order = 0,5,2,6,3,7,4,8,13,9,14,10,11,12.
  - f2.2 CCM is stored as **9 individual wire-type-5 float fields** (tags 0d 15 1d 25 2d 35 3d 45 4d), NOT
    a contiguous array. Variant 2 = the 1472B record (carries f2.8 spectral); variants 0/6 = 519B.
  - cam0 v0 CCM = [0.5933,0.2880,0.0829 / 0.0819,1.1473,-0.2292 / -0.2842,-0.8507,1.9601]; v2 =
    [0.8996,0.1317,-0.0671 / 0.3100,1.0739,-0.3840 / -0.0572,-0.4301,1.3125]; v6 =
    [0.8107,0.0676,0.0860 / 0.2126,0.9459,-0.1586 / -0.1271,-0.4614,1.4137].

## Open / how to resolve (needs better tooling = Codex / native arm64)
- Which variant {0,2,6} is selected (fixed vs adaptive) — undetermined. Resolve by perturbing AFTER the
  mid-render CCM parse (break inside `setColorCorrection`/`ImageApplyColorMatrix` via code pattern-scan, or
  watchpoint the runtime 4×4 copy). Read watchpoints are dead under Rosetta x86_64 LLDB; pixel-hash
  differential is defeated by the nondeterminism above — so this needs single-step / native-arm64 tooling.
- Whether cam0 is a fired camera in this 28mm capture (LightHeader fired-set schema unresolved here).
