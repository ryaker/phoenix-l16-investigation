<!-- provenance: l16-investigator runtime W1b first-hit sweep (ab67f75583bc3e272) + orchestrator static verify, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. W1b four-zoom first-hit data. Method: stampede-free (BP one stage, read at
first stop, kill). No BP missed. Scope = first-hit sample/tier, Unit-1, profile 3. **Confound flagged:** 28mm
had a `.lris` sidecar auto-loaded; 35/70/150 did NOT — so any 28-vs-rest split may be `.lris`, not tier.

# W1b — per-tier operand data + graduations

## Active bilateral window = 5 (all tiers) — RESOLVES W0 "W3 dormant"
BP `0x2f6420`, `r8d`=**5**, `r9`(chroma)=0 at all 4 tiers. ⇒ the W0-dormant W3 worker `0x2f6ad0` is dead
because the **active window is W5** (`0x2f78e0`); not a missing stage. (orchestrator-verified: B-spline/CR
caller separation below; W5 worker VA from the static jump table.)

## CNR tuning = 1.0 / 1.0 (all tiers)
BP `0x34b40a` (=`+26`, after `mov rdi,r14` loads the captured pipeline obj): `[r14+0x15d8]`=**1.0**,
`[r14+0x1624]`=**1.0** all 4 tiers ⇒ CNR runs at default multiplier/sigma (matches the compiled default
`color_denoise_multiplier=1.0`). First-hit.

## Lane-D accept/reject gate FIRES four-zoom (was 70mm-only)
BP `0x216f60` spawner (called from `0x22d250`); gate compare at `0x217ac6` (`ucomiss xmm0,xmm1; jb reject`),
xmm1=**0.25** (`0x3e800000`) all tiers ⇒ reject when 0.25 < measured. First-hit measured: 28/70/150 = 0.0
(accept), **35mm = 0.2485** (accept, but 0.0015 below the 0.25 ceiling — near-boundary). ⇒ gate + 0.25 const
confirmed live at all 4 tiers.

## Compositing gather `0x3bfe60` fires four-zoom (count is `.lris`-confounded)
BP `0x3bfe74`; mutex-guarded drain (`pthread_mutex_lock this+0x20`, flag `this+0x18`, queue head `(rsi)`);
`[r15+0x10]` first-hit tile count = 2 (28mm, .lris) / 1 (35/70/150, no .lris). ⇒ the structure (RB... no, the
linked-list drain) is 4-zoom-confirmed; the count tracks `.lris` presence, NOT focal tier (caveat).

## Resample kernel separation (VERIFIED four-zoom + static)
- **B-spline `0x2b2be0` is called ONLY from inside the terminal merge `0x3661b0`** — two sites `0x368657`
  (+9388) and `0x36a200` (+16469), orchestrator-verified `call 0x2b2be0`. ⇒ B-spline = merge interior resample.
- **Catmull-Rom `0x36f800` is called from a SEPARATE stage `0x3d0650`** (`0x3d08ce call 0x36f800`), uniformly
  all 4 tiers. ⇒ Catmull-Rom = a distinct (selected-cache/tile read-rescale) stage, NOT the merge.
This cleanly separates the two kernels by call surface across all tiers.

## Graduations (→ findings_for_codex, first-hit scope)
- `laneE_fourzoom_topology/resample_kernels_constants.md` (B-spline=merge-interior, CR=`0x3d0650` stage, both
  fire 4-zoom; kernel math already static-decoded + now caller-separated 4-zoom).
- `laneD_final_acceptance_static/accept_reject_gate_located.md` (gate + 0.25 ceiling fire 4-zoom; 35mm near-boundary).
- `laneE_fourzoom_topology/final_compositing_consumer.md` (drain structure 4-zoom; count `.lris`-confounded, noted).
- `denoise_sharpen_tone_stages_mapped.md` (CNR/bilateral/sharpen fire 4-zoom; active window=W5; CNR params=1.0).

## Stays staging (corrections applied)
- `denoise_sharpen_kernel_math.md` — bilateral active window = **W5** not W3 (W3 math was a dormant example);
  W5 inner math still OWED. gate2/gate3 still untriggered 4-zoom (only gate1 fired) → `gate2_gate3_reject_semantics.md`
  stays staging.
