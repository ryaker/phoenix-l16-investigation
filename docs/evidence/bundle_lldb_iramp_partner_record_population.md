# Bundle + LLDB IRAMP Partner Record Population Evidence

**Date:** 2026-05-12
**Status:** Partial evidence admitted for canonical review.
**Scope:** Corrected canonical bridge HDR quartet only.

This document verifies the local IRAMP partner-record append / population path upstream of the already bounded partner-vector gate.

It proves storage layout and first-hit runtime participation. It does not prove the semantic meaning of each field or the complete predicate that decides candidate acceptance.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable first-hit probes live in the repo:

- `tools/lldb_probes/iramp_partner_record_population/record_population_probe.py`
- `tools/lldb_probes/iramp_partner_record_population/record_population_first_28mm.lldb`
- `tools/lldb_probes/iramp_partner_record_population/record_population_first_35mm.lldb`
- `tools/lldb_probes/iramp_partner_record_population/record_population_first_70mm.lldb`
- `tools/lldb_probes/iramp_partner_record_population/record_population_first_150mm.lldb`

Generated run outputs go under ignored `runs/iramp_partner_record_population/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Candidate Grid / Bounds Work Before Append

The path initializes three stack descriptors and prepares `-0x1830` from `-0x1750` with element-size argument `8`:

```asm
0x366b00  movapd %xmm0, -0x1810(%rbp)
0x366b08  movapd %xmm0, -0x1820(%rbp)
0x366b10  movapd %xmm0, -0x1830(%rbp)
0x366b40  movl $0x8, %edx
0x366b45  leaq -0x1830(%rbp), %rdi
0x366b4c  leaq -0x1750(%rbp), %rsi
0x366b53  callq 0xf540
```

The first visible rejection is a non-positive count/extent test:

```asm
0x366b58  movl -0x174c(%rbp), %eax
0x366b5e  testl %eax, %eax
0x366b60  jle 0x368b89
```

Invalid projected coordinate pairs are written as sentinel `0x8000000080000000`:

```asm
0x366da0  movabsq $-0x7fffffff80000000, %rax
0x366daa  movq %rax, -0x4(%r12)
```

Before append, three span/sentinel gates can still reject the candidate:

```asm
0x366e08  subl -0x43c4(%rbp), %ecx
0x366e18  jle 0x368b89
0x366e1e  cmpl $0x7fffffff, %r15d
0x366e25  je 0x368b89
0x366e32  subl %r15d, %eax
0x366e3c  jle 0x368b89
```

These checks prove rejection gates exist before append. They do not, by themselves, prove public semantic names for the stack fields.

### Record Append

The local partner-vector uses `[rbp-0x1800]` as begin and `[rbp-0x17f8]` as end. Append zeroes one `0x280` record and advances the end pointer by `0x280`:

```asm
0x368833  movq -0x17f8(%rbp), %rbx
0x36883a  movq -0x17f0(%rbp), %r14
0x368841  cmpq %r14, %rbx
0x368844  jae 0x368866
0x368846  movl $0x280, %esi
0x36884b  movq %rbx, %rdi
0x36884e  callq __bzero
0x368853  addq $0x280, %rbx
0x36885a  movq %rbx, -0x17f8(%rbp)
```

The grow path uses the same `0x280` element size:

```asm
0x36894a  movq %r14, %rax
0x36894d  shlq $0x7, %rax
0x368951  leaq (%rax,%rax,4), %rdi
0x368955  callq operator new(unsigned long)
0x36898c  movl $0x280, %esi
0x368991  callq __bzero
```

### Physical Record Layout

After append, `[rbp-0x17f8]` is the new end pointer. The record being populated is therefore `end - 0x280`.

The installed binary fills exactly `0x280` bytes as:

- four int32 scalar fields at offsets `+0x00`, `+0x04`, `+0x08`, and `+0x0c`
- thirteen contiguous `0x30` descriptor-like blocks at offsets `+0x10`, `+0x40`, `+0x70`, `+0xa0`, `+0xd0`, `+0x100`, `+0x130`, `+0x160`, `+0x190`, `+0x1c0`, `+0x1f0`, `+0x220`, and `+0x250`

The descriptor at record offset `+0x40` is prepared via `0xf540`:

```asm
0x3689c3  movq -0x17f8(%rbp), %rbx
0x3689ca  addq $-0x240, %rbx
0x3689d1  movl $0xc, %edx
0x3689d6  movq %rbx, %rdi
0x3689d9  leaq -0x1820(%rbp), %rsi
0x3689e0  callq 0xf540
```

The four scalar fields are written immediately afterward:

```asm
0x3689e5  movq -0x17f8(%rbp), %rdi
0x3689ec  movl -0x4434(%rbp), %eax
0x3689f2  movl %eax, -0x280(%rdi)
0x3689f8  movl -0x43c4(%rbp), %eax
0x3689fe  movl %eax, -0x27c(%rdi)
0x368a04  movq -0x43e0(%rbp), %rax
0x368a0b  movl %eax, -0x278(%rdi)
0x368a11  movq -0x43c0(%rbp), %rax
0x368a18  movl %eax, -0x274(%rdi)
```

The remaining descriptor-like blocks are moved/swapped through `0xf340`:

```asm
0x368a1e  addq $-0x270, %rdi      ; record + 0x10
0x368a25  leaq -0x1830(%rbp), %rsi
0x368a2c  callq 0xf340
0x368a38  leaq -0x210(%rbx), %rdi ; record + 0x70
0x368a3f  movq %r13, %rsi
0x368a42  callq 0xf340
0x368a47  leaq -0x1e0(%rbx), %rdi ; record + 0xa0
0x368a4e  leaq -0x1a10(%rbp), %rsi
0x368a55  callq 0xf340
0x368a5a  leaq -0x1b0(%rbx), %rdi ; record + 0xd0
0x368a61  leaq -0x19e0(%rbp), %rsi
0x368a68  callq 0xf340
0x368a6d  leaq -0x180(%rbx), %rdi ; record + 0x100
0x368a74  leaq -0x19b0(%rbp), %rsi
0x368a7b  callq 0xf340
0x368a80  leaq -0x150(%rbx), %rdi ; record + 0x130
0x368a87  leaq -0x1980(%rbp), %rsi
0x368a8e  callq 0xf340
0x368a93  leaq -0x120(%rbx), %rdi ; record + 0x160
0x368a9a  leaq -0x1950(%rbp), %rsi
0x368aa1  callq 0xf340
0x368aa6  leaq -0xf0(%rbx), %rdi  ; record + 0x190
0x368aad  leaq -0x1920(%rbp), %rsi
0x368ab4  callq 0xf340
0x368ab9  leaq -0xc0(%rbx), %rdi  ; record + 0x1c0
0x368ac0  leaq -0x18f0(%rbp), %rsi
0x368ac7  callq 0xf340
0x368acc  leaq -0x90(%rbx), %rdi  ; record + 0x1f0
0x368ad3  leaq -0x18c0(%rbp), %rsi
0x368ada  callq 0xf340
0x368adf  leaq -0x60(%rbx), %rdi  ; record + 0x220
0x368ae3  leaq -0x1890(%rbp), %rsi
0x368aea  callq 0xf340
0x368aef  addq $-0x30, %rbx       ; record + 0x250
0x368af3  movq %rbx, %rdi
0x368af6  leaq -0x1860(%rbp), %rsi
0x368afd  callq 0xf340
```

`0xf340` is a descriptor move/swap helper, not a plain byte-copy. It swaps/moves a `0x30`-byte descriptor-like structure and contains a guard string:

```asm
0xf340  pushq %rbp
...
0xf370  movups (%rdi), %xmm0
0xf373  movl (%rsi), %ecx
...
0xf3c0  movq %rax, 0x20(%rdi)
0xf3c4  movq %rcx, 0x20(%rsi)
0xf3d0  movq %rcx, 0x28(%rdi)
0xf3d4  movq %rax, 0x28(%rsi)
...
0xf3f1  leaq ... ; "moving into reference origin is invalid!"
```

`0xf540` is the already canonical alloc/resize helper. In this context it fills descriptor fields and allocates backing storage when needed:

```asm
0xf540  pushq %rbp
...
0xf644  movslq (%r14), %rax
0xf647  imulq %r15, %rax
0xf64b  movslq 0x4(%r14), %rdi
0xf64f  imulq %rax, %rdi
0xf661  movl $0x40, %esi
0xf666  callq 0x7720
...
0xf68c  movq %rax, 0x20(%rbx)
0xf690  movl $0x0, (%rbx)
0xf696  movl $0x0, 0x4(%rbx)
0xf69d  movl %ecx, 0x8(%rbx)
0xf6a0  movl %edx, 0xc(%rbx)
0xf6a3  movl (%r14), %eax
0xf6a6  movl %eax, 0x10(%rbx)
0xf6a9  movl 0x4(%r14), %eax
0xf6ad  movl %eax, 0x14(%rbx)
```

## Runtime Proof Summary

All four focal tiers hit `0x368b02`, which is after the scalar writes and after all `0xf340` descriptor moves in the append path.

The probe reads the local vector begin/end from `[rbp-0x1800]` and `[rbp-0x17f8]`, computes `record = end - 0x280`, and reads the first populated record metadata. ASLR-specific pointer values are omitted from the summary table, but every captured descriptor had non-zero `ptr_20` and `ptr_28`.

Each tuple below is:

`(i32_00, i32_04, i32_08, i32_0c; i32_10, i32_14, i32_18, i32_1c)`

| Zoom | Vector state at first population | Scalar fields `+0x00..+0x0c` | `+0x10` | `+0x40` | `+0x70` | `+0xa0` | Repeated `+0xd0..+0x250` shape |
|---|---|---|---|---|---|---|---|
| `28mm` | `diff=640`, `npartners=1` | `(5, 3, 175, 440)` | `(0, 0, 28, 28; 28, 28, 28, 28)` | `(0, 0, 28, 28; 28, 28, 28, 28)` | `(-85, -85, 255, 522; 170, 437, 340, 607)` | `(-81, -81, 251, 518; 170, 437, 332, 599)` | `(-16, -16, 84, 191; 68, 175, 100, 207)` |
| `35mm` | `diff=640`, `npartners=1` | `(-6, 1, 315, 299)` | `(0, 0, 28, 28; 28, 28, 28, 28)` | `(0, 0, 28, 28; 28, 28, 28, 28)` | `(-85, -85, 406, 383; 321, 298, 491, 468)` | `(-81, -81, 402, 379; 321, 298, 483, 460)` | `(-16, -16, 145, 135; 129, 119, 161, 151)` |
| `70mm` | `diff=640`, `npartners=1` | `(2, -2, 368, 344)` | `(0, 0, 32, 32; 32, 32, 32, 32)` | `(0, 0, 32, 32; 32, 32, 32, 32)` | `(-73, -73, 439, 419; 366, 346, 512, 492)` | `(-69, -69, 435, 415; 366, 346, 504, 484)` | `(-16, -16, 188, 178; 172, 162, 204, 194)` |
| `150mm` | `diff=640`, `npartners=1` | `(3408, 2760, 3960, 3171)` | `(0, 0, 33, 32; 33, 32, 33, 32)` | `(0, 0, 33, 32; 33, 32, 33, 32)` | `(-73, -73, 625, 484; 552, 411, 698, 557)` | `(-69, -69, 621, 480; 552, 411, 690, 549)` | `(-16, -16, 275, 209; 259, 193, 291, 225)` |

Runtime stop points:

```text
28mm:  Process stopped at libcp+0x368b02; diff=640; npartners=1; scalar fields (5, 3, 175, 440)
35mm:  Process stopped at libcp+0x368b02; diff=640; npartners=1; scalar fields (-6, 1, 315, 299)
70mm:  Process stopped at libcp+0x368b02; diff=640; npartners=1; scalar fields (2, -2, 368, 344)
150mm: Process stopped at libcp+0x368b02; diff=640; npartners=1; scalar fields (3408, 2760, 3960, 3171)
```

In the `150mm` run two worker threads were stopped at the same breakpoint. The recorded packet is from the first packet captured by the LLDB command script.

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- The partner-record population path reaches `0x368b02` at `28mm`, `35mm`, `70mm`, and `150mm`.
- The first populated partner-vector state in each captured run has one `0x280` record.
- A `0x280` partner record is physically composed of four int32 scalar fields followed by thirteen contiguous `0x30` descriptor-like blocks.
- Record offset `+0x40` is prepared by `0xf540` with argument `0xc`.
- The descriptor blocks at `+0x10`, `+0x70`, `+0xa0`, `+0xd0`, `+0x100`, `+0x130`, `+0x160`, `+0x190`, `+0x1c0`, `+0x1f0`, `+0x220`, and `+0x250` are moved/swapped into the zeroed record via `0xf340`.
- The pre-append region includes explicit rejection gates and sentinel writes before a record is appended.

## Not Proven Here

- Public semantic names for the four scalar fields.
- Public semantic names for the thirteen `0x30` descriptor-like blocks.
- The complete upstream candidate-generation and candidate-acceptance predicate.
- Whether the first captured record is representative of every record later appended in a render.
- Runtime empty-gate hits at `35mm` or `150mm`.
- WTA, sub-pixel refinement, bilinear sampling, final acceptance/rejection, or final artifact-suppression math.
