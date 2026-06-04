<!-- provenance: orchestrator cross-read of committed bundle_proof_src1_projection_callable_transform.md vs 0xf33d0, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. This is a **LEAD (region overlap), NOT a confirmed link** — see the
honest caveat. Cross-reads committed evidence against the Lane D accept-consumer finding.

# Lane D — calib→merge link: the current CalibStage region overlaps the merge's projection-transform state (LEAD)

## The overlap
- **Accept writes (my `0xf33d0` finding):** the accepted candidate's CURRENT CalibStage goes to State
  `+0x12c..+0x17c` as vec4 records — 16-byte writes at `+0x12c` (rec1 v0), `+0x13c` (rec1 v1), `+0x14c`
  (rec1 int), `+0x150`/`+0x160`/`+0x170` (rec2), `+0x174/+0x178/+0x17c` (rec3 ints).
- **Merge reads (Codex committed `bundle_proof_src1_projection_callable_transform.md`):** the IRAMP
  projection/coordinate-transform `0x3e42e0` reads a 3×3 matrix from State `+0x120..+0x140`
  (row0 `+0x120/+0x124/+0x128`, **row1 `+0x12c/+0x130/+0x134`**, row2 `+0x138/+0x13c/+0x140`), plus scales
  `+0x0f8/+0x0fc`, table base `+0x100`, centers `+0x118/+0x11c`.
- ⇒ both touch the SAME State object's `+0x12c..+0x140` region. **LEAD:** the per-render refined calibration
  (current CalibStage) feeds the merge's projection transform — i.e. accept gate → CalibStage → projection
  matrix used by the pixel merge. This would close the calib→merge link.

## HONEST CAVEAT (do NOT overclaim — region overlap ≠ field match)
The alignment is NOT clean: `0xf33d0` writes 16-byte **vec4 records** starting at `+0x12c`, whereas the
projection treats `+0x12c/+0x130/+0x134` as three separate floats of a matrix that STARTS at `+0x120`.
The projection's row0 (`+0x120..+0x128`) and the scales/centers (`+0x0f8..+0x11c`) are NOT in `0xf33d0`'s
current-CalibStage write. So this is a region-overlap LEAD, not a proven field-by-field match — it could be
the same State (calibration feeds projection) OR a different object reusing similar offsets. (I nearly
asserted "the offset matches" — corrected; same wrong-field trap as the f3.2.1-vs-K-matrix case.)

## Decisive test (runtime, one 70mm render; not yet run)
BP `0xf33d0`: capture rdi(State addr) + the values written at `+0x12c`. BP `0x3e42e0`: capture the
transform-state addr (from callable `+0x8`) + the values read at `+0x12c`. If the ADDRESSES match (same
object) and the values written by accept later appear at the projection read → link CONFIRMED. (Read
watchpoints dead; use BP-stop pointer/value compare.) Until then: LEAD only.

## VERDICT (runtime probe a1d4b4b, one 70mm render): the predicted direct link is REFUTED
Decisive same-object test:
- Accept-gate `0xf33d0` current-branch State objects = heap family **`0x7f8099f1xxxx`** (10 distinct); their
  `+0x12c` holds LARGE per-frame-varying calibration floats (e.g. `8270.35`, `18149.125` — fx-magnitude,
  re-estimated per frame; factory branch first writes identity `[1,0,0,0]`).
- Projection `0x3e42e0` transform-state = a **single render-STATIC object `0x7f809b054000`** for ALL 80
  sampled hits; `+0x12c`=`[-0.0, 0.998077, 1.999756, -0.0]`, `+0x120`=`[0.998077,-0.0,2.999756,-0.0]`,
  invariant; radial/distortion coeff table ptr at `+0x100` (cvttss2si radius, clamp [0,0xfff]).
- **OVERLAP(accept States ∩ proj state) = ∅; accept `+0x12c` (thousands) ≠ proj `+0x12c` (~0.998). NO flow.**
⇒ The accept-gate per-frame calibration State is **NOT** the projection matrix the merge reads. They are two
separate object families. The merge projection uses a render-static transform (with a radial LUT —
**looks like the LRI factory intrinsics/undistort**, ties to laneB2's distortion model), distinct from the
per-frame accept-gate refinement. The LEAD above (region-overlap) is therefore explained as coincidental
offset reuse across two different object types, NOT a shared object.

## Verify-before-trust catch on COMMITTED evidence (for Codex)
Committed `bundle_proof_src1_projection_callable_transform.md` states `0x3e42e4: state = *(rdi+0x8)`. That
register is WRONG: actual disasm `libcp[0x3e42e4]: movq 0x8(%rsi),%rax` ⇒ transform-state = `*(rsi+0x8)`
(rsi = callable `this`; rdi = the output 2-float point buffer, `movss %xmm0,(%rdi)` at +252). Minor but
load-bearing for anyone re-probing this site. (Quarantine note only; committed doc not modified.)

## Now-open
- Where DOES the accept-gate per-frame calibration (`0x7f8099f1xxxx` State) get consumed? (indirect path
  unknown — not the projection.)
- What builds the projection's static transform `0x7f809b054000`? (LEAD: LRI factory intrinsics/distortion
  = laneB2 Block-3; would connect merge-projection ← B2 factory calibration.)
