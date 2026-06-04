<!-- provenance: l16-investigator runtime four-zoom census (acd7b507969083d99) + orchestrator static spot-checks, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. **This is W0 = the four-zoom FIRING MAP (presence/counts only), the floor
that SCOPES the W1 data sweep — it is NOT a graduation.** No packet graduates on firing alone. Runtime: one
render per tier (28mm L16_02130 / 35mm L16_03041 / 70mm L16_03434 / 150mm L16_02285), Unit-1, profile 3,
JPEG-as-.dng. libcp fileVA==offset; BPs bound via `--shlib libcp.dylib --address`.

# W0 — four-zoom firing census (21 stages × 4 tiers)

**Headline:** 19 of 21 instrumented stages fire at ALL four tiers; 2 dormant at every tier (under tested
render). Firing presence is **tier-invariant** — no stage switches on/off between focals; the 5+5+6 camera
tiers do NOT gate stereo-cost firing.

## Firing map (Y = fired ≥1× in a run-to-exit render)
All Y at 28/35/70/150: CNR apply `0x34b3f0`, CNR worker `0x307ee0`, CNR installer `0x33d6a0`, bilateral
launcher `0x2f6420`, sharpen ctor `0x360a00`, sharpen method `0x361020`, stereo cost body `0x2732f0`, stereo
state builder `0x275630`, stereo runPass `0x276790`, depth upsample `0x29ed90`, CCM setColorCorrection
`0x3466d0`, CCM 4x4 apply `0xbfa20`, CCM orch `0xa9f20`, IRAMP merge `0x3661b0`, score kernel `0x36cde0`,
undistort `0x261940`, resample B-spline `0x2b2be0`, Catmull-Rom `0x36f800`, compositing gather `0x3bfe60`.

**DORMANT (0 hits, all tiers, double-confirmed — "0 under this tested render," not "never"):**
- **bilateral W3 worker `0x2f6ad0`** — launcher fires 2,400–3,000× but the W3 variant never runs ⇒ active
  bilateral window ≠ W3 under bridge HDR.
- **stereo driver `0x2730c0`** — cost body/state/runPass fire ~3,900–4,000× but this driver never runs.

## Magnitudes (28mm / 70mm, run-to-exit)
Tier-invariant (structural): CNR installer 38/38, runPass 4038/4038, setColorCorrection 192/192, depth
upsample 1/1. Tier-varying (lower at tele, smaller coverage): CNR apply 658/525, CNR worker 668/528, bilateral
launcher 2979/2351, sharpen ctor 3142/2445, sharpen method 2827/2221, CCM 4x4 1306/1018, compositing gather
5/4. Stereo state builder 3891/3852, cost body presence-confirmed.

## CORRECTIONS this census forced on staging packets (the point of four-zoom)
1. **`stereo_cost_math_decoded.md`:** the `0x2730c0` driver "records>3 → calls `0x2732f0`" topology is DORMANT
   at runtime. The `0x2730c0→0x2732f0` call edge exists statically (`0x273103`) but never fires in bridge HDR.
   The cost body's LIVE caller is via `runPass 0x276790` (other static callers of `0x2732f0`: `0x272ca9`,
   `0x2773dc`, `0x278a57`; `0x2773dc` is in the runPass region). Cost MATH stands (body fires 4-zoom); the
   driver/gating description must be corrected to the runPass path. → W1 must capture the live caller chain.
2. **`denoise_sharpen_kernel_math.md` / `denoise_sharpen_tone_stages_mapped.md`:** bilateral W3 worker
   `0x2f6ad0` is DORMANT; the active window is not W3 — W1 must identify which W{5,7,9} worker the launcher
   dispatches to. Sharpen ctor address corrected `~0x360b00`→**`0x360a00`** (0x360b00 is `nop` padding;
   0x360a00 = `push rbp` entry — orchestrator-verified).

## Method note (critical for W1 under Rosetta)
Per-hit Python BP callbacks and `--auto-continue`/`--one-shot` STALL renders 30+ min (multi-threaded BP-stop
stampede under Rosetta). The working harness = "drain": arm all BPs no-auto-continue, on each stop mark+DELETE
the fired BP then Continue → exactly one stop per BP, runs to exit. **W1 data capture must therefore stop
SELECTIVELY** (a few BPs per render with state reads) to avoid the stampede — likely 1-2 stages per render,
several renders per tier. This makes W1 even more render-bound than W0.

## Scope
One render/tier, Unit-1 only, profile 3, JPEG-as-.dng. Firing/counts only — NO operand/data capture (that is
W1). Dormancy is tested-condition-bound. Hot per-pixel controls presence-confirmed, not exact-counted.
