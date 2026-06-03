# Lane A2 -- Reducer/Body Search (STATIC) -- Observations

status: NEEDS_CODEX_VALIDATION
libcp.dylib sha256: b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
scope: STATIC ONLY (otool -tV, nm, raw __DATA pointer reads). NO render, NO runtime, NO breakpoints.
weak-language only: OBSERVED / LEAD / CANDIDATE / NEEDS_CODEX_VALIDATION.

---

## O0. Anchor self-check -- anchorPassed = TRUE

VERBATIM (runs/.../full_disasm.txt, function at 0x3eced0):
```
00000000003ecfe4	mulps	%xmm0, %xmm2
00000000003ecfe7	maxps	%xmm1, %xmm2
00000000003ecfea	sqrtps	%xmm2, %xmm2
```
OBSERVED: mulps -> maxps -> sqrtps present at 0x3ecfe4. Anchor confirmed; VAs in this packet are
trustworthy against this exact dylib.

---

## O1. The accumulator 0x369f80 is a per-tile windowed resample loop (IMAGE-EFFECTING)

VERBATIM (full_disasm.txt, inner loop body, function 0x3661b0):
```
0000000000369f80	movss	-0xa0(%rbp,%rsi,4), %xmm0      ; coeff_i  (stack window table)
0000000000369f90	movss	-0xa0(%rbp,%rcx), %xmm1        ; coeff_j
0000000000369f99	mulss	%xmm0, %xmm1                   ; coeff_i * coeff_j
0000000000369f9d	shufps	$0x0, %xmm1, %xmm1            ; broadcast scalar weight
0000000000369fa1	mulps	(%rdi), %xmm1                 ; * source pixels (4-wide, rdi += 0x10)
0000000000369fa4	addps	(%rdx,%rcx,4), %xmm1          ; acc += ...
0000000000369fa8	movaps	%xmm1, (%rdx,%rcx,4)         ; store accumulator
0000000000369fac	addq	$0x4, %rcx
0000000000369fb0	addq	$0x10, %rdi                   ; source stride = 16 bytes (vec4x32f)
0000000000369fb4	cmpq	$0x40, %rcx
0000000000369fb8	jne	0x369f90
0000000000369fbd	addq	$0x100, %rax                  ; outer source row stride = 256 bytes
0000000000369fc6	cmpq	$0x10, %rsi                   ; 16x outer (Hann-16)
0000000000369fca	jne	0x369f80
```
OBSERVED: `%rdi` strides a 16-byte (vec4x32f) source buffer; `%rdx` is a 16x64 float accumulator.
This is `acc += source4 * (coeff_i*coeff_j)`, 16x16 Hann-windowed -- matches the committed-evidence
description of 0x369f80. CLASS = IMAGE-EFFECTING (it reads a strided pixel buffer and writes an
accumulator).
SCOPE-BOUND: this is intra-tile accumulation. It is NOT, by itself, evidence of cross-camera fusion.

## O2. 0x369f80 is reached only via 0x3661b0 <- 0x365960 <- 0x3ec770 <- 0x3ec960 (vtable entry)

VERBATIM direct callers (probe_repro.log [direct-callers]):
```
0x3661b0: ['0x365960']
0x365960: ['0x3ec770']
0x3ec770: ['0x3ec960']
0x3ec960: none (indirect/vtable-only)
0x369f80: none (indirect/vtable-only)   ; (loop head, not a callee)
```
OBSERVED: the chain bottoms out at 0x3ec960, which has NO direct caller -- it is a virtual method
reached through a vtable.

## O3. 0x3ec960's vtable belongs to SourceImageCache's per-tile lambda (RTTI, IMAGE-EFFECTING; per-camera)

VERBATIM: raw __DATA read shows 0x3ec960 sits in the vtable at file-offset 0x65f610:
```
0x65f610: 0x00000000003ec960 <== 0x3ec960   (7th vfunc of this vtable)
```
The class typeinfo name string for this vtable cluster (inline mangled name at 0x608010):
```
ZZN2lt16SourceImageCacheC1ERKNS_4Vec2IiEES4_RKNSt3__110shared_ptrINS_11TileStorageEEE
RKNS6_INS_15RawImageFactoryEEENS_13CapturedImage6CameraEONS_16LensUndistortCRAEE
NK3$_0clERKNS6_INS_4TileINS_8vec4x16fEEEEEEUlRNS_5ImageINS_8vec4x32fEEERKNS_9RectangleIiEEE_
```
Demangled essence:
  lt::SourceImageCache::SourceImageCache(Vec2<int>, Vec2<int>, shared_ptr<TileStorage>,
       shared_ptr<RawImageFactory>, CapturedImage::Camera, LensUndistortCRA&&)
    ::$_0::operator()(Tile<vec4x16f> const&)
      ::'lambda'(Image<vec4x32f>&, Rectangle<int> const&)
OBSERVED: the accumulator chain is the body of a SourceImageCache per-tile callable. Inputs are
ONE CapturedImage::Camera + ONE Tile<vec4x16f>; output is Image<vec4x32f>. It applies LensUndistortCRA.
INFERRED (from RTTI + signature, weak): this is per-camera source-image production / undistort+resample,
NOT a cross-camera N->1 reducer.
SCOPE-BOUND: signature/type inference only; I did NOT runtime-confirm how many cameras feed it.

## O4. 0x3ec960 is a mode dispatch over resample strategies

