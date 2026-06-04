<!-- provenance: runtime probe a1818b7 (one 70mm render) + LRI byte-search, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, runtime LLDB + LRI byte-scan, single 70mm seed).

# Merge projection transform: radial component is EFFECTIVELY IDENTITY (NOT the LRI distortion)

## Prediction tested → REFUTED (for the radial component)
Predicted the merge projection `0x3e42e0`'s transform-state `+0x100` radial table = the LRI Block-3
f3.3.2.5 distortion LUT (or derived). **Refuted.**

## OBSERVED (one 70mm render, L16_03434)
- Projection transform-state P = `*(rsi+0x8)` = single render-static object (this run `0x7fc2df00dc00`),
  identical across all hits (shared by all source records).
- P matrix `P+0x118 f[12]` = `[2075.0, 1590.0, 0.998077, ~0, 2.99976, ~0, 0.998077, 1.99976, ~0, ~0,
  1.0000001, 1.62790]` — `2075/1590` = center fields (≈half of a 4150×3180 frame); the 0.998/2.0/3.0 block
  is a small near-identity 3×3 (computed values, not LRI byte-matches → LEAD whether K-derived).
- Radial table `*(P+0x100)` = monotonic ramp from exactly `1.0` (`0x3f800000`), +~1 ULP/entry; idx109 =
  `1.0000164`; extrapolated over [0,0xfff] caps ~`1.0006` ⇒ **≤0.06% radial correction = effective no-op.**
- **LRI byte-scan (whole 178MB 70mm LRI), aligned float32, any ≥30-long monotonic run in [1.0,1.01]: 0 hits.**
  The P radial ramp is NOT stored in the LRI; a real Brown-Conrady/f3.3.2.5 LUT gives multi-% corner
  correction, which this table is not.

## Conclusion
The **merge's per-source projection applies NO meaningful radial distortion** (radial ≈ identity). It does a
small 3×3 + center-recenter (camera-to-reference geometric alignment). ⇒ **the LRI Brown-Conrady distortion
(Block-3) is applied at a DIFFERENT pipeline stage, not in the IRAMP merge projection.** Clean-room: Phoenix
applies undistort as a separate stage (likely pre-merge), and the merge works on already-normalized coords.

## Tooling note
`breakpoint set --shlib libcp.dylib --address 0xVA` BINDS; `target modules add`+`BreakpointCreateBySBAddress`
did NOT bind (future runtime sessions).

## Open
- Where IS Block-3 distortion applied? (separate undistort stage — new thread, static-findable.)
- P's constructor (built before first use): builder frames `0x3e5b75 / 0x3e40ac / 0x3e2f58 / 0x3e4b0e /
  0x260bfe` — needs a write-watchpoint render. Whether P's 3×3 is K-derived: LEAD.
