# Lane A3 — CORRECTION (self-caught structural error)

**Status:** supersedes the loop-structure narrative in the first commit of this packet (`ecfc8ab`).
The corrected structure below is machine-verified (branch-target ordering); the earlier read was not.

## What was wrong

The first commit claimed: *"one outer contributor loop (top `0x366b00`, back `0x368bb5`) whose body
contains the accumulate; each contributor read-modify-writes the shared `-0x1710` buffer via
`addps/movaps` at `0x369fa4/0x369fa8`."*

That is **incorrect**. Machine-verifying branch targets shows the accumulate `0x369f80` lives at a
**higher address than `0x368bb5`**, so the `0x366b00..0x368bb5` loop does **not** enclose the accumulate.
`0x366b00..0x368bb5` is a *pre-pass* (it builds the per-contributor warp-record array, element stride
`0x280`, via the pre-loop `__Znwm`). The accumulate is reached afterward in a different loop nest.

## How it was caught

Machine grep of backward branches and their targets (`commands.txt` step 4 + the branch-target
ordering check), not LLM re-reading. The `addps`/`movaps`/`-0x1710` instruction facts themselves were
correct; the *loop containment* inference around them was not. This is exactly the failure mode the
project's "LLM-read disasm is not fact" rule guards against.

## Corrected structure (machine-verified branch targets)

```
tile-X loop      0x369140 .............................. 0x369fec  jl 0x369140
  tile-Y loop    0x369160 ............................ 0x369fd9  jl 0x369160
    contributor loop  0x3692f0 ........ 0x369f24  jb 0x3692f0   (counter -0x4358)
        0x3692f0  leaq (%rcx,%rcx,4); shlq $0x7   -> warp record index, stride 0x280
        0x3692f8  movl 0x28(%rdi,%rdx),%eax        -> warp field
        0x369306  movq 0x30(%rdi,%rdx),%r12        -> per-contributor coordinate map ptr
        0x36930b  movl (%r12,%rsi,8),%eax
        0x36930f  cmpl $0x80000000,%eax            -> SENTINEL coverage gate
        0x369314  jne  0x369320                    -> valid: process this contributor
        0x36931b  jmp  0x369f0b                    -> invalid: skip to next contributor
        (valid body 0x369320 .. 0x369ec4) then 0x369ec4 jmp 0x369f0b -> next contributor
    (after contributor loop exits 0x369f24)
    0x369f2a..0x369f7f  setup; 0x369f34 callq 0x36e530 (source prep); dest = -0x1710 base + offset
    Hann accumulate 0x369f80..0x369fca:
        0x369fa1 mulps (%rdi),%xmm1 ; 0x369fa4 addps (%rdx,%rcx,4) ; 0x369fa8 movaps back
```

### Corrected interpretation

- The **cross-camera combination across contributors happens INSIDE the contributor loop body**
  (`0x369320..0x369ec4`), once per output tile, with a **per-(contributor,position) coverage gate**
  on sentinel `0x80000000` (contributors that don't cover the tile are skipped). This sentinel gate is
  a tile-level **acceptance** mechanism — relevant to the ledger's open "acceptance/rejection" item.
- The `addps`/`movaps` RMW at `0x369fa4/0x369fa8` is **cross-tile Hann overlap-add** of the combined
  per-tile result into the shared output, **not** cross-camera summation. (The shared, loop-invariant
  `-0x1710` base — 3 accesses only — remains machine-verified and is consistent with overlap-add.)

### Still OPEN (was wrongly treated as favored)

Whether the inner body `0x369320..0x369ec4` **SUMS** valid contributors (true reduction) or **SELECTS**
one (e.g. last/best valid) is **UNVERIFIED** — that body was not traced. The reduction-vs-selection
question is real and now localized to `0x369320..0x369ec4`. See updated `proof_or_disproof_plan.md`.
