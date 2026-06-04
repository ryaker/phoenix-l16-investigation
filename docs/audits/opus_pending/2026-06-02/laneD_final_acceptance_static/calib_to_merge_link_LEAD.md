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