VERBATIM (full_disasm.txt 0x3ec9dc..0x3eca46):
```
00000000003ec9dc	movl	0x18(%rax), %eax        ; mode enum
00000000003ec9df	leal	-0x2(%rax), %ecx
00000000003ec9e2	cmpl	$0x3, %ecx
00000000003ec9e5	jae	0x3eca1c                ; >=2..? -> 0x3d0650 branch
...
00000000003eca1c	testl	%eax, %eax
00000000003eca1e	je	0x3eca3b               ; mode 0 -> 0x3ec770 (accumulator-caller)
00000000003eca20	cmpl	$0x1, %eax
00000000003eca34	callq	0x3ebb80               ; mode 1
00000000003eca46	callq	0x3ec770               ; mode 0 (the windowed accumulator path)
```
OBSERVED: 0x3ec770 (-> accumulator) is one of several resample strategies selected by an enum at
+0x18 of a config struct. The accumulator path is conditional, not unconditional.

## O5. 0x365960 precomputes a Hann window weight table (IMAGE-EFFECTING setup)

VERBATIM (full_disasm.txt 0x36597f..0x365c66 region):
```
0000000000365a07	addl	$0x3, %eax            ; window half-size from xmm0 scalar
0000000000365a0a	cmpl	$0x41, %eax           ; capped at 65
0000000000365a60	callq	0x556392              ## __Znam   ; alloc 4*N float table
...
0000000000365c66	movups	%xmm0, (%r14,%r12,4)  ; store window weights into table
0000000000365f4b	callq	0x3661b0              ; -> accumulator over source tile
```
Signature of 0x365960 (SysV): rdi,rsi,rdx pointers; rcx & r8 are std::vector<16-byte> whose element
counts MUST be equal (else `jne 0x36608b` aborts at 0x3659d0); r9 ptr; xmm0 float (window size).
OBSERVED: two equal-length vectors of 16-byte descriptors are consumed. CANDIDATE: these could be
parallel per-tile geometry descriptors; their exact role is not statically proven here.

## O6. The normalizer 0x2f78e0 is ImageDenoiseBilateralGeneric<5,true> (IMAGE-EFFECTING; denoise, not fusion)

VERBATIM: raw __DATA read shows 0x2f78e0 is the 7th vfunc in the vtable at file-offset 0x65a598:
```
0x65a598: 0x00000000002f78e0 <== 0x2f78e0
```
typeinfo name string (at 0x5f2630, reached from vtable typeinfo slot 0x65a5b0):
```
NSt3__110__function6__funcIZN2lt8Internal12_GLOBAL__N_1
28ImageDenoiseBilateralGenericILi5ELb1EEEvRNS2_5ImageINS2_8vec4x32fEEERKS8_SB_
RKS7_RKNS2_9RectangleIiEEEUlSH_iE_NS_9allocatorISI_EEFvSH_iEEE
```
Demangled essence:
  std::__function::__func< lt::Internal::(anon)::ImageDenoiseBilateralGeneric<5,true>(
        Image<vec4x32f>&, ImageRef const&, ImageRef const&, ..., Rectangle<int> const&) ... >
OBSERVED: 0x2f78e0 is a bilateral-denoise std::function body operating on Image<vec4x32f>.
INFERRED (weak): the "Sigma(w*v)/Sigma(w)" reciprocal-normalize at 0x2f8584-0x2f85a5 is the
BILATERAL weighted-average normalization (per-pixel edge-aware denoise), which is consistent with a
denoise role and is NOT, on its face, a multi-camera src1/src2 fusion normalizer.
SCOPE-BOUND: I did NOT trace whether SourceImageCache output feeds this denoise; only the RTTI/type
of 0x2f78e0's owning std::function is established here.

## O7. The 0x23faf0 helper is a record/metadata clone (NOT a pixel-buffer op)

VERBATIM (full_disasm.txt 0x23faf0 body):
```
000000000023fb23	movups	(%rbx), %xmm0          ; copy POD header bytes
000000000023fb2a	movups	%xmm1, 0x10(%r12)
000000000023fb55	movups	0x30(%rbx), %xmm0
000000000023fb91	movq	0x70(%rbx), %r15
000000000023fb95	subq	0x68(%rbx), %r15       ; vector size = (end-begin)
000000000023fb9c	sarq	$0x2, %r14             ; element stride = 4 bytes
000000000023fbb6	callq	0x556398              ## __Znwm   ; alloc child vector
000000000023fbf4	callq	0x556032              ## memcpy    ; copy child vector
```
OBSERVED: 0x23faf0 deep-copies a fixed POD header (coords/geometry at offsets 0..0x59) plus one
std::vector of 4-byte elements (child indices/coords). No large strided pixel buffer is touched.
CLASS = METADATA-ONLY (copy constructor / clone of a tree-node-shaped record).

## O8. No static path from 0x23faf0 records to image kernels (bounded; DIRECT-CALL only)

VERBATIM (probe_repro.log):
```
[record-clone] distinct 0x23faf0 host functions: 23
[record-clone] hosts INTERSECT img-reaching set: EMPTY
[record-clone] img-reaching fns that call 0x23faf0: EMPTY
[reachability] functions transitively reaching an img kernel (DIRECT-CALL only): ['0x365960','0x3ec770','0x3ec960']
```
OBSERVED: of the 23 functions that call 0x23faf0, NONE can reach any of the 6 named image kernels
through any depth of DIRECT calls; and NONE of the (only 3) functions that reach an image kernel
call 0x23faf0.
HARD CAVEAT: this is DIRECT-CALL reachability only. 0x2f78e0, 0x3ec960, and 0x369f80 are all reached
via vtable / std::function indirection (O2, O3, O6) -- which a static call graph CANNOT cross.
Therefore "no static path found" bounds the DIRECT-call surface, and does NOT exclude an indirect
(virtual / std::function / callback-registration) link between the State/tree-node side and the
image kernels. This gap is exactly where Codex runtime validation is required.
