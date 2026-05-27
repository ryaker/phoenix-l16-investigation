# Bundle + LLDB IRAMP Tuple Downstream-Consumer Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document narrows the first proven downstream consumer of the three-float
refined tuple written at `0x369e7e..0x369e91`.

It proves:

- the tuple is read later in the same IRAMP body, not merely written
- the third tuple scalar is loaded at `0x36a7d8`
- the first and second tuple floats are read at `0x36a803` and `0x36a814` to adjust a coordinate pair
- the third tuple scalar forms a live `vec4` multiplier consumed by the add loop at `0x36a8c0..0x36a8cb`
- the canonical four-zoom bridge HDR quartet all reach that downstream multiply-add site

It does not prove public tuple-field names, complete downstream policy, or final
ghost-suppression acceptance / rejection.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_tuple_downstream_consumer/consumer_probe.py`
- `tools/lldb_probes/iramp_tuple_downstream_consumer/consumer_first_28mm.lldb`
- `tools/lldb_probes/iramp_tuple_downstream_consumer/consumer_first_35mm.lldb`
- `tools/lldb_probes/iramp_tuple_downstream_consumer/consumer_first_70mm.lldb`
- `tools/lldb_probes/iramp_tuple_downstream_consumer/consumer_first_150mm.lldb`

Generated render outputs go under ignored
`runs/iramp_tuple_downstream_consumer/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Partner-Record Loop

After the known first accumulator region, the body enters a later partner-record
consumer loop. It skips the consumer path when the partner vector is empty:

```asm
0x36a728  movq  -0x1800(%rbp), %r8
0x36a72f  movq  -0x17f8(%rbp), %rdx
0x36a736  cmpq  %r8, %rdx
0x36a741  je    0x36a934
```

For each partner record, it computes `record_offset = r15 * 0x280`, checks the
record's pair-table sentinel, and skips sentinel entries:

```asm
0x36a790  leaq  (%r15,%r15,4), %rsi
0x36a794  shlq  $0x7, %rsi
0x36a798  movl  0x28(%r8,%rsi), %edi
0x36a79d  imull %r14d, %edi
0x36a7a1  addl  %r12d, %edi
0x36a7a7  movq  0x30(%r8,%rsi), %rbx
0x36a7ac  cmpl  $0x80000000, (%rbx,%rdi,8)
0x36a7b3  je    0x36a910
```

### Tuple Reads

For non-sentinel entries, the same record supplies tuple stride/base fields
from `+0x58` and `+0x60`. The third tuple scalar is read first:

```asm
0x36a7c0  movl 0x58(%r8,%rsi), %edx
0x36a7c5  imull %r14d, %edx
0x36a7c9  addl %r12d, %edx
0x36a7cc  movslq %edx, %rdx
0x36a7cf  movq 0x60(%r8,%rsi), %rbx
0x36a7d4  leaq (%rdx,%rdx,2), %rcx
0x36a7d8  movss 0x8(%rbx,%rcx,4), %xmm0
0x36a7de  movaps %xmm0, -0x4300(%rbp)
```

The first and second tuple floats are then added into an adjusted coordinate
pair:

```asm
0x36a7f7  movss -0x4310(%rbp), %xmm1
0x36a7ff  subss %xmm0, %xmm1
0x36a803  addss (%rbx,%rcx,4), %xmm1
0x36a808  movss -0x4320(%rbp), %xmm2
0x36a810  subss %xmm0, %xmm2
0x36a814  addss 0x4(%rbx,%rcx,4), %xmm2
0x36a81a  movss %xmm1, -0x1288(%rbp)
0x36a822  movss %xmm2, -0x1284(%rbp)
```

The adjusted pair is passed to helper `0x372a00`:

```asm
0x36a82a  leaq -0x1280(%rbp), %rsi
0x36a831  leaq -0x1288(%rbp), %rcx
0x36a838  callq 0x372a00
```

This proof does not name `0x372a00`; it only proves that the adjusted
tuple-derived pair is an argument to it.

### Third-Scalar Multiplier And Add Loop

After the helper returns, the saved third scalar is transformed into a `vec4`
multiplier.

`0x5a8120` decodes to `-0.5` in the installed bundle:

```text
0x005a8120: -0.5
```

The scalar transform is:

```asm
0x36a84b  movaps -0x4300(%rbp), %xmm3
0x36a852  movaps %xmm3, %xmm1
0x36a855  addss 0x5a8120, %xmm1
0x36a85d  xorps %xmm0, %xmm0
0x36a860  maxss %xmm1, %xmm0
0x36a864  movaps %xmm3, %xmm1
0x36a867  shufps $0x0, %xmm1, %xmm1
0x36a86b  addss %xmm0, %xmm0
0x36a86f  xorps %xmm2, %xmm2
0x36a872  blendps $0xe, %xmm2, %xmm0
0x36a878  addps %xmm1, %xmm0
```

Let `t` be the third tuple scalar. This produces:

