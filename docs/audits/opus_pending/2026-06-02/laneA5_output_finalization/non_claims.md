# Lane A5 — Non-claims

1. **Not proven that `0x2b2be0`/`0x36f800` write the FINAL output image** (vs an intermediate pyramid
   level). CANDIDATE; confirm at runtime by watching the dst pointer (`0x20` of `0x38(r15)`) against the
   known output buffer base.
2. **Cubic-kernel identity is a LEAD, not a fact.** The 64-entry LUT loop + piecewise polynomial is
   grep-confirmed; the specific kernel family (Catmull-Rom / B-spline / Lanczos-ish) and its coefficient
   values were NOT decoded.
3. **The two views `-0x1730`/`-0x17d0` are not identified.** LEAD: two planes/levels of the same merged
   result (same scale doubles feed both). Not confirmed.
4. **"No acceptance gate" is scope-bound to `0x369ff2..0x36ae41`.** It does NOT claim the merge has no
   acceptance/rejection anywhere — only that THIS finalization tail has only geometric clamping + a
   degenerate-rect skip. Upstream scoring (Lane A3) and other functions are out of scope.
5. **LLM-read disasm interpretation is not fact.** Only the three `strings` asserts and the grep-confirmed
   call-site/gate/LUT-loop VAs are deterministic; everything labeled "role"/"interpretation" is
   LEAD/CANDIDATE pending Codex re-extraction.
6. **No cross-citation as fact.** Does not rely on another Opus packet as fact; consistent with (does not
   strengthen) the ledger's PROVEN `CLM-MERGE-002`.
