<!-- provenance: workflow wf_d596de8b-90c (l16-unfenced-w10), 2026-06-03; finder + verifier; reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm).
**Verifier reliability:** core static findings PASS; one item flagged is a runtime-LEAD the verifier correctly could not re-extract statically (not a real failure)

## C6 static: key-15 -> group-type-2 survival, alternate readers, terminal filter

### Q1 - Does key-15 -> group-type-2 survive the +0x30 clear and affect a decision?
**OBSERVED.** The classifier `0xf6c60` is a pure key->group-type map (no +0x30 read):
- `0xf6c6e movl $0xfc00,%eax; 0xf6c73 btl %esi,%eax; 0xf6c76 jb 0xf6c8a -> movl $0x2,(%rdi)`  => key bit in {10..15} -> type 2. **key 15 -> type 2.**
- else mask `0x1f` -> type 0 (bits0-4) or type 1; `esi>15` -> abort `"unknown camera group type!"`.

The group-type result IS consumed, and even **guards the +0x30 clear**:
```
0x3c9087 callq 0xf6c60            ; classify -> -0x118(%rbp)
0x3c908c cmpl  $0x2,-0x118(%rbp)  ; group-type == 2 ?
0x3c9093 je    0x3c90a9           ; type-2 => SKIP clear
0x3c9095 callq 0xf2720            ; else read item +0x60
0x3c909d cmpl  $0xf,%eax          ; key == 15 ?
0x3c90a5 movb  $0x0,0x30(%rax)    ; clear +0x30
```
**Critical refinement:** the object classified at `0x3c9087` is NOT the item. `0xe6cf0` = `*(int*)(rdi+0x44)` on `%r15` (the vector head at ctx+0xa0 = container/profile). The item key compared to 15 comes from `0xf2720` = `*(int*)(rbx+0x60)`. So there are **two distinct "keys"**: a container group-type (+0x44) and a per-item module key (+0x60). The committed runtime fact that the clear fired on the key-15 item is consistent only when the CONTAINER group-type != 2 at that moment. The `cmpl $0x2` semantics of the clear-guard were not documented in committed evidence; this is the new detail.

### Q2 - Alternate +0x60==15 reader outside 0xf2720?
**OBSERVED (negative, full __text range 0x2250..0x555d20).** `0xf2720` is exactly `return *(int*)(rdi+0x60)`. Of all **58** `0xf2720` callsites, exactly **one** compares the result to 15: `0x3c9098` (already committed). Direct `mov [reg+0x60]; cmp ...,0xf` disp8 pattern: **0 hits**. No alternate +0x60==15 reader exists. The +0x60 value 15 is otherwise consumed only via `0xf6c60` (bucketed to type-2), never re-compared to 15.

### Q3 - Terminal filter excluding group-type-2 / C6?
**OBSERVED: none.** In contributor-decision loop `0x3b1d20`:
```
0x3b2143 callq 0xf2720    ; item +0x60 key
0x3b214d callq 0xf6c60    ; -> -0x108(%rbp)
type 0 -> je (no flag)
0x3b2170 type 2 -> movb $0x1,%r15b
0x3b216a type 1 -> movb $0x1,%r13b
```
Container reclassified at `0x3b219d`; flags merged by container-type at `0x3b21a2-0x3b21c9`; result stored via `0x40b000` (int@rdi + bool@rdi+4) and `0x4b0(%r15)=5-<0x40b0e0>`. `"Unexpected group type!"` aborts (`0x3b434b`,`0x3b46a1`) only for types outside {0,1,2}. **type-2 is a first-class valid contributor type that sets a flag; it is never discarded.**

### Net
key-15 -> group-type-2 is a real, surviving classification (the +0x60 key drives it through `0xf6c60`), consumed in contributor flags and as a clear-guard. The +0x30 active-byte clear is a SEPARATE per-item mechanism guarded by the CONTAINER group-type, not by the item key's type-2 membership. No code excludes type-2 from the contributor set.

## Verifier note(s)
- **0x3c9087 (runtime LEAD)**: Static only (LEAD cannot pass without runtime): static confirms e6cf0(r15) reads r15+0x44 at 0x3c907d; result fed to f6c60 at 0x3c9087; classifier output stored to [r12] which equals &[rbp-0x118] (confirmed by cmp [rbp-0x118],2 at 0x3c908c); if container type==2 then je 0x3c90a9 skips the key-15 clear. Two distinct objects confirmed: r15=container, [rbx]=item. Actual container +0x44 value during tele runs requires LLDB stop at 0x3c9087 or 0x3c9082 to read rdi/rdi+0x44. Not resolvable from binary bytes alone.
