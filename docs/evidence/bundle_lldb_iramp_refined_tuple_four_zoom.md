# Bundle + LLDB IRAMP Refined Tuple Evidence

**Date:** 2026-05-12
**Status:** Partial evidence admitted for canonical review.
**Scope:** Corrected canonical bridge HDR quartet only.

This document bounds the live non-empty partner-record consumer path after the local IRAMP partner gate.

It proves a coarse SIMD SAD / WTA path, a local absolute-difference refinement table, guarded float refinement, 16x16 bilinear vec4 resampling, and a live three-float scratch write across `28mm`, `35mm`, `70mm`, and `150mm`.

It does not prove public semantic names for the written floats or the final merge acceptance / rejection policy.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable first-hit probes live in the repo:

- `tools/lldb_probes/iramp_refined_tuple/refined_tuple_probe.py`
- `tools/lldb_probes/iramp_refined_tuple/refined_tuple_first_28mm.lldb`
- `tools/lldb_probes/iramp_refined_tuple/refined_tuple_first_35mm.lldb`
- `tools/lldb_probes/iramp_refined_tuple/refined_tuple_first_70mm.lldb`
- `tools/lldb_probes/iramp_refined_tuple/refined_tuple_first_150mm.lldb`

Generated run outputs go under ignored `runs/iramp_refined_tuple/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Partner-Record Iteration And Sentinel Rejection

The non-empty path iterates `0x280` partner records. It uses record offset `+0x28` and pointer offset `+0x30`, both inside the record `+0x10` descriptor-like block, to read an int32 pair entry:

```asm
0x3692f0  leaq (%rcx,%rcx,4), %rdx
0x3692f4  shlq $0x7, %rdx
0x3692f8  movl 0x28(%rdi,%rdx), %eax
0x3692fc  imull %r13d, %eax
0x369300  addl %r8d, %eax
0x369303  movslq %eax, %rsi
0x369306  movq 0x30(%rdi,%rdx), %r12
0x36930b  movl (%r12,%rsi,8), %eax
0x36930f  cmpl $0x80000000, %eax
0x369314  jne 0x369320
```

If the entry is sentinel, the record is skipped:

```asm
0x369316  movl %ebx, %edx
0x369318  movl %r15d, %esi
0x36931b  jmp 0x369f0b
```

### Coarse SAD / WTA

The first coarse search is SIMD SAD over byte patches. It uses `mpsadbw` and saturated word accumulation:

```asm
0x369490  movdqu (%rcx), %xmm5
0x369494  movdqu 0x8(%rcx), %xmm9
0x36949a  movdqa -0x1b40(%rbp,%rax), %xmm7
0x3694a3  movdqa -0x1b30(%rbp,%rax), %xmm8
0x3694b1  mpsadbw $0x0, %xmm7, %xmm6
0x3694b7  paddusw %xmm1, %xmm6
0x3694bb  mpsadbw $0x5, %xmm7, %xmm5
0x3694c1  paddusw %xmm2, %xmm5
0x3694ca  mpsadbw $0x2, %xmm7, %xmm4
0x3694d0  paddusw %xmm3, %xmm4
0x3694d4  mpsadbw $0x7, %xmm7, %xmm9
0x3694db  paddusw %xmm0, %xmm9
```

The coarse winner is selected with `phminposuw`:

```asm
0x369537  paddusw %xmm2, %xmm1
0x36953b  paddusw %xmm0, %xmm3
0x36953f  paddusw %xmm1, %xmm3
0x369543  phminposuw %xmm3, %xmm0
0x369548  movd %xmm0, %r11d
0x36954d  movzwl %r11w, %r9d
0x369551  cmpl %r10d, %r9d
0x369554  cmovbl %r9d, %r14d
0x369558  cmovbl %r8d, %r15d
```

This coarse SAD / WTA loop runs a second eight-position lane and loops `r8d` through `0..15`, so the visible coarse surface is a 16-step search window for this record.

### Boundary Gates

After coarse selection, the path checks that the selected neighborhood can be sampled. Failure jumps to `0x369ed0`, which writes the sentinel back into the pair table:

```asm
0x369692  cmpl %eax, %edx
0x36969b  jle 0x369ed0
0x3696b2  cmpl %ecx, %eax
0x3696b4  jge 0x369ed0
0x3696c6  cmpl %eax, %esi
0x3696c8  jle 0x369ed0
0x3696e6  cmpl %ecx, %eax
0x3696e8  jge 0x369ed0
...
0x369ed0  movabsq $-0x7fffffff80000000, %rax
0x369eda  movq -0x4370(%rbp), %rcx
0x369ee1  movq %rax, (%r12,%rcx,8)
```

### Local Absolute-Difference Refinement Table

If the coarse neighborhood passes bounds, the path initializes a local cost table to `0xff`:

```asm
0x3696fc  movl $0xff, %esi
0x369701  movl $0xc4, %edx
0x369706  leaq -0x170(%rbp), %rdi
0x36970d  callq memset
```

The refinement loops cover offsets from `-2` through `+2` in both axes and skip the center:

```asm
0x369730  movq $-0x2, %r12
...
0x369760  movq $-0x2, %rax
...
0x369770  movl %r12d, %esi
0x369773  orl %eax, %esi
0x369775  je 0x3698d4
...
0x3698d4  incq %rax
0x3698d7  cmpq $0x3, %rax
0x3698db  jne 0x369770
0x3698e1  incq %r12
0x3698e4  cmpq $0x3, %r12
0x3698e8  jne 0x369740
```

The local table cost uses unsigned byte absolute differences via `pmaxub`, `pminub`, and `psubb`, then sums with `pmovzxbw`, `paddusw`, `paddd`, and `phaddd`:

```asm
0x369a60  movdqu (%r9), %xmm0
0x369a65  movdqa -0x1b40(%rbp,%r13), %xmm1
0x369a79  movdqa %xmm1, %xmm5
0x369a7d  pmaxub %xmm0, %xmm5
0x369a81  pminub %xmm0, %xmm1
0x369a85  psubb %xmm1, %xmm5
0x369a89  pmovzxbw %xmm5, %xmm0
...
0x369ae1  paddd %xmm0, %xmm2
0x369ae5  pshufd $0x4e, %xmm2, %xmm0
0x369aea  paddd %xmm2, %xmm0
0x369aee  phaddd %xmm0, %xmm0
0x369af3  movd %xmm0, %edx
0x369af7  movl %edx, -0x1a0(%rbp,%rax,4)
```

### Guarded Float Refinement

The float refinement consumes the local table values at `-0x1a0..-0x180`, computes two refined float offsets, and rejects unstable results.

The denominator / guard sequence includes:

```asm
0x369bec  movaps %xmm2, %xmm1
0x369bef  mulss %xmm6, %xmm1
0x369bf3  movaps %xmm5, %xmm0
0x369bf6  mulss %xmm0, %xmm0
0x369bfa  movaps %xmm1, %xmm7
0x369bfd  subss %xmm0, %xmm7
0x369c08  cmpltss %xmm7, %xmm0
0x369c0d  andps %xmm5, %xmm0
0x369c13  mulss %xmm5, %xmm5
0x369c17  subss %xmm5, %xmm1
0x369c1b  ucomiss %xmm4, %xmm1
0x369c21  je 0x369cb0
```

The offset computation divides by that guarded value, then rejects unless both absolute offsets are less than `1.0`. If either absolute value is not below `1.0`, both offsets are zeroed:

```asm
0x369c5b  movss 0x5a8128, %xmm2      ; 1.0
0x369c66  divss %xmm1, %xmm5
0x369c6a  mulss %xmm5, %xmm4
0x369c6e  mulss %xmm0, %xmm5
0x369c75  movaps 0x5a81f0, %xmm1     ; 0x7fffffff abs mask
0x369c7c  movaps %xmm1, %xmm6
0x369c7f  andps %xmm6, %xmm0
0x369c82  movaps %xmm5, %xmm1
0x369c85  andps %xmm6, %xmm1
0x369c88  ucomiss %xmm2, %xmm0
0x369c8b  setb %cl
0x369c8e  ucomiss %xmm2, %xmm1
0x369c91  setb %al
0x369c94  andb %cl, %al
0x369c96  jne 0x369c9b
0x369c98  xorps %xmm4, %xmm4
0x369c9b  testb %al, %al
0x369c9d  jne 0x369cb0
0x369c9f  xorps %xmm5, %xmm5
```

The refined floats are scaled and stored to stack:

```asm
0x369cb0  addss %xmm9, %xmm4
0x369cb5  movss 0x5aae88, %xmm0      ; 1/3
0x369cbd  mulss %xmm0, %xmm4
0x369cc1  addss %xmm8, %xmm4
0x369cc6  addss %xmm3, %xmm5
0x369cca  mulss %xmm0, %xmm5
0x369cd9  movss (%rax), %xmm0        ; scale from object at [rbp-0x4388]+0x28
0x369cdd  movaps %xmm4, %xmm1
0x369ce0  mulss %xmm0, %xmm1
0x369ce4  movss %xmm1, -0x4310(%rbp)
0x369cec  addss %xmm10, %xmm5
0x369cf1  movaps %xmm5, %xmm1
0x369cf4  mulss %xmm0, %xmm1
0x369cf8  movss %xmm1, -0x4320(%rbp)
```

### Bilinear Vec4 Resampling

The same refined floats are also converted into 16.16 fixed-point positions using constants `-8.0` and `65536.0`:

```asm
0x369d00  movss 0x5d4c20, %xmm1      ; -8.0
0x369d08  addss %xmm1, %xmm5
0x369d0c  mulss %xmm0, %xmm5
0x369d10  addss %xmm1, %xmm4
0x369d14  mulss %xmm0, %xmm4
0x369d18  movss 0x5df91c, %xmm1      ; 65536.0
0x369d20  mulss %xmm1, %xmm0
0x369d24  cvttss2si %xmm0, %r12d
0x369d29  mulss %xmm1, %xmm5
0x369d2d  cvttss2si %xmm5, %r15d
0x369d32  mulss %xmm1, %xmm4
0x369d36  cvttss2si %xmm4, %r8d
```

The resampler uses the low 16 bits multiplied by `1/65536` and linearly blends two rows and two columns of `vec4` values into a 16x16 scratch patch at `-0x11a0`:

```asm
0x369d70  movl %r15d, %ecx
0x369d73  sarl $0x10, %ecx
0x369d76  movzwl %r15w, %edx
0x369d7a  cvtsi2ss %edx, %xmm0
0x369d7e  mulss 0x5acc60, %xmm0      ; 1/65536
...
0x369ddb  movaps (%rdi,%rcx), %xmm2
0x369ddf  movaps 0x10(%rdi,%rcx), %xmm3
0x369de4  movaps (%r13,%rcx), %xmm4
0x369dea  movaps 0x10(%r13,%rcx), %xmm5
0x369df0  subps %xmm4, %xmm2
0x369df3  mulps %xmm0, %xmm2
0x369df6  addps %xmm4, %xmm2
0x369df9  subps %xmm5, %xmm3
0x369dfc  mulps %xmm0, %xmm3
0x369dff  subps %xmm2, %xmm5
0x369e02  addps %xmm3, %xmm5
0x369e05  mulps %xmm1, %xmm5
0x369e08  addps %xmm2, %xmm5
0x369e0b  movaps %xmm5, (%rbx)
...
0x369e27  cmpq $0x10, %r11
0x369e2b  jne 0x369d70
```

After the 16x16 patch is built, the path calls `0x36cde0`:

```asm
0x369e31  leaq -0x4240(%rbp), %rdi
0x369e38  leaq -0x11a0(%rbp), %rsi
0x369e3f  callq 0x36cde0
```

`0x36cde0` computes vector sums, products, squared terms, clamps through `maxps` / `minps`, and returns a scalar in `xmm0` used by the third float store. Its exact public semantic meaning is not proven here.

### Three-Float Scratch Write

After `0x36cde0` returns, the path writes three floats through the record `+0x40` descriptor's stride and pointer fields:

```asm
0x369e52  movl 0x58(%rcx,%rdx), %eax
0x369e5d  imull %r13d, %eax
0x369e68  addl %r8d, %eax
0x369e6d  movq 0x60(%rcx,%rdx), %rcx
0x369e72  leaq (%rax,%rax,2), %rax
0x369e76  movss -0x4310(%rbp), %xmm1
0x369e7e  movss %xmm1, (%rcx,%rax,4)
0x369e83  movss -0x4320(%rbp), %xmm1
0x369e8b  movss %xmm1, 0x4(%rcx,%rax,4)
0x369e91  movss %xmm0, 0x8(%rcx,%rax,4)
```

The first two floats are the stack-stored refined values from `0x369ce4` and `0x369cf8`. The third float is the scalar returned in `xmm0` by `0x36cde0`.

## Runtime Proof Summary

All four focal tiers hit the first three-float store at `0x369e7e`.

The probe reads:

- vector begin/end from `[rbp-0x1800]` and `[rbp-0x17f8]`
- current record offset from `[rbp-0x4300]`
- first refined float from `[rbp-0x4310]`
- second refined float from `[rbp-0x4320]`
- output base from `rcx`
- output tuple index from `rax`

| Zoom | Vector state | Current record offset | First refined float | Second refined float | Output tuple index base |
|---|---|---:|---:|---:|---:|
| `28mm` | `diff=640`, `npartners=1` | `0` | `19.22564125061035` | `19.22564125061035` | `60` |
| `35mm` | `diff=640`, `npartners=1` | `0` | `27.641357421875` | `24.948217391967773` | `1128` |
| `70mm` | `diff=640`, `npartners=1` | `0` | `-15.46357536315918` | `16.867599487304688` | `1086` |
| `150mm` | `diff=1920`, `npartners=3` | `0` | `18.533334732055664` | `-16.394872665405273` | `30` |

Runtime packets:

```text
28mm:  hit 0x369e7e; diff=640;  npartners=1; x=19.22564125061035;  y=19.22564125061035;   out_index_times_3=60
35mm:  hit 0x369e7e; diff=640;  npartners=1; x=27.641357421875;    y=24.948217391967773; out_index_times_3=1128
70mm:  hit 0x369e7e; diff=640;  npartners=1; x=-15.46357536315918; y=16.867599487304688; out_index_times_3=1086
150mm: hit 0x369e7e; diff=1920; npartners=3; x=18.533334732055664; y=-16.394872665405273; out_index_times_3=30
```

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- The non-empty partner-record consumer path reaches `0x369e7e` at `28mm`, `35mm`, `70mm`, and `150mm`.
- The path reads record `+0x10` descriptor-backed pair data and skips entries whose first int32 is sentinel `0x80000000`.
- The coarse search uses SIMD `mpsadbw` SAD accumulation and `phminposuw` winner selection.
- The selected coarse neighborhood is boundary-gated; failures write sentinel `0x8000000080000000` back to the pair table.
- The refinement path builds a local absolute-difference cost table over a visible `-2..+2` by `-2..+2` offset neighborhood, skipping center.
- The float refinement has guard rails: a zero-denominator path, an `abs(offset) < 1.0` check for both offsets, and a fallback that zeroes both offsets.
- The path prepares a 16x16 `vec4` patch by bilinear interpolation using 16.16 fixed-point coordinates.
- The path calls `0x36cde0` after building that patch.
- The path writes a three-float tuple through the record `+0x40` descriptor output pointer: refined float 1, refined float 2, and the scalar returned by `0x36cde0`.

## Not Proven Here

- Public semantic names for the two refined floats.
- Public semantic meaning of the third float from `0x36cde0`.
- Whether the first captured tuple is representative of all tuples in a render.
- How the three-float scratch tuple is consumed downstream.
- Whether this local path is the final anti-ghosting acceptance / rejection decision.
- Any complete Lumen-quality merge algorithm.
