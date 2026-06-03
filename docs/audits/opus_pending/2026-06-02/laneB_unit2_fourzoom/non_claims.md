# non_claims — Lane B Unit-2 four-zoom

status: NEEDS_CODEX_VALIDATION. This packet has NO authority.

## What this is NOT

1. **NOT a universality claim.** The static libcp.dylib is byte-identical
   across units (one binary, sha256 b38dc4b3...), so the Hann-16 LUT bytes are
   *shared* by construction — there is nothing per-unit about the table in the
   binary. What is tested here is narrower: whether the RUNTIME accumulator at
   `0x369fa4` actually USES that same tile when fed each Unit-2 LRI, per zoom.
   A per-zoom runtime match does not generalize to "all captures / all units /
   all conditions."

2. **NOT a reducer claim.** This packet does NOT establish that `0x369fa4` is
   "the merge" or "the reducer." Per the two-condition rule, a merge/reducer
   verdict requires BOTH (a) a signature that accepts N>1 camera frames AND
   (b) a body that reduces N->1 with identified accumulator stores. This packet
   captured ONLY the 16 coefficient floats at the FIRST hit; it did NOT trace
   the accumulation loop, count source frames, or identify N->1 store
   instructions. No reducer/merge conclusion is offered.

3. **NOT an image-effect claim.** No statement about output pixels, MAD,
   coverage, or visual result. Render output was sent to /tmp scratch and not
   examined.

4. **NOT a "first hit == only behavior" claim.** Only the FIRST `0x369fa4` hit
   per render was captured. The accumulator fires many times; later hits, other
   tiles, or per-pyramid-level variation were NOT examined.

5. **NOT an anchor confirmation.** anchorPassed = FALSE on this binary: the
   spawn-prompt anchor offset `base+0x3eced0` disassembles to a function
   prologue here, not `mulps->maxps->sqrtps`. The anchor expectation is
   unmet/stale; this is reported, not worked around. The `0x369fa4` probe
   target is independent and did resolve+fire cleanly.

6. **NOT cross-unit averaging.** Unit-1 reference and Unit-2 captures are kept
   strictly separate. No value was merged or averaged across units.

7. **150mm is NOT "never crashes."** It did not SIGABRT in THIS first-hit
   capture (we stop and quit at the first hit, before later stages). Scope-bound
   to this single capture only.

## What IS observed (weak)

- On Unit-2, at the FIRST `0x369fa4` hit, the 16 stack floats at `$rbp-0xa0`
  were float32-identical across all four zooms and identical to the Unit-1
  Hann-16 reference (6 dp, maxdiff 0.0). CANDIDATE / LEAD only.
