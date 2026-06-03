# Lane A verdict — src1/src2 reducer mechanism (predict-then-verify result)

**Status:** mixed. Claims I personally re-extracted from the binary = **OBSERVED**; claims that rest only on
the subagent (which made a verified error, see below) = **LEAD / down-weighted**. All `NEEDS_CODEX_VALIDATION`.
Binary: `libcp.dylib` (file-offset==VA). Method: `arch -x86_64 lldb ... disassemble` (static).

## Prediction tested
- **H1:** src1 = value accumulator, src2 = Σweight accumulator, output = src1·reciprocal(src2) per-pixel.
- **H2:** src1 = output frame, src2 = a second source layer read as pixel data.

## Verdict: H1's *mechanism* REFUTED; its *spirit* (normalize by Σweight) CONFIRMED via a scalar reciprocal.

### OBSERVED (re-extracted by me, not the subagent)
1. **src2 is geometry-only.** `0x366915 movq 0x10(%r15),%rsi` (src2) → `0x36695a callq 0x374ac0`. Inside
   `0x374ac0`, the src2 pointer (r14) is read **only** at `0x374b0a movl 0x30(%r14)` / `0x374b0e movl
   0x34(%r14)` = width/height, and intersected (`cmovlel`) with the caller rect (rbx: `0x0/0x4/0x8/0xc`).
   ⇒ src2 supplies an **ROI/clip box from its dims**, not pixel data and not a weight buffer. **H1's
   "src2 = Σweight buffer" is refuted.**
2. **A scalar reciprocal normalization EXISTS** (this is the key correction):
   ```
   0x36a934  shufps $0x0,%xmm2,%xmm2     ; broadcast the accumulated scalar (Σ score)
   0x36a938  rcpss  %xmm2,%xmm2          ; reciprocal = 1/Σscore   <-- VERIFIED, <+18308> in 0x3661b0
   0x36a93c  movaps %xmm2,-0x42f0(%rbp)
   0x36a946  shufps $0x0,%xmm0,%xmm0     ; broadcast low lane
   0x36a974  callq  0x19e7d0             ; SIMD scale helper: each vec4 *= reciprocal
   ```
   then the separable weighted add:
   ```
   0x36aa30  movaps (%r10,%rdi),%xmm0    ; reciprocal-scaled contributor vec4
   0x36aa47  mulss  (%rax,%rcx,4),%xmm1  ; separable weight-table entry
   0x36aa50  mulps  %xmm0,%xmm1          ; weight * vec4
   0x36aa53  addps  (%rsi,%rdi),%xmm1    ; accumulate into destination
   0x36aa57  movaps %xmm1,(%rsi,%rdi)    ; store
   ```
   ⇒ the merge is a **normalized score-weighted average**: per-contributor scores are summed to a SCALAR,
   reciprocated (`1/Σscore`), each contributor vec4 scaled by it, blended (`reciprocal*0.2` into lane 3 —
   per Codex `bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`), then separable-weighted and
   accumulated. This is **soft, normalized, not hard-select and not un-normalized sum** — consistent with
   the prior A3 converged answer and Codex's committed four-zoom evidence at this same site.

### Caught subagent error (verify-before-trust)
The investigator reported "Grep for divps/divss/rcpps/rcpss across the 0x3661b0 tail (0x36a08f-0x36ae30):
ZERO hits." **False** — `rcpss` is at `0x36a938`, inside that exact range. Confirmed by (a) my own
disasm above and (b) Codex's committed doc. Lesson: a subagent's exhaustive-grep negative is not a fact
until re-extracted; its other §-claims here are treated as LEAD unless independently checked.

### LEAD (subagent-only, plausible, not personally re-extracted)
- src1 = coordinate anchor frame: warp coords validated/clamped against src1 dims (`0x366c77`, `0x36a004`);
  src1's pixel buffer reportedly never written. (Plausible and consistent with §1, but from the agent.)
- The pixel accumulator is a freshly-allocated buffer (not src1, not src2), handed to resamplers
  `0x2b2be0`/`0x36f800`; contributor pixels come from the source-image vector at descriptor `+0x20`
  (cache+0x258). (Consistent with the arg map, but the per-source buffer linkage is static-structural.)

## Net reconciled answer (to the #1 blocker's reduction-math sub-question)
Within `0x3661b0`: **src1/src2 are geometry descriptors** (src1 = warp/clamp anchor frame; src2 = secondary
ROI/clip box with a narrower resample radius), **NOT** the merged image buffers. The actual N→1 reduction
over the contributor source vector is a **per-contributor score-normalized weighted average**
(`1/Σscore` scalar reciprocal → broadcast scale → lane-3 `*0.2` blend → separable-weighted accumulate).
Still OPEN: contributor selection / coverage-sentinel gating, src2 box's runtime gating effect, lane-3
semantics, and runtime confirmation across the four-zoom + two-unit corpus.
