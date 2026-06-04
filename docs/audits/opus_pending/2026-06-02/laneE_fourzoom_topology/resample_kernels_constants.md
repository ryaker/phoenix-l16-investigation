<!-- provenance: orchestrator static disasm + constant byte-decode of 0x2b2be0 and 0x36f800, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm + float constant byte-decode). Verify-before-trust
check on the handoff's resample-kernel labels ("B-spline `0x2b2be0` / Catmull-Rom `0x36f800`"). Binary:
`libcp.dylib` Mach-O x86_64.

# Resample kernels — `0x2b2be0` = cubic B-spline CONFIRMED; `0x36f800` "Catmull-Rom" label REFUTED

## `0x2b2be0` = CUBIC B-SPLINE (CONFIRMED — handoff label correct)
Constant pool (byte-decoded from RIP-relative refs in the body): `0.166667 (=1/6)`, `3.0`, `6.0`, `-6.0`,
`4.0`, `2.0`, `1.0`, `0.015625 (=1/64)`, `-0.1875`, `0.0`. Interval tests against `1.0` and `2.0` (support
[-2,2]). These are the **textbook cubic B-spline basis**:
- `|x|∈[0,1): (1/6)(3|x|³ − 6|x|² + 4)` ⇒ coefficients {3, −6, 4} × 1/6 (all present).
- `|x|∈[1,2): (1/6)(−|x|³ + 6|x|² − 12|x| + 8) = (1/6)(2−|x|)³` ⇒ {6, 2} present.
⇒ **clean-room: Phoenix's separable resample uses the standard cubic B-spline weights — reimplementable from
the published basis (Rule #0 OK, no copied bytes).** (The `1/64`, `-0.1875` are likely a coarser/secondary
path or a fixed-fraction sub-sample table.)

## `0x36f800` "Catmull-Rom" label = REFUTED by its constants (kernel identity OPEN)
`0x36f800` IS a 1/6-normalized **piecewise polynomial** (Horner form: `mulss x,x` square then
`mul;add;add;mul` chains; two parallel polynomial pieces selected by `ucomiss` vs `1.0` and `2.0`) — so it is
*a* spline-class kernel. BUT its constant pool is `{0.166667(1/6), 9.0, 15.0, -15.0, -3.0, 6.0, 2.0, 1.0,
-12.0, -0.375(=-3/8), 0.015625(1/64), 0.075274, 38.666668(=116/3)}`, which matches **NEITHER**:
- **Catmull-Rom** (would need `1.5, -2.5, 1, -0.5, 2.5, -4, 2` — the diagnostic `-0.5`/`2.5`/`-4` are ABSENT;
  it has `-0.375` and `9/15`, not `2.5`), NOR
- **cubic B-spline** (would need `{3, -6, 4}`; it has `{9, ±15, -3, -12, 38.667}`).
⇒ The handoff's "Catmull-Rom `0x36f800`" is **UNVERIFIED and contradicted by the constants.** Candidate
identities (LEAD, not proven): a higher-order (quartic/quintic) spline, a B-spline **derivative** kernel (for
gradients/Jacobian), a windowed-sinc/Lanczos with precomputed terms, or a misattributed VA. Exact identity
needs full register-tracked polynomial reconstruction of the two pieces.

## Action taken
Corrected the handoff RESAMPLE line: `0x2b2be0` = cubic B-spline (confirmed); `0x36f800` = unidentified
1/6-normalized piecewise-polynomial kernel, NOT Catmull-Rom.

## Residuals (NEEDS_CODEX_VALIDATION)
- Exact identity of `0x36f800` (reconstruct both polynomial pieces from the decoded constants + register flow).
- Confirm `0x2b2be0` is on the inter-level resample path at runtime (static-only here; the IRAMP levels 1-4
  are the resample octaves per the dispatcher finding).
- Role of the secondary constants (`1/64`, `-0.1875` in B-spline; `0.075274`, `116/3` in `0x36f800`).
