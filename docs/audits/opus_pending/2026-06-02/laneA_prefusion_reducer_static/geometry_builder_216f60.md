<!-- provenance: workflow wf_cb406491-3d3 (l16-prefusion-fanout-w4), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm only).
**Verifier reliability:** one item flagged (a movsd/cvtss2sd descriptor nuance OR an explicitly runtime-only LEAD) — core OBSERVED; see correction

## THREAD: Classify 0x216f60 output role; decode 0x217250..0x2184f0 (suspected accumulate)

### PREDICTION (pre-verification)
0x216f60 = geometry/warp-record builder. -0x6c8/-0x6c4 mulss = scaled geometry coordinate (not pixels); 0x25e4b0 = transform-record init (not pixel/record append). **CONFIRMED.**

### VERDICT
**0x216f60 is a GEOMETRY / WARP-RECORD BUILDER, NOT a pixel merge and NOT a pixel reducer.** The 0x217250..0x2184f0 block assembles transform-record fields into a struct at `[-0x5b0(%rbp)]` (the State object passed in rdi). No pixel buffer, no per-contributor accumulation loop, no N-to-1 reduction.

### Q1 — Is the -0x6c8/-0x6c4 mulss GEOMETRY or PIXEL? -> GEOMETRY (scalar-scaled coordinate)
- `0x217241 movss 0xf0(%rax),%xmm1` -> xmm1 = State[+0xf0] scalar.
- `0x21726e movss -0x3c0(%rbp),%xmm0 ; 0x217276 mulss %xmm1,%xmm0 ; 0x21727a movss %xmm0,-0x6c8`
- `0x217282 movss -0x3b4(%rbp),%xmm0 ; 0x21728a mulss %xmm1,%xmm0 ; 0x21728e movss %xmm0,-0x6c4`
- Source -0x3c0/-0x3b4 are fields of the `-0x3c8` transform struct just built by `0x264440` (0x2171aa, rdi=-0x3c8).
- **Lifetime proof (whole-function grep):** -0x6c8/-0x6c4 each written once (0x21727a/0x21728e) and read once (0x2176a1/0x2176ca). **No `addss` back into the slot; no loop.** This is `coord * scale`, a one-shot geometry product — NOT normal-equations/least-squares accumulation and NOT pixel summation.

### Q2 — What does 0x216f60 WRITE as output? -> fields of a transform/geometry record on the State object
- The destination object is `[-0x5b0(%rbp)]` = original rdi (saved at 0x216f8f). `0x217203 movq -0x5b0(%rbp),%rax ; 0x21720a leaq 0x48(%rax),%rbx` — State[+0x48] is used as the rdx **input** to 0x25e4b0, i.e. the +0x48 the thread flags is a READ transform field, not the write dest.
- The -0x6c8..-0x5e0 stack block is the staged transform record (matrix rows from -0x230/-0x280 via 0x25e4b0, scalars -0x238/-0x234, scaled coords -0x6c8/-0x6c4) assembled before being committed. It is a **record/matrix**, not an image buffer.

### Q3 — Does 0x25e4b0 append a record or write pixels? -> NEITHER; it INITIALIZES a transform matrix
- `0x25e4b4 movl $0x3f800000,(%rdi)` ... `+0x14,+0x28,+0x3c` = float 1.0 diagonal; `movups xmm0(=0)` off-diagonals; `+0x48 = packed (1.0,1.0)`; tail `jmp 0x25e0c0`.
- 0x25e0c0 does cvtps2pd float->double on matrix element offsets (+0x24..+0x50) of two structs = matrix composition setup.
- This is an **identity-homography/affine initializer + double-precision compose**, not a vector append and not a pixel write.

### Supporting helpers
- `0x264440` -> shim (`edx=1; jmp 0x264270`); sibling 0x264460 = identity init + std::vector<float> deep-copy (transform + coefficient vector).
- `0x218390` (called 3x at 0x2171d7/0x2171fe/0x217b3f) = matrix*vector compose gated on scalar!=0; produces -0x138/-0x1e0 fed into 0x25e4b0.

### Hard-rejection filters
Not applicable — this function touches NO pixels. The "1 source/pixel", "pick 1 reference frame", "single-A multiple-B" filters concern the pixel merge, which is elsewhere.

### Scope / what was NOT done
- STATIC ONLY (`arch -x86_64 lldb --batch ... disassemble`); no runtime, no register dumps.
- Did NOT trace what consumes the built transform records. The 0x216f60 tail (0x217e00..0x2180d5) is exception-unwind + string/shared-count cleanup with **indirect `callq *0x20(%rax)`/`*0x28(%rax)` vtable dispatch that static analysis cannot cross** — the consumer of the geometry records is reached via vtable indirection and REQUIRES RUNTIME to resolve.
- Did NOT decode 0x217665..0x2184f0 instruction-by-instruction beyond the -0x6c8/-0x6c4 read sites; confirmed only that no add-back accumulation into those slots exists.
- Did NOT cross-check against the prior 0xe6ba0/0x1f0a00/0x218390 geometry-cluster evidence docs line-by-line; consistent with the stated prior-wave finding that the cluster is geometry/transform setup.
- All VAs bound to libcp.dylib at /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib (___lldb_unnamed_symbol_216f60 @ __TEXT.__text+2182416). Re-verify if binary swapped.

## Verifier note(s)
- **0x218390 (+0..+189)**: MOSTLY CONFIRMED with one inaccuracy: the body uses movsd (not cvtss2sd) to load from -0x40/-0x90. The float->double promotion happens in the CALLER (0x25e0c0), not inside 0x218390. Confirmed: 0x1c79e0 is called at +51 with rsi=-0x40/%rbp and rdx=-0x90/%rbp as output slots; then movsd loads from those slots; mulsd matrix row products confirmed throughout; gate is ucomisd (saved xmm1) vs 0.0 double at 0x2183d4, je 0x218714 confirmed. Overall character (geometry matrix-multiply, gated by input scalar, pure double arithmetic, no pixel accumulation) is accurate. The 'cvtss2sd loads' descriptor for 0x218390 body is technically incorrect - loads are movsd.
