# HYP-PREFUSION-002 — Per-Pixel Weighted-Average Normalizer (function `libcp+0x2f78e0`)

**Status:** `HYPOTHESIS` (unproven; uncitable as fact per `docs/hypotheses/README.md`)
**Relates to:** `CLM-PREFUSION-002` (the `src1`/`src2` pre-fusion merge/reduction mechanism — still `OPEN`/`BLOCKER`)
**Created:** 2026-05-30 · **Address-corrected:** 2026-05-30 (28mm decider, commit `e34e6d6`)

> **ADDRESS CORRECTION (machine-verified, committed in `e34e6d6`):** the original title VA `0x2f8040`
> was WRONG — it is a stack spill `movl %esi,-0x194(%rbp)`, not a normalizer. The real
> `Σ(w·v)/Σ(w)` reciprocal-normalize block is at **`0x2f8584–0x2f85a5`** inside function
> **`0x2f78e0`** (trip count `movl $0x5,%edx` at `0x2f8418`; division census of the function body =
> **0** hardware divides, **6** `rcpps`). Those three are now machine-verified FACTS (see
> `docs/evidence/bundle_proof_prefusion_reducer_arithmetic_static.md`). What stays a HYPOTHESIS is the
> kernel's **role** on the `src1`/`src2` path.

## Statement

Function `libcp+0x2f78e0` contains a per-output-pixel **weighted average** at `0x2f8584–0x2f85a5`:

```
out_pixel = Σ_i ( w_i · v_i )  /  Σ_i ( w_i )       over 5 unrolled contributor records
```

with the division done by reciprocal-multiply (`rcpps` at `0x2f859f` + `mulps` at `0x2f85a2`, no
hardware `div`), weights clamped to a floor and scaled by a shared per-output reciprocal `1/(pixel·gain)`.
Normalization is **`/Σw` (first power)** — not `/Σw²`, not `/N` (the literal `5` is the unroll trip
count). **The arithmetic shape is machine-verified.** The HYPOTHESIS is whether this kernel operates on
the `src1`/`src2` pre-fusion path (vs being a local spatial filter), which would resolve the
parity-critical normalization question for the merge.

## Provenance (and why the ROLE is only a hypothesis)

- Arithmetic shape + address: machine-verified by parent against an independent `otool` disasm
  (`e34e6d6`); reproduction `runs/prefusion_reducer_static/verify_28mm_decider_addresses.sh`.
  Originally surfaced (at the wrong address) by static workflow `wf_821d9755`.
