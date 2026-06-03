<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## 0xe6ba0 — verdict: keyed SELECT-ONE lookup, NOT the N->1 merge/reducer

**PREDICTION (refuted):** I predicted an 8-point DLT/homography solve (the >=8 guard at 0x2170d1 looked like the 8-point algorithm). Disasm refutes this: no solve, no blend, no float arithmetic at all in the body.

### (1) What it is
A 40-instruction linear `std::vector` search returning ONE matched record:
- `0xe6bb7 movq 0x10(%rsi),%rbx` / `0xe6bbb movq 0x18(%rsi),%r13` — vector begin/end ptrs.
- `0xe6bbf cmpq %r13,%rbx ; je 0xe6bf3` — empty check.
- Loop `0xe6bd0`: `callq 0xf3320` (returns elem `+0x64`) `cmpl %r12d(edx)` ; if eq `callq 0xf2720` (returns elem `+0x60`) `cmpl %r15d(ecx)` ; if both eq -> match `0xe6c0c`.
- `0xe6bea addq $0x10,%rbx` — 16-byte stride = `{ptr, shared_ptr ctrl}`.

### (2) Inputs / output
- `rdi` = 16-byte out-buffer (returned in rax).
- `rsi` = object holding the vector at `+0x10/+0x18`.
- `edx` = key A (matched against elem field `+0x64` via 0xf3320).
- `ecx` = key B (matched against elem field `+0x60` via 0xf2720).
- Output: match -> copies `(elem)` and `0x8(elem)` into out-buf and `__add_shared()` retains the ctrl block (`0xe6c0c..0xe6c24`). No match -> `xorps`+`movups` zero-fill (`0xe6bf3`).

### (3) Arithmetic?
NONE. The only xmm instruction is the `xorps %xmm0,%xmm0` zeroing idiom at `0xe6bf3`. No mulps/addps/divps/subps/mulss/addss/divss in `0xe6ba0..0xe6c0b`. It neither blends nor dispatches to a blender; it just returns the selected record (then unpacked downstream via 0xf3360 -> 0x1f0a00).

### Merge-rule bearing
Fails BOTH gates for an "X is the merge/reducer" verdict: signature does not accept N>1 frames to combine, and body has no accumulator store reducing N->1 — it picks a single keyed contributor. The internal `0xf2720` (`+0x60` accessor) is the same field route tracked in Lane C/C6 tele work. The real N->1 accumulate is NOT here; look upstream/downstream of the call site at 0x21710c (the >=8-pair guard counts coordinate pairs, but 0xe6ba0 only fetches one record per call).