```text
(t + 2 * max(0, t - 0.5), t, t, t)
```

That multiplier is then used by a vector add loop:

```asm
0x36a8c0  movaps (%rcx,%rdi), %xmm1
0x36a8c4  mulps  %xmm0, %xmm1
0x36a8c7  addps  (%rdx,%rdi), %xmm1
0x36a8cb  movaps %xmm1, (%rdx,%rdi)
```

The same path also accumulates the third scalar into `xmm2` after each
non-sentinel partner record:

```asm
0x36a8fe  addss %xmm3, %xmm2
```

The running scalar starts from the installed-bundle constant at `0x5df904`,
which decodes to `0.200000003`, and a reciprocal is formed after the loop:

```asm
0x36a739  movss 0x5df904, %xmm2
...
0x36a934  shufps $0x0, %xmm2, %xmm2
0x36a938  rcpss  %xmm2, %xmm2
```

This proves a tuple-scalar-weighted downstream accumulation and normalization
surface. It does not prove whether this is the final contributor acceptance /
rejection policy.

## Runtime Proof

The LLDB probe breaks at `0x36a8c0`, the first vector load in the downstream
add loop. At that point, the static tuple reads and multiplier construction have
already happened.

Captured fields:

- saved third tuple scalar at `rbp-0x4300`
- adjusted coordinate pair at `rbp-0x1288..0x1284`
- live multiplier vector in `xmm0`
- running scalar accumulator in `xmm2`
- source `vec4` before multiply
- destination `vec4` before add

### Four-Zoom Packets

| Zoom | Third scalar `t` | Adjusted pair | Multiplier vector | Row stride |
|---|---:|---|---|---:|
| `28mm` | `0.0` | `(-1.5435848236083984, -1.7435970306396484)` | `(0.0, 0.0, 0.0, 0.0)` | `640` |
| `35mm` | `0.5421872138977051` | `(7.36444091796875, 4.609716415405273)` | `(0.6265616416931152, 0.5421872138977051, 0.5421872138977051, 0.5421872138977051)` | `640` |
| `70mm` | `0.0` | `(18.83077621459961, -32.93846893310547)` | `(0.0, 0.0, 0.0, 0.0)` | `544` |
| `150mm` | `0.9917429685592651` | `(15.004558563232422, -0.5856380462646484)` | `(1.9752289056777954, 0.9917429685592651, 0.9917429685592651, 0.9917429685592651)` | `544` |

All four first-hit packets had `partner_record_index_r15 = 0`,
`byte_offset_rdi = 0`, and `running_scalar_sum_xmm2 = (0.20000000298023224,
0.0, 0.0, 0.0)` at the breakpoint.

Representative source/destination samples:

| Zoom | Source `vec4` before multiply | Destination `vec4` before add |
|---|---|---|
| `28mm` | `(0.49824708700180054, -0.0028459576424211264, -0.002670508110895753, 0.37568914890289307)` | `(-0.0768294557929039, 0.0, 0.0, 0.0)` |
| `35mm` | `(0.036988161504268646, -0.0008951863273978233, -0.0003239864017814398, 0.13123728334903717)` | `(0.026514656841754913, 0.0, 0.0, 0.0)` |
| `70mm` | `(0.0, 0.0, 0.0, 0.0)` | `(0.06421202421188354, 0.0, 0.0, 0.0)` |
| `150mm` | `(0.0054840571247041225, 0.00008909688767744228, -0.000022056286979932338, 0.0000039287988329306245)` | `(-0.05150976777076721, 0.0, 0.0, 0.0)` |

First-hit source/destination values are not semantic constants.

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- A downstream consumer of the three-float refined tuple exists in the same
  IRAMP body.
- The consumer loop reads partner records with `0x280`-byte stride and skips
  pair-table sentinel entries.
- The third tuple scalar is read from record `+0x60` storage at `0x36a7d8`.
- The first and second tuple floats are read from the same tuple storage at
  `0x36a803` and `0x36a814` and are added into an adjusted coordinate pair.
- The adjusted coordinate pair is passed to helper `0x372a00`.
- The third scalar forms multiplier vector
  `(t + 2 * max(0, t - 0.5), t, t, t)`.
- The multiplier vector is used at `0x36a8c0..0x36a8cb` to multiply a source
  `vec4`, add a destination `vec4`, and store the destination `vec4`.
- The third scalar is also added into a running scalar sum initialized from
  `0x5df904 = 0.200000003`, and a reciprocal of that sum is formed after the
  partner loop.
- The downstream multiply-add site is runtime-observed on the canonical
  `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR quartet.

## Not Proven Here

- Public names for the three tuple fields.
- Public meaning of the third scalar.
- Whether first-hit tuple-consumer values are representative.
- Complete downstream consumer topology after the reciprocal is formed.
- Whether this is the final ghost-suppression acceptance / rejection policy.
- Any complete Lumen-quality merge algorithm.