- **Role unproven:** no call-graph / data-flow proof links `0x2f78e0` to the `src1`/`src2` path, and at
  28mm runtime the kernel was **not observed live** (BP-binding/async tooling gap — "not observed under
  tested conditions," not "never fires").

## Why It Is Not Yet Fact (the ROLE)

1. **No runtime observation that it is on the merge path.** The "5 contributors" could be 5 **cameras**
   (true inter-camera merge) or 5 **spatial neighbor taps** (a local filter). Static bytes cannot decide.
2. No call-graph / data-flow proof links `0x2f78e0` to `src1`/`src2`.
3. The sibling accumulator `0x369f80` (in function `0x3661b0`, single caller `0x365960`) IS on the IRAMP
   path and IS Hann-windowed (verified), but at 28mm only zero-valued first-touch tiles were captured —
   so even that kernel's N-camera-merge role is unresolved (see `bundle_proof_prefusion_reducer_arithmetic_static.md`).

## Proof Plan

> **Four-zoom rule (non-negotiable):** per the claim ledger, merge-critical closure requires explicit
> zoom coverage for **28mm, 35mm, 70mm, AND 150mm**. A result observed at one focal length is
> scope-bound to that focal length and CANNOT promote this hypothesis or move `CLM-PREFUSION-002`.
> Assume nothing about cross-zoom generality — observe it.

1. **Static re-extraction (deterministic, build-universal):** `otool -arch x86_64 -tV libcp.dylib`, slice
   function `0x2f78e0` around block `0x2f8584..0x2f85a5`, capture to a log under `runs/`. Confirm the
   `rcpps`/`mulps` normalizer shape and the
   `divss/divps` census = 0. Anchor-check `0x3eced0` first. (This part is zoom-independent — it is the
   binary's code, identical for every render — so a single clean static decode suffices for the
   *arithmetic shape*. It does NOT establish that this kernel is on the src1/src2 path at any zoom.)
2. **Runtime provenance — must be done at ALL FOUR zooms, sequentially (never concurrent instrumented
   renders; concurrency perturbs thread timing and surfaces the documented 150mm race):** for each of
   `28mm L16_02130`, `35mm L16_03041`, `70mm L16_03434`, `150mm L16_02285`, BP the normalizer (and the
   `0x369fa4` accumulator); on first hit read the `source` operand window + full backtrace +
   `image lookup` to determine whether `source` is multi-camera frame data or a single intermediate
   tile, and whether the enclosing chain reaches IRAMP `0x365960`/`0x3661b0`.
3. **Promotion gate:** this hypothesis may become fact ONLY when steps 1+2 agree across all four zooms.
   A partial result (e.g. 28mm-only) is recorded here as a scope-bound observation under "Progress",
   NOT as promotion, and explicitly names the zooms still unobserved.

## Progress

### 28mm runtime decider — 2026-05-30 (scope-bound to 28mm; promotes NOTHING) — committed `e34e6d6`

- **VERIFIED (zoom-independent binary facts):** address correction above — normalizer at
  `0x2f8584–0x2f85a5` in `0x2f78e0` (not `0x2f8040`); 0 hw divides / 6 `rcpps`; accumulator `0x369f80`
  in function `0x3661b0`, single caller `0x365960` (brief hint "accumulator in `0x365960`" REFUTED).
- **28mm runtime observations (scope-bound, NOT generalizable):** 16 accumulator hits at `0x369fa4`;
  coeff tile `rbp-0xa0` matched the periodic Hann-16 LUT on all 16; per-tile loop confirmed; backtrace
  `0x3661b0 ← 0x365960 ← 0x3ec770 ← 0x3ec960 ← 0x3d47d0 ← … ← pthread`.
- **INCONCLUSIVE:** all 16 tiles were zero-valued first-touch → N-camera-merge vs single-tile NOT
  resolved; no per-camera loop in the immediate caller; the `0x2f78e0` normalizer not observed live.
- **Still owed (four-zoom rule):** a redesigned probe that captures NON-ZERO accumulation and
  instruments the loop at frames `0x3ec770`/`0x3d47d0`, then runs at 28/35/70/150mm sequentially.
  28mm alone closes nothing.

### `0x2f53d0 -> 0x2f6420` callback-arm runtime — 2026-06-01 (scope-bound route exclusion)

- **VERIFIED under tested route:** after the first visible-`src1` `0x3e4b09` gate, complete accepted
  bridge HDR runs at `28mm`, `35mm`, `70mm`, and `150mm` select only the `0x2fb320` callback arm at
  `0x2f67e2 -> 0x5440` inside live helper `0x2f6420`; the `0x2f78e0` arm, worker entry, and normalize
  sites `0x2f8584`, `0x2f859f`, and `0x2f85a5` have zero hits under that route. See
  `docs/evidence/lldb_2f53d0_callback_arm_runtime_four_zoom.md`.
- **Consequence:** this hypothesis is not a valid explanation for the already-bounded visible-`src1`
  `0x3449f0 -> 0x345920 -> 0x2f53d0 -> 0x2f6420` runtime path unless a separate pre-gate or alternate
  caller route is proven.
- **Still not global disproof:** this does not prove `0x2f78e0` is dead globally; it only excludes this
  tested post-gate path as a positive runtime route to the normalizer.

## Disproof Criteria

- The "is it a `Σwv/Σw` normalizer" disproof is now **settled** — the arithmetic shape is machine-verified
  at `0x2f8584–0x2f85a5`. What remains falsifiable is the ROLE:
- If runtime shows the `source` operand is a single intermediate tile / spatial neighborhood rather than
  distinct per-camera buffers → the "inter-camera merge" reading is `REFUTED` (the arithmetic could still
  be a local filter; record that distinction).
- If a call-graph trace shows `0x2f78e0` is never reached from the `src1`/`src2` IRAMP path → `REFUTED`
  as the merge normalizer.

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
