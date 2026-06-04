<!-- provenance: runtime probe agent abbfa81e (single 28mm render), 2026-06-03 -->
> **CORRECTED + GRADUATED (2026-06-04) → `../../opus_findings_for_codex/cgroup_runtime_FOURZOOM.md` §4.**
> ⚠ The **"L2-4=0 / only L0,L1 fire / zoom-independent" claim below is REFUTED.** It came from a python
> script-callback breakpoint that **silently drops hits under Rosetta multi-thread**. The reliable native
> drain-counter shows **L2-4 (`0x3d0650`) fires on every tier** and counts are **tier-VARYING**: 28mm
> ~298/343/362 (L0/L1/L2-4, 2-run reproducible), 35mm 232/280/232, 150mm 63/80/59. The merge runs a real
> multi-level pyramid. (70mm native re-measure still owed.)

**Status:** GRADUATED(corrected) → cgroup_runtime_FOURZOOM §4 (was NEEDS_CODEX_VALIDATION; the L2-4=0 claim is REFUTED — python hit-drop artifact).
**Verifier reliability:** single-probe OBSERVED (breakpoint tally + backtrace); not independently re-run. Scope-bound to this one render.

# Lane E — RUNTIME: which PipelineCache levels fire + the scheduler topology (28mm)

## Prediction tested → REFUTED
Predicted all 5 levels (0..4) fire as a Gaussian-octave pyramid with a cross-level upsample+add recombine.
**Refuted:** only levels 0 and 1 fire; no cross-level add in the traced chain.

## OBSERVED (one render, L16_02130 28mm, profile 3; BP at libcp 0x3ec9df = after `movl 0x18(%rax),%eax`, %eax=level)
- **Level fire tally — 282 dispatcher hits:** level 0 = **250** (→ 0x3ec770, the IRAMP N→1 camera merge);
  level 1 = **32** (→ 0x3ebb80, single-source resample); **levels 2,3,4 = 0** (the 0x3d0650 rescale branch
  of THIS dispatcher never taken on this render).
- **Driver:** single unique caller of the dispatcher = per-tile worker **0x3d47d0** (reaches it via indirect
  vtable call `callq *%rax` at 0x3d4840, vtable+0x30), 282/282 hits.
- **Call chain (both level-0 and level-1):** `0x3adf30` (polymorphic task scheduler — body is `callq *%rax`
  vtable dispatches) → task-type split (L0: 0x3b0740→0x41a7d0; L1: 0x3bb2b0) → **0x3d0650 (RECURSIVE —
  appears as ancestor of both, re-enters the dispatcher at L0/L1, not a level-2..4 leaf)** → 0x3d01b0 →
  **0x5440 (tile-grid splitter:** `imull %r13d,%eax`@0x54c9 = tiles_x*tiles_y; ==1 tile → direct vtable
  worker dispatch `callq *0x30(%rax)`@0x5506; else loops building sub-tasks) → 0x3d47d0 → dispatcher.
- **Topology = a recursive TILED TASK SCHEDULER, NOT a pyramid-collapse loop.** Each tile writes its result
  into its descriptor at `(%r14)+0xf0` (dispatcher tail 0x3eca4b→0x3e5720) — per-tile-descriptor output,
  not a global pyramid add.

## Recombine (the Lane E question) — NOT located (behind indirect dispatch)
- NO cross-level upsample+add in the observed driver chain (0x3adf30 / 0x3d01b0 / 0x3d0650). 0x3d0650's only
  FP ops are scalar addss/mulss/subss on scale/coords (0x3d0789..0x3d0885), not pixel `addps`.
- 0x3adf30 is dominated by indirect `callq *%rax` (0x3adfcc, 0x3adff1, 0x3ae0b2) — the per-level/per-tile
  outputs are consumed behind these. The recombine/assembly site is genuinely behind indirect dispatch
  (not crossed here). Next: BP those vtable sites + find where `descriptor+0xf0` tile outputs are read back.

## Scope / caveats
- ONE render, 28mm, profile 3, Unit-1 (L16_02130). Levels 2-4 may fire for 70/150mm tiers or other profiles
  — "levels 2-4 never fire" is bound to THIS render. Did NOT cross the indirect dispatch to the recombine
  store; "no cross-level add" = observed-absent-in-traced-chain, not proven-absent. Did NOT re-verify the
  level-0 N→1 reduction here (only that level 0 routes to 0x3ec770 250×).

## GENERALIZATION to 70mm (runtime probe acd4551d, single 70mm render L16_03434, OBSERVED)
Same topology: level 0 = **221** hits (IRAMP merge), level 1 = **48** (resample), levels 2,3,4 = **0**.
⇒ the level/octave structure is **zoom-independent** (resolution-support), NOT focal-tier-dependent. The
L0/L1 ratio shifts (28mm 250:32≈7.8:1; 70mm 221:48≈4.6:1) — LEAD (plausibly tile-count/crop differences),
not a finding. levels 2-4 (the 0x3d0650 rescale leaf) fire 0× on BOTH zooms ⇒ coarse dim-pyramid octaves
appear cache-only / not rendered under bridge HDR. Lane E reframe: a single LRI render = one full bridge
image; the "four zooms" are 4 separate captures (cross-validation), and within one capture the focal-spanning
5+5+6 cameras combine via the **level-0 camera merge** (0x3661b0). Open: the L0/L1 tile-output recombine
site (behind 0x3adf30 vtable dispatch). 70mm = Unit-1; Unit-2 twin + other profiles not tested.
