# Lane A1 — Observations (STATIC)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
sha256 `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`. File offset == VA.
Status: NEEDS_CODEX_VALIDATION. All disasm OBSERVED-from-bytes unless marked INFERRED.

## 0. Anchor (OBSERVED) — log: runs/.../ (regenerate per commands.txt step 1)
```
00000000003ecfe4	mulps	%xmm0, %xmm2
00000000003ecfe7	maxps	%xmm1, %xmm2
00000000003ecfea	sqrtps	%xmm2, %xmm2
```
anchorPassed = true.

## 1. Node producer 0x23faf0 — what it writes into the dst node (base = r12 = arg rdi)
Log: `runs/laneA1_post_node_consumers/func_23faf0.log` (0x23faf0 .. 0x2404c9).

Function copies the source node (rbx = arg rdx) into the dst node (r12 = arg rdi), then runs
a 3x3-ish matrix transform on offsets 0x30..0x48 (the `mulss`/`insertps`/`mulps`/`addps`
chain at 0x23fdb5..). OBSERVED dst-node (r12) field writes intersecting +0x28..+0xa0:
```
000000000023fb40	movl	%eax, 0x28(%r12)
000000000023fb48	movl	%eax, 0x2c(%r12)
000000000023fb50	movl	%eax, 0x50(%r12)
000000000023fb5d	movups	%xmm1, 0x40(%r12)
000000000023fb63	movups	%xmm0, 0x30(%r12)
000000000023fb6d	movups	%xmm0, 0x54(%r12)
000000000023fb82	movups	%xmm0, 0x68(%r12)      ## zero-init of a std::vector triple at +0x68/+0x70/+0x78
000000000023fbc3	movq	%r13, 0x70(%r12)
000000000023fbc8	movq	%r13, 0x68(%r12)
000000000023fbd2	movq	%rax, 0x78(%r12)
000000000023fc3a	movl	%eax, 0xa0(%r12)
000000000023fc50	movups	%xmm1, 0x90(%r12)
000000000023fc59	movups	%xmm0, 0x80(%r12)
00000000002400d3	movl	%eax, 0x28(%r12)      ## second store batch after transform math
00000000002400de	movl	%eax, 0x2c(%r12)
0000000000240109	movups	%xmm0, 0x54(%r12)
0000000000240159	movq	%rax, 0x68(%r12)
000000000024016a	movq	%rax, 0x78(%r12)
```
INFERRED node layout from these writes:
- `+0x00..+0x2c` : scalar/int header block (copied verbatim from src)
- `+0x30..+0x48` : float transform/matrix region (REWRITTEN by the transform math)
- `+0x50`        : int
- `+0x54..+0x63` : float quad (copied)
- `+0x68/+0x70/+0x78` : std::vector<u32> (begin/end/cap) — heap, memcpy'd from src (`callq _memcpy` 0x23fbf4)
- `+0x80..+0x9c` : second float quad block
- `+0xa0`        : int
Note `r15 = r12 + 0x80` (alias set via `subq $-0x80,%r15` at 0x23fd59), so writes to
`r15+0x00..+0x20` (e.g. `0x240181 movl %eax,0x20(%r15)`) == node `+0x80..+0xa0`.

## 2. WHERE the produced node lands in the caller 0x23c5f0 (OBSERVED)
Log: `runs/laneA1_post_node_consumers/func_23c5f0.log`. Two producer call sites:

Site 1 — `0x23c6da  callq 0x23faf0`, with dst node arg:
```
000000000023c6c9	leaq	-0x1f8(%rbp), %rdi     ## dst node = stack slot rbp-0x1f8
000000000023c6d0	leaq	-0x2a0(%rbp), %rdx     ## src node
000000000023c6d7	movq	%rbx, %rsi
000000000023c6da	callq	0x23faf0
```
Site 2 — `0x23cbbc  callq 0x23faf0`, dst node = stack slot rbp-0x378:
```
000000000023cbaf	leaq	-0x378(%rbp), %rdi
000000000023cbb6	movq	%rbx, %rsi
000000000023cbb9	movq	%r15, %rdx
000000000023cbbc	callq	0x23faf0
```
So node1 base = `-0x1f8(%rbp)` (== node+0x00). The orientation-doc "site 0x23d025" is the
vector-free cleanup that follows the SECOND node's `0xa0(%r13)` write (`0x23d01e movl %ecx,0xa0(%r13)`),
not a producer call — captured for completeness but it is a destructor pattern (`testq %rdi; __ZdlPv`).

