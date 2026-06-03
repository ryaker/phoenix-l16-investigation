<!-- provenance: workflow wf_86500d78-8bf (l16-prefusion-fanout-w3), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

Matrix at 0x36ac7d row loads resolve to __DATA,__bss, NOT rodata. Storage-class LEAD (fixed RODATA constant) REFUTED; orthonormal-rotation LEAD numerically consistent (values from runtime).

(1) Rip targets: movss@0x36ac7d->0x671988, movq@0x36ac85->0x671980, movss@0x36ac91->0x671994, movq@0x36ac99->0x67198c, movss@0x36aca5->0x6719a0, movq@0x36acad->0x671998; contiguous 0x671980..0x6719a4; static read all 0.0/0x00.

(2) otool -l ranges: __TEXT,__const 0x5a74a0..0x62eb29; __DATA,__const 0x6501f0..0x664797; __DATA,__data 0x6647a0..0x66d147; __DATA,__bss 0x66d170..0x6740f0 offset 0 (S_ZEROFILL). All six targets in __bss => runtime-populated, not a constant.

(3) Numeric test (committed runtime rows): row0=(0.57735002,0.57735002,0.57735002) norm 0.99999957 sum 1.7320501; row1=(0.70710999,0,-0.70710999) norm 1.00000454 sum 0; row2=(0.40825000,-0.81650001,0.40825000) norm 1.00000420 sum 0; r0.r1=r0.r2=r1.r2=0.0 => unit-norm + mutually orthogonal = orthonormal; basis (1/sqrt3)(1,1,1),(1/sqrt2)(1,0,-1),(1/sqrt6)(1,-2,1); row0 luminance axis, rows1-2 chrominance plane.

Transform body 0x36acf0..0x36ad32 (odd) and 0x36ad50..0x36adac (even, the committed-bundle body) compute out[i]=in0*row0[i]+in1*row1[i]+in2*row2[i], lane3 forced 1.0 via blendps. Adds the static storage-class classification the committed bundle_lldb_iramp_post_weighted_add_shaping.md did not assert.

Scope: static cannot identify the __bss producer or timing; orthonormal values known only from committed live capture; did not investigate downstream after 0x36adac.