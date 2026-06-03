# Lane A3 Step 0 — inner combine body `0x369320..0x369ec4`

**Status:** `NEEDS_CODEX_VALIDATION`. Machine-verified facts + one OPEN hinge. Two separate automated
disasm traces produced conflicting/erroneous verdicts on the loop re-entry point (see "Why runtime"
below); treat the sum-vs-select verdict as UNRESOLVED until a runtime watchpoint settles it.

## Machine-verified (deterministic opcode / branch checks)

### MV1 — per-contributor SAD block-match motion search (NEW finding)
The inner body runs integer SAD block matching with an explicit argmin:
```
0x3694b1 mpsadbw $0x0,%xmm7,%xmm6   0x3694bb mpsadbw $0x5,...   0x3694ca mpsadbw $0x2,...   0x3694d4 mpsadbw $0x7,...
0x3694f3 mpsadbw $0x0,%xmm8,%xmm1   ... (8 mpsadbw)             0x369543 phminposuw %xmm3,%xmm0   (argmin)
0x3695a1 mpsadbw ... (second 8-block)                          0x369643 phminposuw %xmm3,%xmm0
```
`mpsadbw`+`phminposuw` = sum-of-absolute-differences block match + horizontal-min index = a motion /
displacement search. So each contributor is **aligned to a reference by block matching** before it is
combined. (Deterministic: opcodes are byte-level, not interpretation.) This is a substantive mechanism
detail for `CLM-PREFUSION-002` — the merge is motion-compensated per contributor.

### MV2 — single post-loop accumulate, fed by per-contributor scratch (branch-verified)
```
0x369f24 jb 0x3692f0          ; contributor loop back-edge
0x369f2a (fall-through, AFTER the contributor loop)
0x369f2d leaq -0x4240(%rbp),%rdi
0x369f34 callq 0x36e530       ; consumes -0x4240 scratch, returns source in rax
0x369f65 addq -0x1710(%rbp),%rdx ; dest = shared output base + tile offset
0x369f80..0x369fca            ; Hann 16x16 separable overlap-add (addps/movaps into (%rdx,%rcx,4))
0x369fd9 jl 0x369160 ; 0x369fec jl 0x369140 ; tile loops
```
The Hann accumulate runs **once per tile**, after all contributors. Its source is `-0x4240`. Inside the
body, `-0x4240`/`-0x11a0` are the per-contributor scratch (`0x369e31 leaq -0x4240,%rdi`,
`0x369e38 leaq -0x11a0,%rsi`).

### MV3 — coverage sentinel reuse (branch-verified)
`0x369ed0 movabsq $0x8000000080000000` writes the same packed sentinel the producer uses at `0x366da0`,
into a contributor-indexed map `(%r12,%rcx,8)` (rcx = `-0x4370` = contributor index). It is a
coverage-reject marker, reached only via the bounds `jle/jge 0x369ed0` rejections — NOT a result write.

## The OPEN hinge (sum vs select)

H-REDUCE requires that `-0x4240` (or `-0x11a0`) be **accumulated** across the contributor loop
(load→add→store-back to the same scratch each valid contributor), so the single post-loop accumulate
sees the SUM. H-SELECT results if `-0x4240` is **overwritten** each contributor (post-loop accumulate
sees only the LAST valid contributor). The extracted range does not contain a decisive
load-add-store-to-same-scratch pattern across contributors, and `0x36e530`'s body (the scratch
consumer/finalizer) was not extracted. **UNRESOLVED statically.**

## Why runtime is the arbiter (not more static reading)

Two independent automated disasm passes both mis-attributed the loop that re-enters the `0x369f80`
accumulate (one placed it inside `0x366b00..0x368bb5`; one claimed per-contributor re-entry of
`0x369f80`). Branch-target machine-checks refuted both. Given that track record, the sum-vs-select
hinge should be resolved by a **runtime watchpoint**, not a third interpretation.

## Runtime experiment (the decisive one)

On a tile where ≥2 contributors pass the `0x36930f` coverage gate:
1. Break at `0x369f2d` (start of post-loop accumulate setup). Read the 16x16 `-0x4240` scratch contents
   once. Separately, break at the per-contributor scratch finalize inside the body and snapshot
   `-0x4240`/`-0x11a0` after each valid contributor.
2. If the scratch grows monotonically (sum) across ≥2 contributors ⇒ **H-REDUCE**. If it is replaced
   each contributor (only last survives) ⇒ **H-SELECT**.
   Equivalent: hardware-watchpoint one 16-byte slot of `-0x4240` and count load-add vs plain-store.
3. Four-zoom, sequential renders, Codex offline only. Report scope-bound.

Cheaper static pre-step if a render is unavailable: extract `0x36e530` body and the `0x369e00..0x369ec4`
scratch-store pattern to check for load-add-store into `-0x4240` across contributors.
