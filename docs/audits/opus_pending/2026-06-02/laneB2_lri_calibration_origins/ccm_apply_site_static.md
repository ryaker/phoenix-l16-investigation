<!-- provenance: workflow wf_d596de8b-90c (l16-unfenced-w10), 2026-06-03; finder + verifier; reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm).
**Verifier reliability:** apply-site located; verifier flagged 2 VA-precision details (corrected in packet); core (CCM values absent from binary => parsed from LRI; libcp applies-not-selects) stands

## CCM Consuming Site — Static Findings (libcp.dylib, Mach-O x86_64)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` (6,935,696 bytes, Oct 8 2019). All VAs re-extractable via `arch -x86_64 lldb --batch -o 'target create <lib>' -o 'disassemble --start-address 0xADDR --count N'` or `objdump -d`.

### (1) ImageApplyColorMatrix + setColorCorrection bodies — VAs

| What | VA (entry) | Evidence |
|---|---|---|
| ImageApplyColorMatrix vec4 **Mat 4x4** apply ($_3) | **0xbfa20** | matrix load 0xbfa4b; 4x4 MAC loop 0xbfad0; vtable @0x652968 (op() slot=0xbfa20) |
| GN ImageApplyColorMatrix Image<float> **Mat 3x3** apply ($_2) | **0x300980** | matrix pre-combine 0x3009a0; per-pixel 3-ch dot loop 0x300ab4; RTTI stub 0x300c00 |
| GN ImageApplyColorMatrix vec4 Mat 3x3 ($_3) | RTTI name @0x5f34f0, stub @0x304854 | (third apply overload) |
| setColorCorrection lambda op() ($_58 family) | **0x3464d5** | reads gain f32 @0x1618(state), byte mode @0x161c(state); calls 0xfc2f0 |
| setColorCorrection apply worker | **0xfc2f0** | gain+byte-mode → grid resampler 0x106cb0 |

RTTI name strings (in `__const`): ApplyCM/4x4 @0x5ab690, GN/3x3 Image<f> @0x5f31c0, setCC $_58..$_63 @0x5f8530/0x5f8790/0x5f8890/0x5f8990/0x5f8aa0/0x5f8d00. No exported symbols (`nm` = 0 hits), all anonymous-namespace — matches brief.

### (2) Block-6 variant {0,2,6} selection — NOT at the consuming site

- Zero `cmp/movl $0x2`/`$0x6` and zero indirect-switch tables in the setColorCorrection region (disasm lines ~803000–807000).
- D50 row-sum constants 0.9642 / 0.8252 have **0 f32 hits** in the entire binary → CCM matrices are parsed from LRI Block-6 at runtime, not hardcoded.
- **Conclusion: libcp APPLIES a pre-selected ColorCorrection; the {0,2,6} f2.f1 variant pick is an upstream LRI Block-6 parse decision, outside the consuming site.** PREDICTION ("fixed selection of variant 2 at the consuming site") REFUTED.

### (3) Apply form — 3x3 AND 4x4, both POST-demosaic

- 4x4 (0xbfa20): packed `vec4x32f` RGBA, per-pixel `shufps`-broadcast × 4 matrix columns + `addps` accumulate.
- 3x3 (0x300980): `Image<float>` RGB; pre-combines the 3x3 (likely CCM × AWB-diagonal product at 0x3009d8) then per-pixel `mulss/addss` dot products.
- Both consume float RGB(A) → applied **after demosaic**, not on raw Bayer.

### Static boundary (real finding)
The `setColorCorrection → ImageApplyColorMatrix` edge is `std::function`-mediated; the `__func` vtable pointers are installed via chained-fixup/rebase relocations. Byte-search across the full file finds **0 literal pointer refs** to the typeinfo objects → static analysis cannot cross this dispatch. Committed evidence has not crossed it either.

### Future mid-render probe targets
- Variant/mode + gain: bp `0xfc2f0`, read `r8d` (byte mode from 0x161c) and `xmm0` (gain from 0x1618).
- Actual matrix bytes: bp `0xbfa20` read `0x8(%rdi)` (4×16B) / bp `0x300980` read `%rdx` (3x3 source).

## Verifier note(s)
- **0xbfa20**: Prologue confirmed at 0xbfa20 (push rbp/mov rsp). Matrix pointer loaded via 0xbfa47 movq 0x8(%rdi),%rcx; 4x movups at 0xbfa4b/4e/52/56 load rows 0-3 from (%rcx)+0/10/20/30. Pixel loop at 0xbfad0 confirmed: movaps (%rcx),%xmm4; shufps $0x00 broadcast ch0 -> mulps col0; shufps $0x55 broadcast ch1 -> mulps col1; shufps $0xaa broadcast ch2 -> mulps col2; shufps $0xff broadcast ch3 -> mulps col3; three addps accumulate; movaps %xmm4,(%rdx) store at 0xbfb01. Vtable at 0x652968 holds 5 function slots: [0xbfa00, 0xbfa10, 0xbfa20, 0xbfb20, 0xbfb40]. 0xbfa00 is the non-deleting destructor (push/pop/ret, no-op), NOT a clone; actual clone is at 0xbf9a0 (operator new + vptr install + data copy). 0xbfa10 is the deleting destructor (pop/jmp operator delete). 0xbfa20=op() and 0xbfb20=target_type positions are correct. The claim's vtable entry count (3) omits bfa10 and bfb40, and mislabels bfa00 as 'clone'.
- **0x300980**: 0x300980 is at offset +1040 inside ___lldb_unnamed_symbol_300570 (function start 0x300570=op()). Function identity confirmed: RTTI name at 0x5f31c0 = ZN2lt12_GLOBAL__N_121ImageApplyColorMatrixEPNS_5ImageIfEE...Mat3x3...$_2; target_type stub at 0x300c00 correctly loads leaq rip+0x2f25b5 -> 0x5f31c0. The description of 0x3009d8-0x300a54 as 'matrix-by-matrix product producing 3x3 into stack' is wrong: 0x3009a0-0x3009d4 transposes 4 INPUT PIXELS from AoS to SoA using unpcklps/unpckhps/unpcklpd/unpckhpd (4-pixel vectorized path), then 0x3009d8-0x300a54 applies the 3 matrix rows to those 4 transposed pixels producing 3 output rows (one store each at 0x3009fc/0x300a28/0x300a54). No matrix-by-matrix pre-multiplication found. Scalar remainder loop confirmed at 0x300ab4: mulss %xmm3,%xmm2 / mulss %xmm4,%xmm1 / addss / mulss / addss / movss -> (%r10,%rdx,4). Vtable entry 0x300570 found at file VA 0x65a9a8.
