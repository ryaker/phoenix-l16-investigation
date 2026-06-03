<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Quarantine packet — src2 secondary ROI box in reducer 0x3661b0 (WEAK-LABELED)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` (Mach-O x86_64). Method: static `arch -x86_64 lldb --batch ... disassemble`. NOT verified/proven — re-extract every VA below.

### Prediction tested
"src2 box at -0x17d0/-0x17e0 is later read inside 0x3661b0 to clip the secondary/narrow-kernel resample region."

### Verdict: REFUTED as stated; box drives an in-place margin zero-fill of src2, performed inside 0x374ac0, not a downstream resample clip in 0x3661b0.

### Chain (OBSERVED)
1. `0x366900-0x36690e`: `movaps %xmm0,-0x17b0 / -0x17c0 / -0x17d0` — zero-inits a 48-byte object spanning -0x17d0..-0x17a1 (a managed strided-view value type; see destructor 0xf4e0 layout: ptr at +0x20, frees +0x28).
2. `0x366915`: `movq 0x10(%r15),%rsi` — **src2 = descriptor at 0x10(r15)** loaded as intersect arg2.
3. `0x366920-0x366946`: builds rect at -0x17e0 = caller bound **inset by 8 px on all sides** (`leal -0x8`, `leal 0x8`). Pad = 8 (narrow/secondary kernel half-width), contrasting the pad 0x18 of src1.
4. `0x36694c/0x366953/0x36695a`: `rdi=-0x17d0 (out box)`, `rdx=-0x17e0 (inset rect)`, `call 0x374ac0`.
5. Inside `0x374ac0`: reads src2 dims `0x30/0x34(%r14)` (`0x374b0a/0x374b0e`); intersects with the inset rect; then `0x374cd5 movq 0x20(%rax),%rdi` (src2 buffer/owner), `0x374cf1 callq *%rax` (vtable +0x30 sink), and `0x374d70..0x374d88` row loop calling `__bzero` (`0x374d76`) to **zero src2 buffer rows outside the clipped ROI band**.
6. Back in 0x3661b0: the box and all clip-math outputs are **dead**. The only load-from the -0x17b0..-0x17e0 cluster after the call is `0x3669ad movl -0x17b8(%rbp),%esi`, and -0x17b8 was zeroed at `0x366907`. Writes at `0x3669c0` (data ptr), `0x3669c7` (width), `0x3669cd` (height), `0x3669d6/e8/f1` (residual box) are never re-read. Failure path `0x3669f9->0x366a00 callq 0xf4e0` destructs the box.

### Interpretation (LEAD)
The src2 secondary box's runtime-static role at this call site is to define the valid (pad-8 inset) ∩ src2-dims region and have 0x374ac0 ZERO out src2's pixel margins in place — i.e. it prepares/cleans src2's buffer, it does not restrict a later sampling pass within 0x3661b0 and is not an output clip. The "pad 8" inset (vs src1 pad 0x18) is the only place the narrow-kernel half-width manifests here.

### Cross-check
Extends committed `docs/evidence/bundle_proof_pair_grid_roi_transform.md`, which independently labeled 0x374ac0 (at the separate 0x366f12 call site) as "clamps/intersects against image dims then zero-fills out-of-block margins through a callback sink." Same primitive, new caller (0x36695a) + new operand (src2 = 0x10(r15)). Novel: the src2 binding, the pad-8 inset, and the proof the returned box is dead in 0x3661b0.