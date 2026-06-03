<!-- provenance: workflow wf_86500d78-8bf (l16-prefusion-fanout-w3), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Cluster verdict: 0x218390 / 0x1f0a00 / 0x216f60 body are NOT the merge accumulator

**PREDICTION REFUTED** for "0x218390 is the per-pair accumulate." No multi-frame per-element float accumulator exists in any of the three candidates.

### (1) 0x216f60 loop / body 0x217100-0x2171f0 (OBSERVED, static)
- Real per-pair loop is EARLIER, at `0x217030-0x217083`: SIMD `movss/insertps` -> `cmpltps %xmm2,%xmm4` (compare > 0) -> `andps` -> `paddd %xmm2,%xmm0`, horizontally reduced to `%ebx` at `0x217085-0x217093`. This COUNTS positive coordinate pairs -> matches ">=8 positive pairs."
- Body at `0x217100`: `callq 0xe6ba0` (+428) -> result fed to `callq 0x1f0a00` (+485) -> `callq 0x218390` (+631) and again (+670). Sequence order in question is correct.
- BUT no back-edge `j* 0x217100` found in a 700-insn scan; body is straight-line per-record in static view. **Body iteration count per merge needs runtime.**

### (2) 0x218390 = TRANSFORM COMPOSER, not accumulator (OBSERVED)
- `je 0x218714` at `0x2183d8`: when xmm1 scalar arg == 0, copies input struct through (the loop calls it with xmm1=0 via `xorpd %xmm1,%xmm1` at 0x2171d3/0x2171fa).
- `0x2183e8-0x21845e` mulsd chains into fresh slots -0x140..-0x190; `0x21848c-0x2185fd` `movddup/mulpd/addpd` row products into -0x120..-0xe0 = a 3x3/affine MATRIX PRODUCT, each output written ONCE (no read-modify-write).
- `0x218605` loads `{-0.0,-0.0}` (EA 0x5a80c0) used by `xorpd` negations (0x218615/0x218635/0x2186c4/0x2186f4) -> cofactor/cross-product (adjugate/inverse) pattern.
- Helpers: `0x1c79e0` = matrix*vector apply; `0x1c0910` = `__sincos_stret` rotation builder. **0x218390 builds/composes a parametric transform.**

### (3) 0x1f0a00 = map iterator + per-record extract (OBSERVED)
- `0x1f0a30-0x1f0a7f`: std::__1 RB-tree/map walk (child ptr 0x10(%rax), flag bytes 0x1c8/0x1c0(%rbx)) selecting ONE node.
- `0x1f08a0` = `operator new(0xe8)` + `cvtps2pd` float32->float64 member fill; `0x1f0530` = `operator new(0x220)` + same. **Per-record CONSTRUCTOR/converter, not a reducer.**

### addsd at 0x2171e4 (OBSERVED)
`movsd 0x3921ec(%rip),%xmm0` reads constant 2.0 (EA 0x5a93d0); `addsd -0x600(%rbp),%xmm0` adds a per-record scalar to that constant -> a bias for the next 0x218390 angle arg, NOT a cross-frame sum.

### Hard-rejection-filter note (Light pseudo-code)
0x1f0a00 selecting ONE map record per call resembles a per-output "pick" pattern; this is per-record TRANSFORM-PARAMETER lookup (geometry/rotation), not pixel-value merge selection. Does NOT by itself satisfy or violate the merge filters - it is upstream geometry, not the pixel reducer.