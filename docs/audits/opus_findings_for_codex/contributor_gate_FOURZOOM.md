> GRADUATED to four-zoom OBSERVED (2026-06-03, W1d — four_zoom_data_W1d.md). sentinel 0x36930f fires 4-zoom; index-0=0x80000000 uniform all tiers. Scope=first-hit/firing/tier, Unit-1.

<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Quarantine packet (WEAK-LABELED) — IRAMP reducer 0x3661b0 contributor gate + loop bound + score role

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` (Mach-O x86_64). Method: static `arch -x86_64 lldb --batch ... disassemble`. NOT runtime. Scope-bound to the disassembled ranges below; no LLDB trace, no LRI parse, no proof the loop fires under four-zoom.

### Q1 — what sets the value compared vs 0x80000000 at 0x36930f, and what does the gate skip
Raw (OBSERVED):
```
0x3692f0  leaq (%rcx,%rcx,4),%rdx        ; rcx = contributor index
0x3692f4  shlq $0x7,%rdx                 ; *0x280 stride into source-record array at %rdi
0x3692f8  movl 0x28(%rdi,%rdx),%eax
0x3692fc  imull %r13d,%eax               ; *stride_x
0x369300  addl %r8d,%eax                 ; +base
0x369303  movslq %eax,%rsi
0x369306  movq 0x30(%rdi,%rdx),%r12      ; r12 = per-contributor index/coord table base
0x36930b  movl (%r12,%rsi,8),%eax        ; <-- WRITER of the compared value: lookup into table
0x36930f  cmpl $0x80000000,%eax
0x369314  jne 0x369320                   ; valid index -> process
0x369316  movl %ebx,%edx                 ; sentinel case: load default coords
0x369318  movl %r15d,%esi
0x36931b  jmp 0x369f0b                   ; skip SAD/score/warp body, go to loop tail
```
Interpretation (LEAD): the compared value is a packed source-pixel **index/coordinate** fetched from the per-contributor table at record+0x30 (base) indexed by the computed source position. `0x80000000` is the "invalid / out-of-frame / no-coverage" index sentinel. When equal, the contributor is **skipped for this tile** (no SAD block-match, no 0x36cde0 score, no warp) and falls straight to the loop-advance tail. The reject-sentinel `0x8000000080000000` is written into the contributor record on the reject path at 0x369ed0/0x369ee1. This matches prior committed note `bundle_proof_iramp_live_signature_and_warp_records.md:159` ("writes sentinel 0x8000000080000000 for rejected pairs") — that doc had the WRITE; this packet adds the READ/gate VAs (0x36930b/0x36930f/0x369314).

### Q2 — loop bound (where N=number of contributors comes from)
Raw (OBSERVED):
```
0x3692ce  movq -0x1800(%rbp),%rdi        ; vector BEGIN
0x3692d5  movq -0x17f8(%rbp),%r9         ; vector END
0x3692dc  cmpq %rdi,%r9 ; je 0x369f2a    ; empty-vector early out
...
0x369f0b  incq %rcx                      ; advance contributor counter
0x369f0e  movq %r9,%rax
0x369f11  subq %rdi,%rax                 ; (end-begin) bytes
0x369f14  sarq $0x7,%rax                 ; /0x80
0x369f18  imulq %r14,%rax                ; r14=0xCCCCCCCCCCCCCCCD -> divide quotient by 5
0x369f1c  cmpq %rax,%rcx                 ; counter vs element count
```
Interpretation (LEAD): N = element count of the source-record vector = ((end-begin)>>7)/5. The `/5` (magic 0xCC..CD) and the per-record `*0x280` stride (leaq*5;shl 7 = 0x280 = 5*0x80) indicate each vector element is 5 sub-records of 0x80 bytes (0x280 total) — consistent with the scaffold's "5-item vector at descriptor +0x20 (cache+0x258)". So the loop bound is data-driven from the vector span; it is NOT a hardcoded contributor count. (LEAD: tying -0x1800/-0x17f8 to cache+0x258 not re-verified statically here.)

### Q3 — does the 0x36cde0 score gate inclusion (branch/skip) or only weight
Raw (OBSERVED):
```
0x369e3f  callq 0x36cde0                 ; per-contributor score -> xmm0
0x369e44  movq -0x42f0(%rbp),%rcx
0x369e4b  movq -0x4300(%rbp),%rdx
0x369e52  movl 0x58(%rcx,%rdx),%eax
0x369e5d  imull %r13d,%eax
0x369e68  addl %r8d,%eax
0x369e6b  cltq
0x369e6d  movq 0x60(%rcx,%rdx),%rcx
0x369e72  leaq (%rax,%rax,2),%rax        ; *3 (3-float tuple stride)
0x369e7e  movss %xmm1,(%rcx,%rax,4)      ; tuple[0] = warp dx (-0x4310)
0x369e8b  movss %xmm1,0x4(%rcx,%rax,4)   ; tuple[1] = warp dy (-0x4320)
0x369e91  movss %xmm0,0x8(%rcx,%rax,4)   ; tuple[2] = SCORE (0x36cde0 result), UNCONDITIONAL
```
Interpretation: REFUTES prediction (3). There is **no compare/branch on the 0x36cde0 result** between the call (0x369e3f) and the three `movss` stores. The score is stored as the 3rd field of the per-contributor (dx,dy,score) tuple at base record+0x60, stride 12 bytes. It is a **weight/annotation**, consistent with the downstream 1/Sscore-normalized weighted average (rcpss at 0x36a938, per scaffold). The score does NOT gate membership in this loop.

The real per-contributor inclusion gates observed are:
1. index-validity sentinel `0x80000000` at 0x36930f (Q1) — full skip.
2. variance/SAD-derived guard at 0x369c21 `je 0x369cb0` (when xmm1 = a*c - b^2 <= 0, warp deltas zeroed) and the magnitude/overflow guard ending at 0x369c9d `jne` — these zero the warp delta but the tuple is still stored (degraded, not skipped). (0x369c9d labeled LEAD: exact predicate not fully reduced.)

### Open / not investigated
- Did NOT runtime-confirm any of this fires under four-zoom bridge HDR (static only).
- Did NOT prove -0x1800/-0x17f8(%rbp) == cache+0x258 / descriptor+0x20 statically (taken from scaffold).
- Did NOT decode 0x36cde0 internals here (covered by bundle_lldb_iramp_36cde0_scalar.md).
- Did NOT determine whether the (dx,dy,score) tuple array at record+0x60 is later filtered by score downstream (the gate-vs-weight question for the SUBSEQUENT consumer remains OPEN — this packet only proves it is not gated WITHIN 0x3661b0's contributor loop).