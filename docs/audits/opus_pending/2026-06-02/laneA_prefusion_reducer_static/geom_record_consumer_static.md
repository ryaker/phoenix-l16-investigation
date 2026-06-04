<!-- provenance: workflow wf_d596de8b-90c (l16-unfenced-w10), 2026-06-03; finder + verifier; reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm).
**Verifier reliability:** core PASS (0x216f60 callers 0x22aaf0/0x22d250 confirmed); one sub-detail flagged

## 0x216f60 consumer — RESOLVED (two THREAD-premise corrections)

### Q1 — Who calls 0x216f60, and what does it populate?
Exactly two direct callers (objdump xref on installed libcp.dylib):
- `0x22acf5` inside State operator `0x22aaf0`
- `0x22d74c` inside State operator `0x22d250`

Both pass `(rdi,rsi = output-collection ptrs, rdx/rcx = current keyed record node)`. The iterated node has stride `0x28` and is walked as an int-keyed std::map (node compare `cmpl 0x20(%rbx),%eax`, follow `(%rbx)`/`0x8(%rbx)`). 0x216f60 does positive-(x,y) coordinate scan/count (committed window 0x217030-0x2170d4: counts only lanes where 0<x AND 0<y, threshold >=8) plus record population.

CORRECTION: 0x216f60 does NOT "build a transform/matrix State into [-0x5b0(rbp)]". At entry `0x216f8f movq %rdi,-0x5b0(%rbp)` stores the INCOMING first arg; -0x5b0 is an INPUT pointer, not a built-and-threaded State. The function returns normally at `0x217d23`.

### Q2 — Does that State feed FusionCacheBayer/IRAMP, or another consumer?
Another consumer: the CalibDataProcessor **"State machine"**, not (directly) FusionCacheBayer 0x406a10 / IRAMP warp records.
- Committed runtime stack (bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md): `0x22acfa -> 0x22f3ff -> 0x227063`.
- `0x22f0f0` = dispatcher (embeds string "State machine" at 0x22f11b; mach_timebase/mach_absolute_time profiling). It virtually invokes the operator via function-object **vtable slot +0x30** at `0x22f3fd`, then stores the returned `eax` (next-State enum int) to `(%r12)` at `0x22f3ff` — a scalar status, NOT a State pointer threaded to a warp consumer.
- Dispatcher callers: `0x22705e` (in 0x226c70) and `0x2277b3`.

### Q3 — Indirect dispatch 0x217ef8/0x217f0c object identity?
The THREAD's "tail dispatch via callq *0x20(%rax)/*0x28(%rax)" is a MISREAD. Region 0x217ec4-0x2180da is the **exception-cleanup landing pad** of 0x216f60: `0x217ef8 callq *0x20(%rax)` and `0x217f0c callq *0x28(%rax)` are virtual DESTRUCTOR slot calls on local sub-objects during unwinding (guarded by `cmpq %r15,%rdi` SSO/self checks), the whole block terminating in `_Unwind_Resume` at `0x2180d2`. Not the productive output dispatch.

The REAL productive virtual dispatch (the one that routes INTO operator 0x22aaf0) is the State-machine function-object call at `0x22f3fd` (vtable slot +0x30). Its object identity is static-uncrossable from literal section dumps because libcp uses LC_DYLD_INFO_ONLY rebase fixups (operator addresses are not literal in __const/__data — confirmed: 0x22aaf0/0x22d250 absent from __TEXT/__DATA __const and __data; GOT slot at 0x226c87 reads 0 statically). Committed evidence already crossed it at runtime: vtable address point `0x658958` = `runHigherGroupCams::$_12`, +0x30 operator (bundle_proof_state_machine_terminal_22e1d0_static.md).

### Net for CLM-PREFUSION-002 geometry side
0x216f60 is a State-machine (CalibDataProcessor) per-record coordinate scan/count + record-population helper, NOT a builder whose State output threads into FusionCacheBayer/IRAMP via the 0x217ef8 dispatch. The geometry/warp link to FusionCacheBayer 0x406a10 is NOT established by this call chain; if it exists it must be via the State-machine's record trees being read by a separate consumer downstream of the dispatcher, which static cannot cross past the +0x30 function-object dispatch.

## Verifier note(s)
- **0x22acf5**: libcp.dylib[0x22acf5] <+517>: callq 0x216f60 -- confirmed inside ___lldb_unnamed_symbol_22aaf0. rdi: movq -0x78(%rbp),%rdi at 0x22acea YES. rsi: movq -0x70(%rbp),%rsi at 0x22acee YES. rdx: movq %rbx,%rdx at 0x22acf2 YES. rcx: loaded from movq -0x60(%rbp),%rcx at 0x22acc2, NOT from rbx. Claim 'rcx=rbx' is NOT supported by static disassembly; rcx comes from -0x60(rbp). r8d=0 and r9d=0 (xorl at 0x22ace4/0x22ace7) are present but not mentioned in claim.
