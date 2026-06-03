<!-- provenance: workflow wf_f431f343-5fd (l16-b2-crosscorpus-w6), 2026-06-03; finder reliable=True BUT orchestrator-corrected -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 4-zoom × 2-unit corpus).
**Verifier reliability:** the finder + its verifier both returned `reliable=True`, but they shared a
**wrong-field blind spot** — both read `f3.2.1` (a per-scale constant) and mislabeled it "fx," producing a
FALSE "5+5+6 refuted." Orchestrator re-parsed the binary independently (different field path) and
**corrected it below.** This is a verify-before-trust catch: a `reliable=True` workflow result was still
wrong because finder and verifier read the same wrong field.

## CORRECTED RESULT

### 1. Per-camera fx EXISTS in the K matrix → 5+5+6 focal tiers STAND (orchestrator-OBSERVED, 28mm Unit-1)
Independent re-parse (`tools/lri_field_inspect.py`, Block-3 idx3, `f13[cam]→f3→f3.2[scale0]`):
- `f3.2.1 = 818.0` is **constant across all 16 cams** (a per-scale value, NOT fx). ← what the finder read.
- `f3.2.2.1` (the K matrix `[fx 0 cx; 0 fy cy; 0 0 1]`) carries **per-camera fx**:
  - cam0 = `3375.88`, cam5 = `8283.43`, cam10 = `18794.65`, cam15 = `18655.07`.
- ⇒ fx clusters **5+5+6**: 28mm `{0–4}≈3376`, 70mm `{5–9}≈8300`, 150mm `{10–15}≈18700`. The earlier
  wave-5 + committed `verified_field_map.md` finding is **CONFIRMED**; the finder's "fx constant / 5+5+6
  REFUTED" is **rejected**. (Independently corroborated: wave-6 thread-2 distortion found exactly **3
  optical tier groups**.)

### 2. Block-6 excluded pair {1,15} is corpus-stable (OBSERVED, all 8 seeds — finder valid, simple set check)
Every seed's Block-6 = 42 sub-records = 14 camera-ids × 3, with exactly **ids 1 and 15 absent** across all
4 zooms × both units. With §1: id 1 = a 28mm camera, id 15 = a 150mm camera — the excluded pair is one
camera from each **outermost** tier; the middle 70mm tier loses none. id 0 = reference camera
(Block0.field5). Block-6 LELR index = 6 (11-block seeds) / 7 (12-block seeds) — **tracks block-count, not
focal tier** (so "idx6 for all 35mm" is false: U1_35=idx6, U2_35=idx7).

### 3. DOWN-LABELED / not trusted (from the same agent that misread fx)
The finder reported a Block-3 "calibration-MODEL split" `WWWWWTTTWTTTTTWW` = simple/identity `{0,1,2,3,4,8,14,15}`
vs full-distortion `{5,6,7,9,10,11,12,13}` (an 8/8 split distinct from the 5+5+6 focal tiers). Given the
fx-field error, this is **LEAD only, unverified** — needs an independent re-parse of the actual distortion
fields per camera before it is trusted. (Note: wave-6 thread-2 found p1=p2=0 for ALL 16 cams and 3 tier
groups, which does not obviously match an 8/8 "simple vs full" split — so this LEAD is in tension and must
be re-checked, not cited.)

## Open
- Re-verify the 8/8 distortion-complexity split independently (or discard it).
- Why Block-6 drops exactly one outer-tier camera per end (id 1 of 28mm, id 15 of 150mm) — structural
  reason unknown (LEAD: a 14-slot calibration topology).
