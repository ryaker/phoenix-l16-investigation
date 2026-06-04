<!-- provenance: l16-investigator finder (static disasm) + orchestrator re-extraction of load-bearing VAs/consts, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine; finder + orchestrator-verified). Maps the blind-spot stages
from `BLIND_SPOTS_discovered_stages.md` (denoise/sharpen/tone) — CNR fully, bilateral partially, sharpen
structurally. Binary `libcp.dylib` x86_64.

# Denoise / Sharpen / Tone — the un-mapped stages, now mapped (CNR fully)

## 1. ColorNoiseReduction (CNR) — FULLY MAPPED (VERIFIED)
- **Apply body = `0x34b3f0`** (`setColorNoiseReduction $_77`), SHARED by all 3 payload variants
  (Bayer/BayerFloat/Color; trampolines `jmp 0x34b3f0`). Reads two params from the captured **pipeline object**
  `r14`: `0x34b684 movss xmm0,[r14+0x15d8]`, `0x34b68d movss xmm1,[r14+0x1624]`, then `0x34b6bb call 0x307ee0`.
- **Worker `0x307ee0` math (VERIFIED):**
  - `levels = max(0, floor( log2f([+0x15d8]) + 5.0 ))` — `log2f` stub `0x556002`, **bias 5.0** `0x5f1040`
    (`0x307fce call; 0x307fd3 addss [0x5f1040]; 0x307fdf maxss; 0x307fe3 cvttss2si`).
  - `variance = ([+0x1624]·[+0x15d8])²`; per-level weight `= ldexp(1, -2·level)·variance = 4^(-level)·variance`
    (`ldexp` stub `0x555fde` @`0x3080ac`; `mulsd` @`0x3080b1`) ⇒ a **multi-scale (pyramid) noise-variance ladder**.
  - Inner per-tile kernel `0x3085a0` (captureless task, tiled-for `0x5440`): per-pixel **local color
    covariance / structure tensor** (Σc·c, cross terms, α-weighted; `rsqrtps` `0x30874c`; 3×3 build) ⇒
    **covariance-based chroma noise reduction — NOT bilateral, NOT NLM.**
- **Installer `0x33d6a0`** (a SIBLING of CCM's `0x335620`, NOT the same): selector on `esi`; constructs the 3
  std::function variants and writes them into pipeline stage slots `[rbx+0x540]`, `[rbx+0x120]`, `[rbx+0x960]`.
- **Param source = config/tuning-profile** (`color_noise_reduction.color_denoise_multiplier` @`0x6359bc`,
  `.type` @`0x633e44`), landed into the pipeline settings object at `+0x15d8`/`+0x1624` — **NOT the LRI, NOT a
  payload offset** (contrast CCM's matrix at `BayerPipelinePayload[0]+0x14`).

## 2. Pipeline order — CNR registers BEFORE CCM (OBSERVED, registration order)
Both installers are called from one master pipeline-build function: **CNR `0x33d6a0` @`0x31867b`** (finder),
**CCM `0x335620` @`0x318dc8`** (orchestrator-VERIFIED). `0x31867b < 0x318dc8` ⇒ **CNR before CCM** in the build
sequence. ⚠ registration order, NOT proven to equal runtime execution order (static only).

## 3. Bilateral denoise — MAPPED (separate subsystem)
- **Launcher `0x2f6420`**: `idx = window_size−3`; jump table `0x2f6a08`; valid **W∈{3,5,7,9}** (odd→throw
  "Unsupported bilateral kernel size!" `0x633252`). W3 worker = `0x2f6ad0`. Per-W vtables 0x65a4e0/0x65a568/…
  dispatched via tiled-for `0x5440`.
- Operates in a **decorrelated color space**: initializer `0x2f63f0` loads the **I1I2I3/Ohta basis** from
  `0x5f2380`=`[1/√3,1/√3,1/√3,1/√2]`, `0x5f2390`=`[0,-1/√2,1/√6,-2/√6]` into BSS `0x670ad0/ae0/af0`.
- **REFUTED prediction:** the static float pool is NOT spatial/range Gaussian sigmas — sigmas are computed
  per-call from params; the pool is the fixed decorrelation matrix.
- NLM / PatchNLM<4> bodies present (vtables 0x65abb0, 0x668950) but launchers/math NOT decoded — UNKNOWN.

## 4. Sharpen + tone — PARTIALLY MAPPED (HYPOTHESIS on math)
- `lt::Internal::SharpenLineFactory<f>` = factory + shared_ptr + **per-scanline line-worker** (ctor ~`0x360b00`,
  methods `0x361020`/`0x361490`) ⇒ a **separable line-based sharpen**. Config `tone_mapping.sharpening` /
  `.sharpening_scale`.
- A distinct **Laplacian-pyramid clarity/tone path** (`tone_adjust.lpyr_clarity`, + `lpyr_shadows/highlights/
  sigma/percentiles/samples` strings `0x6335da..0x633650`) separate from the unsharp `sharpening` path.
- Line-kernel math (unsharp vs Laplacian-pyramid) NOT decoded — HYPOTHESIS only.

## 5. CLEAN-ROOM / LEGAL implication (important — new)
These stages' parameters come from a **JSON/tuning-profile config → pipeline settings object** (keys
enumerated `0x326340..0x326e60`), NOT from the LRI and NOT published. ⇒ like the tone-curve LUTs, the
denoise/sharpen/tone **tuning values are app-level Lumen IP, not LRI-resident** — a Rule #0 / item-#27-class
problem: Phoenix must either derive its own denoise/sharpen tuning or treat libcp's as reference-only. The
ALGORITHMS (covariance chroma-NR, bilateral, line-sharpen, Laplacian clarity) are reimplementable; the
CONSTANTS/tuning are not LRI-derivable.

## Cross-check resolution (verify-before-trust)
The I1I2I3 basis at `0x5f2380` is now found by THREE independent probes (CCM decoy `0x300570`, post-merge
`__bss 0x671980`, bilateral `0x2f63f0`). The earlier "9th-constant discrepancy" (CCM finder `0.40825` vs my
re-read `0.0`) is RESOLVED: the table slot is genuinely `0.0`; the `0.40825` is supplied by a **code immediate**
(`0x3ed10625`), not the table — both finders were correct about different sources.

## Residuals (NEEDS_CODEX_VALIDATION)
- NLM/PatchNLM launcher + math; sharpen line-kernel math (unsharp vs Laplacian); whether bilateral is a
  registered std::function stage vs inline driver; runtime execution order vs registration order; the config
  deserializer offsets that populate pipeline `+0x15d8`/`+0x1624`; which denoise path(s) actually fire in
  bridge HDR (all static here — no runtime).
