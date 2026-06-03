# Lane A6 addendum — stage-2 (CDF 9/7 wavelet term) + final combination

**Status:** `NEEDS_CODEX_VALIDATION`. Completes the score closed-form to: stage-1 **assembled**
(`closed_form_stage1.md`), stage-2 **identified + combination confirmed** (this doc), full q2 formula
**bounded but not assembled** (deferred — see below). Constants/instructions OBSERVED (deterministic).
Binary `libcp.dylib` sha256 `b38dc4b3…`.

## Stage-2 helpers are CDF 9/7 wavelet lifting (byte-anchored)

After stage-1 stores `q1` to `-0x80(%rbp)`, the body calls two helpers on the reference patch (`r14`):
```
0x36cf28 movq %r14,%rdi ; 0x36cf2b callq 0x371730
0x36cf30 movq %r14,%rdi ; 0x36cf33 callq 0x371a90
```
`0x371730` is a dense SIMD routine (188 SIMD ops in 201 instrs) with a lifting predict/update structure
(`subps`/`addps` around `mulps` by coefficient registers). It loads the CDF 9/7 coefficient
`0x5cbfe0 = 3.1722686` (= 2·α) at `0x37174b` — **byte-confirmed** use of the CDF 9/7 lifting constants
(matching A6's coefficient cluster `0x5cbfd0..0x5cc040`). So `0x371730`/`0x371a90` apply the **CDF 9/7
biorthogonal wavelet transform** to the patch (a multi-band/lifting decomposition), then later code derives
a wavelet-domain scalar `q2` (a sharpness/energy/structural statistic of the transformed patch).

## Final combination (OBSERVED)

```
0x36e511 mulss %xmm1, %xmm0     ; q1 * q2
0x36e515 sqrtss %xmm0, %xmm0    ; score = sqrt(q1 * q2)
0x36e528 retq
```
The returned per-contributor score is the **geometric mean** of the stage-1 SSIM contrast-structure term
`q1` and the stage-2 wavelet-domain term `q2`.

## Score closed-form status (summary)

```
score = sqrt( q1 * q2 )
q1 = clamp( (mu_A[3]*(2*sigma_AB+0.03)/(sigma2_A+sigma2_B+0.03) - 0.8)/0.19, 0, 1 )   [ASSEMBLED]
q2 = wavelet-domain statistic of the CDF 9/7 transform of the patch                    [IDENTIFIED, not assembled]
```

## Non-claims / deferred
- **q2 is not assembled.** The exact wavelet-domain statistic (which subbands, what energy/sharpness
  reduction) requires assembling the 188-op `0x371730` + `0x371a90` bodies and the post-helper reduction;
  deferred deliberately to avoid an error-prone over-claim. What IS established: it is a CDF 9/7
  wavelet-domain scalar (coefficient use byte-confirmed).
- The geometric-mean combination `sqrt(q1·q2)` is OBSERVED; the public name (e.g. a composite
  structural+sharpness quality) is not proven.
- Clean-room note: both q1 (SSIM) and q2 (CDF 9/7 wavelet) are **published algorithms** — the full metric
  is reimplementable from formula once q2 is assembled; no libcp bytes needed.
- LLM-read disasm; constants byte-verified. `NEEDS_CODEX_VALIDATION`.