## 3. CANDIDATE downstream consumer of node1 fields +0x28..+0x50
Log: `runs/laneA1_post_node_consumers/node1_consumer_block.log` (0x23c855..0x23c98a).

Stack-slot -> node1 offset map (base -0x1f8 == node1+0x00), computed arithmetically (address math only):
```
-0x1d8 -> +0x20    -0x1d4 -> +0x24    -0x1cc -> +0x2c    -0x1c8 -> +0x30
-0x1c4 -> +0x34    -0x1c0 -> +0x38    -0x1bc -> +0x3c    -0x1b8 -> +0x40
-0x1b4 -> +0x44    -0x1b0 -> +0x48    -0x1ac -> +0x4c    -0x1a8 -> +0x50
```
OBSERVED reads of those slots, widened float->double via `cvtps2pd`/`cvtss2sd`, then stored
into a fresh `0xa8`-byte record (base r14) at +0x28..+0xa0:
```
000000000023c917	cvtps2pd	-0x1f8(%rbp), %xmm1    ## node1 +0x00/+0x08
000000000023c91e	cvtps2pd	-0x1f0(%rbp), %xmm2
000000000023c925	cvtps2pd	-0x1e8(%rbp), %xmm3    ## node1 +0x10..
000000000023c92c	cvtps2pd	-0x1e0(%rbp), %xmm4
000000000023c933	movss	-0x1d8(%rbp), %xmm5    ## node1 +0x20
000000000023c93b	movss	-0x1cc(%rbp), %xmm6    ## node1 +0x2c
000000000023c947	cvtps2pd	-0x1d4(%rbp), %xmm7    ## node1 +0x24/+0x28
000000000023c952	movups	%xmm1, 0x28(%r14)
000000000023c957	movups	%xmm2, 0x38(%r14)
000000000023c95c	movups	%xmm3, 0x48(%r14)
000000000023c961	movupd	%xmm4, 0x58(%r14)
000000000023c967	movsd	%xmm5, 0x68(%r14)
000000000023c96d	movups	%xmm0, 0x70(%r14)
000000000023c972	movq	%rax, 0x80(%r14)
000000000023c979	movups	%xmm7, 0x88(%r14)
000000000023c981	movsd	%xmm6, 0x98(%r14)
000000000023c98a	movl	$0x0, 0xa0(%r14)
```
Classification (bounded): float->double widening copy of node1's transform/header fields
(+0x20..+0x50) into a double-precision record at r14+0x28..+0xa0. The earlier block at
0x23c85b also reads node1 +0x30..+0x50 (`-0x1c8..-0x1a8`) and `cvtps2pd`-widens into a
`-0x110`/`-0x130` matrix that is then passed to `0x1dc5a0`.

r14 record is allocated & default-initialized just upstream (0x23c7ce..0x23c829):
diagonal doubles `0x3ff0000000000000` (=1.0) at +0x28/+0x48/+0x68 (identity transform),
then `movq %r14,(%r15)` (0x23c829) links it and `callq 0xdb240` (0x23c84f) inserts it.

## 4. Callees receiving the record pointer — bounded classification

### 0xdb240 (OBSERVED red-black-tree insert-fixup) — log: callee_db240.log
```
00000000000db240	pushq	%rbp
00000000000db247	sete	0x18(%rsi)         ## color byte at record+0x18
00000000000db260	movq	0x10(%rsi), %rcx   ## parent
00000000000db264	cmpb	$0x0, 0x18(%rcx)   ## color test
00000000000db29f	movb	$0x1, 0x18(%rcx)   ## recolor (rotations on +0x08/+0x10 child/parent ptrs)
```
=> std::map/std::set rebalance. Container insert of the r14 record; does NOT read the
record's +0x28..+0xa0 transform fields. This places the produced node into a TREE.

### 0x1dc5a0 (LEAD) — log: callee_1dc5a0.log
Receives rdi = the `-0x110` double-matrix (0x48 bytes), mallocs a 0x48 copy, feeds 0x1dd3b0
with stride 0x28. Adjacent consumer of node1-derived double matrix, NOT a direct reader of
node1+0x28 raw fields.

## 5. Negative observation (OBSERVED)
Within 0x23c5f0, node1 fields `+0x54..+0xa0` (the second float quad / second std::vector at
+0x68..+0x78 / +0x80..) are NOT read after production — they are only *written* during
production (step 1). The downstream consumer in step 3 reads only +0x20..+0x50.
The +0x68 std::vector heap data is owned but not re-read in this function body.
