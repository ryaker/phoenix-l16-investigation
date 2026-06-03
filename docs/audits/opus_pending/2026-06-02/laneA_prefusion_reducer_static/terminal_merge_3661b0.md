<!-- provenance: workflow wf_cb406491-3d3 (l16-prefusion-fanout-w4), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## IRAMP terminal-merge confirmation + producer barrier (static, libcp.dylib x86_64)

Binary: /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib (re-extractable via `arch -x86_64 lldb --batch -o 'target create libcp.dylib' -o 'disassemble --start-address 0xADDR --count N'`).

### PART 1 — 0x3661b0 produces pixels (terminal N->1 merge). OBSERVED.
- Accumulate body 0x36aa30..0x36aa6c: per-contributor vec4 read `movaps (%r10,%rdi),%xmm0`, weight `mulss`/`mulps`, then **`0x36aa53 addps (%rsi,%rdi),%xmm1` ; `0x36aa57 movaps %xmm1,(%rsi,%rdi)`** = accumulate-store. Dest base `%rsi` set at `0x36a9ff addq -0x1200(%rbp),%rsi`.
- `-0x1200(%rbp)` is the data-ptr field of a stack tile descriptor (built 0x36a40b-0x36a4b6 via helpers 0xf540/0xf7c0; `0x36a4b6 addq %rbx,-0x1200(%rbp)` = crop-origin pointer advance).
- After the N-loop, blend-back 0x36ab88-0x36ac38 merges the accumulated tile (`%r12=-0x1200(%rbp)`) into the **real output image** base `-0x4270(%rbp)`.
- `-0x4270` traces to arg0: `0x3661ce movq %r15,-0x4388(%rbp)` (arg0); `0x36a08f movq 0x38(%r15),%rdi`; `0x36a0f1 movl 0x18(%rdi),%r10d`(stride); `0x36a104 addq 0x20(%rdi),%rcx`(data ptr); `0x36a14b movq %rcx,-0x4270(%rbp)`. => output buffer = **[arg0+0x38].dataptr (+0x20)**.
- N-contributor controls from `[arg0+8]`: `0x366b18 movq 0x8(%r15),%r13`; count `[%r13+0x10]` (`0x36aa5e`); weight plane `[%r13+0x28]` (`0x36aa3b`). Loop is over ALL contributors -> reduced to 1 output pixel buffer.
- Dual gate satisfied for the IRAMP path: entry 0x365960 enforces matching N>1 vectors (`0x3659a8-0x3659d0`); body 0x3661b0 reduces N->1 (store `0x36aa57`).

### Framing correction
- The function the caller (PipelineCache::processLevel0 @ 0x3ec770) invokes with src1/src2/+0x270/+0x258 is **0x365960** (the IRAMP entry), which then calls **0x3661b0** at `0x365f4b` (rdi=-0x158(%rbp) work-record, rsi=%rbx). 0x3661b0 is the inner accumulate body, not the caller-facing entry.

### PART 2 — producer of cache+0x258 / +0x270 is NOT statically reachable. OBSERVED barrier.
- Caller arg map (`0x3ec7ac-0x3ec7da`): src1=[cache+0x238]->rsi, src2=[cache+0x248]->rdx, **rcx=&cache+0x270 (source image-generator vector, arg4)**, **r8=&cache+0x258 (paired record/warpfield vector, arg5)**. NOTE: this is the **reverse** of the thread's stated +0x258=source / +0x270=warp mapping; cross-checked against committed `docs/evidence/bundle_proof_iramp_live_signature_and_warp_records.md` lines 65-66, 175.
- Records are built upstream in initResAmp scope (gated by strings "Requested PipelineCache::processLevel0 before initResamp()!" @0x3ec837 and "ImageResolutionAmp did not create image of correct size!" @0x3ec879).
- Source/warp descriptor producer = **indirect virtual call**: `0x3ebf3d movq 0x1d8(%r12),%rdi` ; `0x3ebf45 movq (%rdi),%rax` ; `0x3ebf48 movq 0x18(%rax),%rax` ; `0x3ebf5d callq *%rax`. Dispatch via [PipelineCache+0x1d8] vtable slot +0x18. **Static cannot cross this.** Whether the concrete target is the 0x216f60 / 0x23faf0 family is a LEAD requiring runtime resolution of %rax — NOT done here.

### Verdict on two-stage split
Structurally CONSISTENT: geometry/warp records produced upstream (vtable-dispatched, unresolved), pixels merged in 0x3661b0 consumer (OBSERVED). Producer-identity leg = LEAD pending runtime, not OBSERVED. NEVER PROVEN.

## Verifier note(s)
- **0x3ebf5d (runtime)**: Not extracted. This is a LEAD item explicitly marked as requiring runtime LLDB. Static disassembly cannot resolve the indirect call target. No verdict possible from static analysis alone.
