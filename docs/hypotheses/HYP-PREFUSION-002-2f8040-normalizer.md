# HYP-PREFUSION-002 — Per-Pixel Weighted-Average Normalizer at `libcp+0x2f8040`

**Status:** `HYPOTHESIS` (unproven; uncitable as fact per `docs/hypotheses/README.md`)
**Relates to:** `CLM-PREFUSION-002` (the `src1`/`src2` pre-fusion merge/reduction mechanism — still `OPEN`/`BLOCKER`)
**Created:** 2026-05-30

## Statement

There may be a function at `libcp+0x2f8040` that computes a per-output-pixel **weighted average**:

```
out_pixel = Σ_i ( w_i · v_i )  /  Σ_i ( w_i )       over 5 unrolled contributor records
```

with the division done by reciprocal-multiply (`rcpps`+`mulps`, no hardware `div`), weights clamped to a
floor and scaled by a shared per-output reciprocal `1/(pixel·gain)`. If true, normalization is **`/Σw`
(first power)** — not `/Σw²`, not `/N` — which would resolve the parity-critical normalization question.

## Provenance (and why this is only a hypothesis)

- Produced by static multi-agent workflow `wf_821d9755` (raw: `runs/prefusion_reducer_static/workflow_wf_821d9755_result.json`).
- It is **LLM-read disassembly**: an agent reported verbatim-looking opcodes, but those bytes were **not
  machine-verified** against the binary by a deterministic tool. One agent in the run reported two
  premature/erroneous outputs under a "transient empty-Bash-output" condition.
- `0x2f8040` appears in **zero** existing repo evidence docs — there is no prior independent cross-check.

## Why It Is Not Yet Fact

1. The disassembly was never independently re-extracted and captured to a log.
2. **No runtime render was observed.** The "5 contributors" could be 5 **cameras** (true inter-camera
   merge) or 5 **spatial neighbor taps** (a local filter). Static bytes cannot decide.
3. No call-graph / data-flow proof links `0x2f8040` to the `src1`/`src2` path.

## Proof Plan

1. **Static re-extraction (deterministic):** `otool -arch x86_64 -tV libcp.dylib`, slice `0x2f8040`,
   capture to a log under `runs/`. Confirm the `rcpps`/`mulps` normalizer shape and the `divss/divps`
   census = 0. Anchor-check `0x3eced0` first.
2. **Runtime provenance (the decider):** BP at the normalizer (and at the `0x369fa4` accumulator); on
   first hit read the `source` operand memory window + a full backtrace + `image lookup` to determine
   whether `source` is multi-camera frame data or a single intermediate tile, and whether the enclosing
   chain reaches IRAMP `0x365960`/`0x3661b0`.

## Disproof Criteria

- If the re-disassembly shows `0x2f8040` is **not** a `Σwv/Σw` normalizer (e.g. it is integer/ROI prep,
  or contains a real hardware divide, or the "5" is not a contributor trip count) → `REFUTED`.
- If runtime shows the `source` operand is a single intermediate tile / spatial neighborhood rather than
  distinct per-camera buffers → the "inter-camera merge" reading is `REFUTED` (the arithmetic could still
  be a local filter; record that distinction).

## Sub-Hypotheses

- **HYP-2a (staging path):** the Hann LUT is staged `0x5fdb50 → -0xa0(%rbp)` by `libcp+0x3661b0`.
  Agent-reported, not machine-checked. (NOTE: the LUT *storage location* `0x5fdb50` itself is **already
  PROVEN** by byte-search — see `docs/evidence/bundle_proof_prefusion_reducer_arithmetic_static.md`. Only
  the staging disassembly remains a hypothesis.)

## Resolved Items (kept as do-not-repeat markers)

- **REFUTED meta-claim:** a workflow agent asserted the committed "proven chain" (`0x36cde0`, `0x36e530`)
  was "stale/broken." This was checked against the repo and is false — it was measured against a loose
  paraphrase in the workflow brief (a `contributor_record+0x48` weight and a `0x2f8f50` multiply-add),
  not against the repo. `docs/evidence/bundle_lldb_iramp_36cde0_scalar.md` already documents `0x36cde0`
  as patch-statistics/variance/covariance returning `sqrt(xmm0·xmm1)`, which matches. **No committed
  evidence doc is stale; the ledger was right.** No ledger action.
