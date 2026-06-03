<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

# Quarantine packet: terminal merge accept/reject — static (libcp.dylib)

Binary: /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib (Mach-O x86_64). All VAs file/image-relative as printed by lldb disassemble.

## Q1 — 0x218b30 guard: what it accepts vs rejects (OBSERVED)
Per-pair loop 0x218bc0..0x218cd0 over array at (%r15) deref into %rdx; stride 8 bytes per pair (2 floats {x,y}); index %rbx; bound from 0x18(%rbx) container size/0x14 record-stride math (0x218cbb..0x218ccd, magic 0xCCCCCCCCCCCCCCCD => /20). xmm0 = 0.0 (0x218b7a).
Two reject-to-continue branches, both targeting 0x218cb8 (`incq %rbx` loop-advance):
- 0x218bc0 `ucomiss (%rdx,%rbx,8), %xmm0` ; 0x218bc4 `jae 0x218cb8` -> skip unless x STRICTLY > 0 (jae also taken on unordered/NaN). Sentinel x=-1.0 (0xbf800000): 0>=-1 true -> SKIPPED. This is the sentinel rejection.
- 0x218bca `movss 0x4(%rdx,%rbx,8), %xmm3` ; 0x218bd0 `ucomiss %xmm0,%xmm3` ; 0x218bd3 `jbe 0x218cb8` -> skip unless y STRICTLY > 0.
ACCEPT = both lanes strictly positive (== the positive-pair predicate). The (-1,-1) sentinel from 0x21b923/0x21b92a is rejected by the x-lane guard at 0x218bc4. CORRECTION to scaffold: 0x218bc4 is the first of a PAIR (x then y) of guards, not a lone gate.

## Q2 — terminal accept store? (OBSERVED)
NO per-record accept store in 0x218b30. Accepted pairs mutate only running accumulators:
- 0x218ca4 `addss %xmm3,%xmm1` (sum of minss-clamped magnitude, clamp at 0x218ca0 against xmm9)
- 0x218c99 `seta %cl` / 0x218cab `addl %ecx,%r10d` (count of |score|>xmm9)
- 0x218cae `incl %r9d` (count of accepted pairs)
Epilogue stores are STATISTICS, not a record:
- 0x218cd6 cvtsi2ss r9 ; 0x218cdb add eps ; 0x218ceb `divss` -> 1/(r9+eps)
- xmm2 = r10/(r9+eps) -> 0x218cfb `movss %xmm2,(%r14)` (fraction exceeding threshold)
- xmm0 = xmm1/(r9+eps) (mean clamped score) returned (0x218d00..0x218d0e retq)
=> 0x218b30 is a SCORE/STATISTIC REDUCER over accepted pairs (LEAD on role). Acceptance is purely the absence of skip; there is no 'accept this contributor into the merge' store here.

## Q3 — >=8 threshold whole-merge fallback (OBSERVED; threshold itself in prior doc bundle_static_prefusion_sentinel_216f60_scan_count_window.md L83-87)
- 0x2170d1 `cmpl $0x8,%ebx` ; 0x2170d4 `jl 0x217d00`  (branch VA 0x2170d4 -> target 0x217d00)
- NEW: 0x217d00 = CLEAN cleanup+return (0x217d07 basic_string dtor, stack restore, 0x217d23 retq). Not a throw. <8 positive pairs => skip the entire merge-construction block (0x2170da pxor-zeroed locals -> 0x21710c callq 0xe6ba0) and return.
- Throw path is SEPARATE: 0x217d24 builds "src_image cannot be empty" (string at 0x217d3b) reached from empty-input guards 0x216fbc/0x216fc7 `jle 0x217d24` and empty-vector 0x216fd8 `je 0x217d00`.

## Scope / not investigated
- Did NOT runtime-confirm any of this (Codex owns the watchpoints; instructed not to re-prove). Static only.
- Did NOT identify caller(s) of 0x218b30 or 0x216f60, nor which one runs per zoom tier.
- The semantic role labels ("score reducer", "whole-merge fallback") are LEADs; only the disasm/branch facts are OBSERVED.
- 0x218b30's container at 0x18(%rbx) and the -0x58(%rbp) 3x2 affine matrix (built by callq 0x267000 at 0x218b54, used 0x218be4..0x218c24 as 6 coeffs) transform each pair before the threshold tests — affine source/role not traced.
- Whether 0xe6ba0 (the skipped heavy body) is the actual N->1 reducer is OUT OF SCOPE here.