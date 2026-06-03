# Lane A3 — Non-claims (what this packet does NOT establish)

1. **Not proven that overlap actually occurs at runtime.** The `addps`-RMW proves the *capability* to
   sum overlapping contributions. It does NOT prove the per-contributor warp offsets ever collide on
   the same output element. If every contributor's warp maps to a strictly disjoint tile, behavior is
   effectively mosaic despite the RMW structure. This is the single ambiguity the runtime plan resolves.

2. **Not a verified reducer closure for `CLM-PREFUSION-002`.** This packet locates a *candidate*
   physical convergence point (the `0x369fa4/0x369fa8` accumulate into the `-0x1710` buffer). It does
   not establish the full merge mechanism boundary, the acceptance/rejection logic, or the semantic
   src1/src2 payload contents — all of which the ledger lists as still open.

3. **Contributor count not pinned to 5 here.** The static code uses a dynamic `(end-begin)/16` count.
   It is consistent with the entry-proven 5, but this packet did not re-confirm 5 at runtime.

4. **`this->0x8` not confirmed as the externally-visible output.** The dest base derives from
   `0x8(%r15)` via crop helper `0x374ac0`. Whether that object is the buffer the bridge later reads
   back as the merged output (vs an internal scratch later copied out) is NOT traced here. Helper
   bodies `0x374ac0`, `0x36fba0`, `0x36e530` were not read.

5. **Entry→`this` marshalling not verified at runtime.** The mapping from the entry's `rcx`/`r8`
   vectors into `this->0x18`/`this->0x20` is inferred from stride, not runtime-confirmed.

6. **LLM-read disasm.** Every VA/instruction is read from `otool` output by an LLM, not independently
   re-extracted. Per project rule this is not fact until Codex re-extracts.

7. **No cross-citation.** This packet does not rely on any other Opus quarantine packet as fact.
