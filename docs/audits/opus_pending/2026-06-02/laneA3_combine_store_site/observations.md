# Lane A3 — Observations (OBSERVED-from-disasm)

Source dumps (machine-extracted, reproducible — see `commands.txt`):
- `runs/laneA3_combine_store_site/func_365960_outer.txt` (419 insns, `0x365960`)
- `runs/laneA3_combine_store_site/func_3661b0_accumulator.txt` (3512 insns, `0x3661b0`, contains `0x369f80`)

All VAs are installed-`libcp.dylib` module offsets (VA == file offset). LLM-read; not yet Codex-re-extracted.

## O1 — The contributor iteration is ONE outer loop inside `0x3661b0`

`0x365960` calls `0x3661b0` exactly once (`0x365f4b callq 0x3661b0`). The 5-fold iteration is inside
`0x3661b0`:

- Loop top: `0x366b00`.
- Induction register: `rbx` (`0x366af2 xorl %ebx,%ebx`; `0x368b95 incq %rbx`).
- Loop-back: `0x368bb5 jb 0x366b00`.
- Trip count (re-derived each pass), the contributor vector:
  ```
  0x368b98  movq -0x4388(%rbp), %r15      ; r15 = this
  0x368b9f  movq 0x18(%r15), %rax         ; vector at this+0x18
  0x368ba3  movq 0x8(%rax), %rcx
  0x368ba7  subq (%rax), %rcx
  0x368baa  sarq $0x4, %rcx               ; (end-begin)/16 = element count (16-byte stride)
  0x368bae  cmpq %rcx, %rbx
  ```
- Per contributor, a `0x50`-stride warp record is indexed (`leaq (%rbx,%rbx,4); shlq $0x4` = ×0x50),
  matching the established 5-element / `0x50`-stride warp vector.

16-byte contributor stride + `0x50` warp stride are consistent with the entry-proven vectors.

## O2 — The accumulate store is a read-modify-write into a shared buffer

Accumulate (inside the tile loops, `0x369f80` region):
```
0x369f4c  movl  -0x4390(%rbp), %edx
0x369f52  addl  -0x4398(%rbp), %edx       ; warp-mapped tile row
0x369f58  imull %r8d, %edx                ; * view stride
0x369f5c  addl  %ecx, %edx                ; + col
0x369f5e  movslq %edx, %rdx
0x369f61  shlq  $0x4, %rdx                ; *16 (vec4 float)
0x369f65  addq  -0x1710(%rbp), %rdx       ; dest = PERSISTENT base + warp-mapped pixel offset
...
0x369f80  movss -0xa0(%rbp,%rsi,4), %xmm0 ; row Hann weight
0x369f90  movss -0xa0(%rbp,%rcx), %xmm1   ; col Hann weight
0x369f99  mulss %xmm0, %xmm1              ; separable weight
0x369fa1  mulps (%rdi), %xmm1             ; source vec4 * weight  (rdi = source pixel)
0x369fa4  addps (%rdx,%rcx,4), %xmm1      ; += EXISTING dest contents   (READ-MODIFY)
0x369fa8  movaps %xmm1, (%rdx,%rcx,4)     ; store back to SAME dest      (WRITE)
```

## O3 — The dest base `-0x1710(%rbp)` is loop-invariant across contributors

Every access to `-0x1710(%rbp)` in `0x3661b0`:
```
0x366356  movaps %xmm0, -0x1710(%rbp)   ; zero-init (prologue)
0x36640c  addq   %rsi,  -0x1710(%rbp)   ; ONE crop-offset adjust, PRE-LOOP
0x369f65  addq   -0x1710(%rbp), %rdx    ; READ as dest base, inside store loop
```
No store to `-0x1710` exists between the loop top `0x366b00` and the accumulate `0x369f65`. The base
is established once (cropped view from `0x8(%r15)` via crop helper `0x374ac0` at `0x3665d5`), not a
per-contributor `__Znam`/`__Znwm`. The only `__Znwm` (`0x366a8b`) allocates the warp working array and
runs PRE-loop. Therefore each contributor's accumulate targets the same buffer; only the warp-mapped
pixel offset (`-0x4390/-0x4398`) varies per contributor.

## O4 — Write hierarchy

contributor(`rbx`) → tile(`r13`,`r12`) → 16×16 separable Hann accumulate(`rsi` 0..0x10, `rcx` 0..0x40)
→ RMW into shared `-0x1710` buffer.

## Interpretation (LEAD / CANDIDATE, not proof)

H-MOSAIC would require either a per-contributor fresh dest pointer or a plain `movaps` write with no
prior-contents `addps`. Neither is present. The `addps`-then-store-back RMW into a contributor-invariant
base favors **H-REDUCE**. Confidence: LEAD/CANDIDATE — disasm-read structure, not a verified runtime
N→1 reduction. The deciding runtime question is in `proof_or_disproof_plan.md`.
