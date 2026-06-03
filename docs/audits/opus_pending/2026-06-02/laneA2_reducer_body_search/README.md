# Lane A2 -- Reducer / Body Search (STATIC) -- Research Packet

**status: NEEDS_CODEX_VALIDATION**
**authority: NONE.** This packet is a reproducible research artifact produced in an isolated
quarantine worktree. It uses weak language (OBSERVED / LEAD / CANDIDATE) only and must be
independently validated by Codex before any canonical use.

- libcp.dylib sha256: `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- method: **STATIC ONLY** -- `otool -arch x86_64 -tV`, `nm -arch x86_64`, raw `__DATA` pointer/RTTI
  reads. NO render, NO runtime, NO breakpoints (concurrent agent may be rendering).
- anchorPassed: **TRUE** (0x3eced0 shows mulps@0x3ecfe4 -> maxps -> sqrtps).

## One-paragraph result
The known accumulator kernel **0x369f80** (`acc += source4 * (coeff_i*coeff_j)`, Hann-16) is
IMAGE-EFFECTING and is the body of a **per-tile SourceImageCache lambda** reached only through a
vtable (chain `0x3661b0 <- 0x365960 <- 0x3ec770 <- 0x3ec960`, vtable slot `0x65f610`, RTTI
`lt::SourceImageCache::...::$_0::operator()(Tile<vec4x16f>)::lambda(Image<vec4x32f>&, Rectangle<int>)`).
The normalizer **0x2f78e0** is IMAGE-EFFECTING but its RTTI identifies it as
`ImageDenoiseBilateralGeneric<5,true>` (a bilateral-denoise `std::function` body, vtable slot
`0x65a598`) -- i.e. its reciprocal-normalize block is a denoise weighted-average, role on src1/src2
still UNPROVEN. The State-helper-derived record family **0x23faf0** is a METADATA-ONLY record/clone
(POD header + one `vector<4-byte>` child index list). Across its **23** host functions there is **NO
DIRECT-CALL path** to any of the 6 named image kernels, and no image-reaching function calls
0x23faf0. **Hard caveat:** 3 of the 6 kernels are vtable/`std::function` indirect, which a static
call graph cannot cross, so the indirect link is bounded-out only for direct calls.

## For/against a single tidy reducer
**AGAINST**, within the searched surface. The image-kernel sub-graph is shallow (only 3 functions
reach a kernel by direct call) and is gated as **per-camera SourceImageCache source production** plus
**bilateral denoise** -- not a single N->1 combine. CANDIDATE reading: any pre-fusion merge is
**distributed and/or behind indirection (vtable/std::function/callbacks)**, not a lone reducer.
This is consistent with the briefing's warning not to assume an N->1 reducer exists.

## Files
- `observations.md` -- VERBATIM disasm/RTTI excerpts O0..O8 with log paths, scope-bound.
- `non_claims.md` -- 8 explicit non-claims.
- `proof_or_disproof_plan.md` -- P1..P5 + disproof conditions for Codex (incl. runtime backtrace test).
- `commands.txt` -- exact reproduction commands.
- `manifest.json` -- machine-readable summary.
- probe: `tools/lldb_probes/opus_pending/laneA2_reducer_body_search/callgraph_probe.py`
- logs: `runs/laneA2_reducer_body_search/{full_disasm.txt,nm_symbols.txt,callgraph_summary.log,probe_repro.log}`

## Reproduce
```
LIB="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
otool -arch x86_64 -tV "$LIB" > runs/laneA2_reducer_body_search/full_disasm.txt
python3 tools/lldb_probes/opus_pending/laneA2_reducer_body_search/callgraph_probe.py \
    runs/laneA2_reducer_body_search/full_disasm.txt "$LIB"
```
