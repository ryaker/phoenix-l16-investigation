<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** one claim failed re-extraction (a detail; core stands) — see correction at end; treat that item as LEAD

## THREAD: Consumer of 0x218b30 stats (mean score xmm0 + fraction *(%r14)) — is it the merge gate?

### PREDICTION (stated first, then tested)
Predicted: xmm0 is thresholded (ucomiss vs constant) and branched to accept/reject; gate in caller.
**REFUTED** at the only call site — both outputs are stored into arrays, not branched on.

### VERDICT
**This caller is an array-FILLER, not the accept/reject gate.** The two statistics are written into two index-aligned per-iteration float arrays; no threshold/branch exists at the call site.

### Call-site facts (re-extractable, libcp.dylib)
- Single direct call site: `0x218f7c  callq 0x218b30` (E8-rel32 scan of __text @ file off 8784/addr 0x2250 size 0x553ad0 -> exactly 1 hit). It sits inside function `0x218e20`.
- Arg mapping at site:
  - `0x218f76 movq %r13,%rdi`  arg1 = *(rbx+0x20) object
  - `0x218f79 movq %r14,%rsi`  arg2 = -0xd0(%rbp) local (built by 0x23faf0)
  - `0x218f63 movq 0x30(%rbx),%rdx`  arg3 -> callee r15
  - `0x218f6b leaq (,%r15,4),%rcx` + `0x218f73 addq (%rax),%rcx`  arg4 = *(rbx+0x38)+r15*4  (callee's %r14 fraction destination = element r15 of a 2nd float array)
- Output consumption:
  - `0x218f81 movq 0x18(%rbx),%rax` ; `0x218f85 movq (%rax),%rax` ; `0x218f88 movss %xmm0,(%rax,%r15,4)` — **mean score stored UNCONDITIONALLY** into score array[r15].
  - fraction already routed (above) into fraction array[r15] by the callee writing to (%r14).
- Loop proof: `0x218ff6 incq %r15` / `0x218ff9 cmpq -0x228(%rbp),%r15` / `0x219000 jl 0x218e70`. r15 = loop index.
- **Shown negative:** window 0x218f81..0x219006 has NO `ucomiss`/`comiss` and NO float-conditional branch on xmm0 — only `testq` null checks, std::vector operator-delete arithmetic, and the loop cmpq. So no gate here.

### Where the gate actually is (LEAD)
- `0x218e20` has **0 direct E8 callers** but is stored as LE64 `0x218e20` in `__const` at file offset `0x6580e0` (section __const 0x6501f0..0x6647a0) -> dispatched indirectly (vtable / task descriptor). 
- The real accept/reject consumer is the downstream owner that later reads the two index-aligned arrays at **rbx+0x18 (scores)** and **rbx+0x38 (fractions)**. Tracing that requires following the rbx object / the __const descriptor at 0x6580e0 — NOT statically resolvable via direct call chain in this pass.

### Scope-bound disclaimer
Investigated ONLY: the static call graph of 0x218b30, the single call site 0x218f7c, its enclosing function 0x218e20, and stored-pointer location of 0x218e20. Did NOT: run LLDB on a live LRI, resolve the indirect dispatcher at __const 0x6580e0, identify the rbx object's class, or locate the downstream reader of rbx+0x18/+0x38. Did NOT confirm these arrays gate "the whole merge" — that claim remains OPEN and lives with the downstream array consumer.

## Verifier correction(s) — load-bearing
- **0x218f79**: 4C 89 F6 confirmed: instruction movq %r14,%rsi is correct. However r14 = -0x220(%rbp) (set at 0x218f4d leaq -0x220(%rbp),%r14), NOT -0xd0(%rbp). The -0xd0(%rbp) address is passed as %rdx arg3 to 0x23faf0 at 0x218f57. Instruction encoding PASS; description of r14's frame offset is WRONG (-0x220 not -0xd0).
