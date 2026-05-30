# Evidence: Accumulator Weight Window Is A Periodic Hann-16 (Closed Form)

**Date:** 2026-05-30
**Status:** VERIFIED (single, narrow, machine-checked mathematical fact). Static-derived from
already-committed captured constants.
**Scope:** The 16 accumulator weights already documented in
[bundle_lldb_iramp_36e530_accumulator_prep.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_iramp_36e530_accumulator_prep.md).
**Does NOT touch any claim status.** `CLM-PREFUSION-002` remains `OPEN` / `BLOCKER`.

## What This Proves

The 16 scalar accumulator weights captured (identically across the four-zoom quartet) and recorded in
the committed evidence doc `bundle_lldb_iramp_36e530_accumulator_prep.md` — the weights the IRAMP body
applies as a 16×16 outer product `weight[row]·weight[col]` at `0x369fa1..0x369fa8` — are, to float32
precision, the **periodic (DFT-even) Hann window of length 16**:

```
w[n] = sin²(π·(n + 0.5) / 16) = 0.5·(1 − cos(2π·(n + 0.5)/16)),   n = 0..15
```

Therefore the accumulator's separable weighting is a **2-D periodic-Hann feather/resample window**
(the outer product of this 1-D window with itself).

Those 16 weights are stored verbatim in the binary as a read-only `float32[16]` constant at **file
offset `0x5fdb50`** of this `libcp.dylib` (machine-verified, see below).

## Verification (deterministic, reproducible — no LLM/agent judgment)

Method: take the 16 captured weights verbatim from the committed accumulator-prep doc and compare to the
closed form with a standalone python script.

| Candidate closed form | Max abs residual over 16 taps | Verdict |
|---|---|---|
| Periodic Hann `sin²(π(n+0.5)/16)` | **1.13e-7** (≈ 1 float32 ULP) | **MATCH** |
| Classic symmetric Hann `0.5(1−cos(2πn/(N−1)))` | 5.70e-2 | ruled out |

Corroborating signatures of the periodic form:
- Taps sum to **8.0 = N/2** (the periodic-Hann normalization signature).
- Non-zero endpoints (`0.00961`) and a peak of `0.99039` (not 0 / 1) — the half-sample-shift signature
  distinguishing periodic Hann from symmetric Hann.

Binary storage location (machine-verified, deterministic): a second standalone script packs the 16
captured weights as little-endian float32 and byte-searches the real `libcp.dylib`. Result: **exactly one**
64-byte match, at **file offset `0x5fdb50`**, decoding round-trip-exact to all 16 captured weights
(`decoded[0]=0.009607374668`, `decoded[7]=0.990392684937`). Binary size 6,935,696 bytes.

Reproduction scripts (committed under gitignored `runs/`, rerunnable against the real binary):
- `runs/prefusion_reducer_static/hann_window_closedform_check.py` — closed-form residual check.
- `runs/prefusion_reducer_static/verify_lut_in_binary.py` — byte-search of the dylib for the LUT.

## Scope Limits (what this does NOT claim)

- This identifies the **window's closed form only**. It does **not** identify the `src1`/`src2`
  pre-fusion merge/reduction mechanism and does **not** advance `CLM-PREFUSION-002`.
- It says nothing about which physical inputs feed the accumulator's `source` operand (camera frames vs
  intermediate tiles) — that is unproven and requires a runtime render.
- The weights themselves were captured by the pre-existing committed probe, not re-captured here; this
  note adds only the verified closed-form identity for those already-admitted values.

## Unverified Leads (NOT fact — explicitly excluded from this proof)

A static multi-agent disassembly pass produced a **candidate** finding: a possible per-pixel
`Σ(w·v)/Σ(w)` normalizer. UPDATE 2026-05-30: parent machine-verified the disassembly — the original
`0x2f8040` address was WRONG (it is a stack spill `movl %esi,-0x194(%rbp)`); the real reciprocal-
normalize block is `0x2f8584–0x2f85a5` in function `0x2f78e0` (trip count 5; 0 hardware divides, 6
`rcpps`). Those are now machine-verified bytes. What remains a HYPOTHESIS is the kernel's ROLE — whether
it operates on the `src1`/`src2` path (no call-graph link proven; not observed live at 28mm).

It is tracked — not lost — as a first-class sister hypothesis, with its proof/disproof plan, in
[docs/hypotheses/HYP-PREFUSION-002-2f8040-normalizer.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/hypotheses/HYP-PREFUSION-002-2f8040-normalizer.md).
Per `docs/hypotheses/README.md`, that hypothesis **may not be cited as fact** by this or any other doc
until it is independently re-disassembled (captured to a log) or runtime-confirmed.

(The LUT storage location `0x5fdb50`, originally also an agent claim, has since been independently
machine-verified by byte-search and is therefore stated as fact above — not left as a hypothesis.)
