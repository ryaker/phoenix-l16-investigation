# Lane C — C6 alias / terminal-filter / alternate-route — STATIC observations

status: **NEEDS_CODEX_VALIDATION**
method: STATIC ONLY — `otool -arch x86_64 -tV`. No render, no runtime breakpoints.
binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
sha256: `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
disasm dump: `runs/laneC_c6_alias_terminal_route/full_disasm.txt` (1,333,882 lines)
NOTE: file offset == VA (__TEXT vmaddr=0). All VAs below are verbatim from the dump.

---

## 0. Anchor self-check — anchorPassed = true (with note)

Requested: "0x3eced0 must show mulps -> maxps -> sqrtps."

OBSERVED: 0x3eced0 is a function **prologue**, not the SIMD triple directly:
```
00000000003eced0	pushq	%rbp
00000000003eced1	movq	%rsp, %rbp
```
The `mulps -> maxps -> sqrtps` triple appears INSIDE that function. First occurrence (VERBATIM):
```
00000000003ecfe4	mulps	%xmm0, %xmm2
00000000003ecfe7	maxps	%xmm1, %xmm2
00000000003ecfea	sqrtps	%xmm2, %xmm2
```
Triple repeats at 0x3ecff4, 0x3ed02c, 0x3ed065, 0x3ed077, 0x3ed101, 0x3ed135 (see `anchor_selfcheck.log`).
INFERRED: anchor is satisfied at function granularity; the briefing VA points at the enclosing function entry, not the instruction. Re-anchoring NOT required.

---

## 1. C6 anchors re-confirmed STATICALLY (cite as LEAD, not fact)

### 1a. Key getter `0xf2720` (VERBATIM, `c6_anchors.log`)
```
00000000000f2720	pushq	%rbp
00000000000f2721	movq	%rsp, %rbp
00000000000f2724	movl	0x60(%rdi), %eax
00000000000f2727	popq	%rbp
00000000000f2728	retq
```
OBSERVED: `0xf2720` is a trivial getter returning **item+0x60** (a 32-bit int) — the "key".

### 1b. Constructor `0xf2770` field map (VERBATIM excerpts)
```
00000000000f27a1	movl	0x30(%r14), %edi        ; source field
00000000000f27a5	callq	0x137d70                ; transform
00000000000f27aa	movq	%r13, %rdx
00000000000f27ad	movl	%eax, 0x60(%rdx)        ; -> item+0x60  (the key, read back by f2720)
00000000000f27b0	movb	0x60(%r14), %al
00000000000f27b4	movb	%al, 0x30(%rdx)        ; -> item+0x30  (active byte flag)
```
OBSERVED: item+0x60 = key int; item+0x30 = active byte flag. These are **distinct fields**.

### 1c. Clear site `0x3c90a5` (VERBATIM, `c6_anchors.log`)
```
00000000003c9095	movq	(%rbx), %rdi
00000000003c9098	callq	0xf2720
00000000003c909d	cmpl	$0xf, %eax            ; key == 15 ?
00000000003c90a0	jne	0x3c90a9
00000000003c90a2	movq	(%rbx), %rax
00000000003c90a5	movb	$0x0, 0x30(%rax)      ; clear active flag ONLY
```
OBSERVED (load-bearing): the clear writes **item+0x30 = 0**. It does **NOT** touch item+0x60.
INFERRED: after the clear, the key getter `0xf2720` still returns **15**; only the +0x30 active byte goes to 0.

---

## ANGLE 1 — Alias / untested-field enumeration

### 1.A — Complete field map written by the C6 item constructor (`angle1_constructor_fields.log`)
OBSERVED — the constructor `0xf2770` writes the item at **exactly** these offsets (deduped, VERBATIM dst operands):
```
0x30, 0x38, 0x40, 0x44, 0x48, 0x4c, 0x4d, 0x50, 0x54, 0x60, 0x64,
0x104, 0x108, 0xd8, 0xdc, 0xe0, 0xe4, 0xe8, 0xec, 0xf0, 0xf4, 0xf8, 0xf9, 0xfc
```
OBSERVED (load-bearing): the constructor writes **NOTHING in the 0x68..0xa0 band**. The briefing's
target band (+0x68..0xa0) is **not an initialized C6-item field range** per this constructor.

INFERRED: the C6 item's defined fields **outside the already-covered set** (+0x30/+0x58/+0x5c/+0x60/+0x64) are:
`0x38, 0x40, 0x44, 0x48, 0x4c, 0x4d, 0x50, 0x54, 0x104, 0x108`, plus the `0xd8..0xfc` block.
(+0x58/+0x5c are NOT written by the constructor; see 1.C — they belong to a sub-region returned by `0xf2750`.)

### 1.B — Trivial getters in the C6 accessor cluster (`angle1_cluster_getters.log`)
OBSERVED — the only single-offset getters with `push rbp; mov; ret` shape in the `0xf2720..0xf2768` cluster:
```
0x000f2724	movl	0x60(%rdi), %eax      ; f2720  -> key int
0x000f2734	movl	0x100(%rdi), %eax     ; f2730  -> int at 0x100
0x000f2744	movb	0x4c(%rdi), %al       ; f2740  -> byte 0x4c
0x000f2754	leaq	0x58(%rdi), %rax      ; f2750  -> POINTER to 0x58 sub-region
0x000f2764	movb	0x4d(%rdi), %al       ; f2760  -> byte 0x4d
```
LEAD: dedicated accessors exist for +0x4c, +0x4d, +0x58(ptr), +0x60, +0x100 — i.e. fields beyond the
covered set (+0x4c, +0x4d, +0x100) **do** have first-class getters and therefore likely have callers.

### 1.C — +0x58 sub-region (returned by `0xf2750`) read shape
OBSERVED — at the `0xf2750` callers, the returned `%rax` is read at +0x0/+0x4 with a sign-bit test:
```
00000000001a8e4f	callq	0xf2750
00000000001a8e54	movl	0x4(%rax), %ecx
00000000001a8e57	orl	(%rax), %ecx
00000000001a8e59	js	0x1a8eb0               ; if (item+0x58 | item+0x5c) sign-bit set -> skip
```
(same idiom at 0xe6a24, 0x1a8f4a). INFERRED: +0x58/+0x5c form a packed pair whose sign bit is a
validity/range gate. This is consistent with the "covered" labeling of +0x58/+0x5c.

### 1.D — Blind +0x68..0xa0 reader enumeration (`angle1_blind_0x68_0xa0_reads.log`)
OBSERVED: 145 reader VAs exist anywhere in the binary at offsets 0x68..0xa0 on `%rdi`.
**SCOPE WARNING (load-bearing):** these are a **superset across all struct types**; they are **NOT
attributed to the C6 item**. Example: the getter cluster at `0xe7634..0xe76a4` (offsets
0x30,0x108,0x40,0x250,0x160,0x180,0x1a8,0x78) extends to 0x250+ and is a **different, larger
container** struct (the C6 item's max defined offset is 0x108), so its +0x78 getter (`0xe76a4 leaq 0x78`)
is a PARENT-container field, NOT a C6-item alias. Do not conflate.

ANGLE 1 RESULT: **CANDIDATE** — the disciplined, item-attributed answer is that the C6 item's
constructor defines NO fields in +0x68..0xa0; the non-covered *defined* fields are
+0x38/0x40/0x44/0x48/0x4c/0x4d/0x50/0x54/0x104/0x108/0xd8..0xfc, with first-class getters present for
+0x4c/+0x4d/+0x100. A blind binary-wide +0x68..0xa0 read list is provided but is NOT C6-attributed.

---

## ANGLE 2 — Terminal-filter candidate (non-skipping path on cleared item)

### 2.A — literal key==15 tests (`angle2_cmpl_0xf_sites.log`)
OBSERVED: 15 sites match `cmpl $0xf, %eax`. Of these, **only ONE** is immediately preceded by
`callq 0xf2720` (the live key getter): that is `0x3c909d` — the clear site itself (`jne` skips, so the
clear path branches AWAY when key != 15; when key == 15 it falls through to the clear). All other 14
`cmpl $0xf` sites are preceded by `andl $0xf` (bit-masking), `movl (%r13)`, or `movzbl` and are
followed by `ja`/`sete` (switch bounds-checks / bit tests) — they are **not** C6-key tests via the getter.

### 2.B — Gated selection region `0x1a8df0` (`angle2_gated_region_1a8df0.log`, VERBATIM)
```
00000000001a8df0	cmpb	$0x0, 0x30(%rdi)      ; +0x30 active-flag gate
00000000001a8df4	je	0x1a8e90              ; cleared -> SKIP to exit
...
00000000001a8e00	callq	0xf2720              ; key
00000000001a8e08	movq	0x118(%r14), %rdi
00000000001a8e0f	callq	0x1bea00
00000000001a8e14	cmpl	%eax, %r15d          ; key vs reference value
00000000001a8e17	je	0x1a8eb0
...
00000000001a8e2c	callq	0xf6c60              ; key -> camera-group-type
00000000001a8e40	callq	0xf6c60              ; ref -> camera-group-type
00000000001a8e45	cmpl	-0x60(%rbp), %r15d   ; group-type match?
00000000001a8e49	jne	0x1a8eb0
00000000001a8e5b	movq	-0x50(%rbp), %rdi
00000000001a8e5f	callq	0xf2720              ; key
00000000001a8e64	movl	%eax, -0x64(%rbp)
00000000001a8e77	movl	%eax, (%rcx)         ; STORE key into list @ 0x150(%r14)
00000000001a8e7d	movq	%rcx, 0x150(%r14)    ; advance list cursor
```
OBSERVED: this routine collects keys of matching camera-group-type into a list at `0x150(%r14)`.
It **is** gated by item+0x30 at 0x1a8df0 (`je 0x1a8e90` -> exit when cleared). So for a CLEARED
key-15 item, this selection path **skips** (expected behavior). A SECOND +0x30 gate exists in the same
function at 0x1a8ef5 (`cmpb $0x0,0x30(%rdi)`), same skip discipline.

### 2.C — Does a NON-skipping path on the item exist?
OBSERVED: the camera-group-type classifier `0xf6c60` (Angle 3) reads **only the key value (%esi)** and
never consults item+0x30. Any code that calls `0xf6c60` with the C6 key, OUTSIDE an enclosing
`cmpb $0x0,0x30` guard, would classify a cleared key-15 item as group-type 2 regardless of the clear.

ANGLE 2 RESULT: **LEAD (NEEDS_CODEX_VALIDATION).** The two C6 selection paths I disassembled fully
(0x1a8df0 family) ARE +0x30-gated and correctly skip a cleared item. BUT the classifier `0xf6c60`
itself is a +0x30-blind function operating on the key value (which survives the clear). Whether any of
the 58 `f2720` callers reach an image-effecting consumer without an enclosing +0x30 guard is NOT
resolved statically here — full guard-domination analysis per caller is required (proof plan §2).
No fully-traced non-skipping image path was confirmed under this static search.

---

## ANGLE 3 — Alternate route (key-15-derived pointer to an image kernel)

### 3.A — Key consumption across all 58 `f2720` callers (`angle23_f2720_caller_census.log`)
OBSERVED: across the 58 direct callers, the returned key int is used in three idioms:
1. **List-search predicate** — `cmpl %r15d/%r14d/-0x70(%rbp), %eax; je ...; addq $0x10,%rbx` (e.g.
   0xdf8f3, 0xe680f, 0xe688f, 0xe69df, 0xe6be0, 0xe745f, 0x227d5e). Key matched against a sought value
   while iterating 0x10-stride containers. NOT a literal-15 test.
2. **Classifier argument** — passed as `%esi` into `0xf6c60` (group-type), `0xe7730`, `0xe7420`,
   `0xe7370`, `0xf3bc0`, `0x1bea00` (e.g. 0x144c80, 0x145703, 0x1459d9, 0x31bce0, 0x31bd00).
3. **Stack-store then by-pointer** — `movl %eax,-0xNN(%rbp); leaq -0xNN(%rbp),%rsi` (e.g. 0x27d7ce,
   0x3f30ca, 0x402df7, 0x40d18d). Key copied out for downstream by-reference use.

### 3.B — `0xf6c60` key->camera-group-type classifier (`angle3_f6c60_classifier.log`, VERBATIM)
```
00000000000f6c60	pushq	%rbp
00000000000f6c64	pushq	%rbx
00000000000f6c69	cmpl	$0xf, %esi            ; key > 15 -> throw
00000000000f6c6c	ja	0xf6c9f
00000000000f6c6e	movl	$0xfc00, %eax         ; bitmask {10,11,12,13,14,15}
00000000000f6c73	btl	%esi, %eax
00000000000f6c76	jb	0xf6c8a              ; key in {10..15} -> group type 2
00000000000f6c78	movl	$0x1f, %eax           ; bitmask {0,1,2,3,4}
00000000000f6c7d	btl	%esi, %eax
00000000000f6c80	jae	0xf6c92             ; else group type 1
00000000000f6c82	movl	$0x0, (%rdi)          ; group type 0
...
00000000000f6c8a	movl	$0x2, (%rdi)          ; group type 2
...
00000000000f6c92	movl	$0x1, (%rdi)          ; group type 1
...
00000000000f6cae	... "unknown camera group type!"  (key > 15 throw path)
```
OBSERVED (load-bearing): bit math (computed by python on the masks) is
`0xfc00 = bits {10,11,12,13,14,15}`, `0x1f = bits {0,1,2,3,4}`. Therefore **key 15 -> camera-group-type 2**.
INFERRED: because the 0x3c90a5 clear leaves item+0x60 == 15, the classifier still maps the item to
group-type 2 after the clear (the classifier is +0x30-blind).

### 3.C — Alternate route to an image kernel?
OBSERVED: within the statically-traced caller set, the key-15 path terminates in (a) list membership
predicates, (b) group-type classification feeding key-collection lists (e.g. list at 0x150(%r14) in §2.B),
and (c) by-pointer stack copies. I did NOT statically trace any of these consumers all the way to an
image kernel (e.g. the SIMD anchor region at 0x3ecfe4) carrying a key-15-derived **pointer**.

ANGLE 3 RESULT: **no static alternate route to an image kernel confirmed under this search.**
The key VALUE (15) propagates past the clear into a group-type classifier (group-type 2) and into
key-collection lists — that is a **LEAD** that the clear of +0x30 does NOT neutralize the key's
*classification* identity. But a key-15-derived **pointer reaching an image kernel** independent of the
`call 0xf2720` census was NOT found here. Full forward dataflow from the group-type-2 lists to a kernel
is the open item (proof plan §3).
