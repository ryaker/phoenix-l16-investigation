# Lumen.app Proof-Only Audit

**Date:** 2026-04-22
**Authoring rule:** this document includes only statements backed by direct inspection of the installed `Lumen.app` bundle, or by exact-path scratch documents whose primary evidence matches the live bundle.
**No hypothesis:** if a point was not directly proven, it is listed under "Not proven here" instead of being completed by inference.

## Scope

This audit was limited to bundle-backed questions that can be checked directly from:

- `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen`
- `/Volumes/Dev/lumen-phoenix-scratch/*.md`

`l16-tech-part-1-3.md` was used as a contradiction guardrail, not as a source for the findings below. A term search for

`Ceres|Cauchy|warp|dst|coordinate|Triangulator|ReProjectionCost|f_scale|0x5c3580|0xf540|IRAMP`

returned no matches in `/Users/ryaker/Documents/Light_Work/l16-tech-part-1-3.md`, so the specific findings below are neither confirmed nor contradicted there.

## Bundle Fingerprint

| Item | Value |
|---|---|
| App path | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app` |
| `libcp.dylib` path | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |
| Main executable path | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen` |
| `libcp.dylib` type | `Mach-O 64-bit dynamically linked shared library x86_64` |
| `Lumen` type | `Mach-O 64-bit executable x86_64` |
| `libcp.dylib` size | `6935696` bytes |
| `Lumen` size | `15312240` bytes |
| `libcp.dylib` SHA-256 | `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9` |
| `Lumen` SHA-256 | `1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d` |

## Structural Fact Needed For Byte Reads

`otool -l` on `libcp.dylib` shows:

```text
segname __TEXT
vmaddr  0x0000000000000000
fileoff 0
```

That means a virtual address inside `__TEXT` is also the file offset for this specific `libcp.dylib`. The `OPEN-FSCALE` contradiction depends on this detail.

## Verified Finding 1: `OPEN-FSCALE` is not open for this bundle

### Direct byte proof

Reading 32 bytes from file offset `0x5c3580` in the live `libcp.dylib` produced:

```text
00000000: 000000000000f03f 000000000000f03f  .......?.......?
00000010: 5f427b09ed251f40 5f427b09ed251f40  _B{..%.@_B{..%.@
```

The first 16 bytes are two little-endian IEEE754 doubles:

- `0x3ff0000000000000` = `1.0`
- `0x3ff0000000000000` = `1.0`

The older four-float decode `(42.0, 1023.0, 0.0005468..., -0.0000204...)` came from the wrong file offset. It does not describe the bytes at `0x5c3580` in this bundle.

### Direct code-site proof

The live disassembly at `libcp+0x20be9d` shows the exact 16-byte block at `0x5c3580` being loaded and copied into a stack object:

```text
0x20be9d: movq   0x4434e4(%rip), %rax
0x20bea4: addq   $0x10, %rax
0x20bea8: movq   %rax, -0x288(%rbp)
0x20beaf: movaps 0x3b76ca(%rip), %xmm0     ; load from 0x5c3580
0x20beb6: movups %xmm0, -0x280(%rbp)
```

This proves, for this exact bundle:

- the 16-byte constant at `0x5c3580` is real and live
- the constant loaded there is exactly `(1.0, 1.0)` as two doubles
- the contrary "4 floats" reading is wrong for this binary at this address

### Corroborating scratch evidence

`/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md` reports a live LLDB stop at `libcp+0x20bebd` and reads the stack payload as:

- `a_ = 1.0`
- `b_ = 1.0`

That scratch file agrees with the live bundle bytes above. The older contrary text in `/Volumes/Dev/lumen-phoenix-scratch/ceres_residual_bodies.md` is superseded by direct bundle evidence and by the newer LLDB-backed scratch document.

### Audit verdict

For this installed `libcp.dylib`, `OPEN-FSCALE` is resolved. The direct byte-backed truth is:

- the constant at `libcp+0x5c3580` begins with the two doubles `(1.0, 1.0)`
- the earlier `(42.0, 1023.0, ...)` claim is a bad-offset error

## Verified Finding 2: the warp dst-coordinate array format is partly decoded, and `0xf540` is not the pair-writing loop

### What `0xf540` is proven to do

The function at `libcp+0xf540` is a generic resize/allocate helper, not a coordinate-writing loop.

Direct evidence:

- its disassembly validates dimensions, computes `width * height * element_size`, allocates storage, and records metadata in the destination object
- strings tied to `0xf540` elsewhere in the corpus are `"invalid resize dimensions!"` and `"cannot resize a reference-type image!"`

Key instructions from `libcp+0xf540`:

```text
0xf556: movl   (%r14), %ecx
0xf559: movl   0x4(%r14), %edx
...
0xf644: movslq (%r14), %rax
0xf647: imulq  %r15, %rax
0xf64b: movslq 0x4(%r14), %rdi
0xf64f: imulq  %rax, %rdi
...
0xf666: callq  0x7720
...
0xf68c: movq   %rax, 0x20(%rbx)
0xf69d: movl   %ecx, 0x8(%rbx)
0xf6a0: movl   %edx, 0xc(%rbx)
0xf6a6: movl   %eax, 0x10(%rbx)
0xf6ad: movl   %eax, 0x14(%rbx)
```

This is storage setup and metadata recording. It is not writing `(x, y)` sample pairs into the backing buffer.

### Where the pair buffer is allocated

Inside `libcp+0x3661b0`, the stack object at `-0x1760(%rbp)` is zeroed and then passed to `0xf540` with `edx = 8`:

```text
0x366488: movaps %xmm0, -0x1740(%rbp)
0x36648f: movaps %xmm0, -0x1750(%rbp)
0x366496: movaps %xmm0, -0x1760(%rbp)
0x36649d: movl   %eax, -0x16f8(%rbp)
0x3664a3: movl   %ecx, -0x16f4(%rbp)
0x3664a9: leaq   -0x1760(%rbp), %rdi
0x3664b0: leaq   -0x16f8(%rbp), %rsi
0x3664b7: movl   $0x8, %edx
0x3664bc: callq  0xf540
```

This proves the buffer being prepared there has 8-byte elements.

### Where the `(x, y)` pairs are actually written

The same function later fills the allocated backing store with nested loops at `0x366500..0x366553`:

```text
0x3664ce: movq   -0x1750(%rbp), %rax
0x3664d5: movq   -0x1740(%rbp), %r9
0x3664e3: addq   $0x4, %r9
0x3664e7: movslq -0x1748(%rbp), %r8
0x3664ee: shlq   $0x3, %r8
...
0x36650b: leal   (%rax,%r10,8), %edx
...
0x366520: movl   %esi, -0x4(%rcx)
0x366523: movl   %edx, (%rcx)
0x366528: movq   -0x1750(%rbp), %rax
0x366532: addl   $0x8, %esi
0x366535: addq   $0x8, %rcx
0x366545: incq   %r10
0x36654b: addq   %r8, %r9
```

What this directly proves:

- each record is 8 bytes
- each record contains two 32-bit integers
- `-0x1750(%rbp)` is used as the pair-grid dimension qword: low 32 bits feed the inner-loop bound, high 32 bits feed the outer-loop bound after `shrq $0x20`
- `-0x1748(%rbp)` supplies the row-stride count, which is multiplied by `8` before row-to-row pointer advancement
- the first stored integer is at record offset `0`
- the second stored integer is at record offset `4`
- the first integer increments by `8` across the inner loop
- the second integer increments by `8` across the outer loop

The generated backing buffer is therefore a regular integer grid of packed `(x, y)` pairs with an 8-pixel step in both axes.

### Where the same pairs are consumed

Later in the same function, the transform loop reads the same records back as:

```text
0x366bcc: movq   -0x1740(%rbp), %r15
...
0x366bf7: addq   $0x4, %r15
...
0x366c70: movl   -0x4(%r15), %eax
0x366c74: movl   (%r15), %esi
...
0x366dc0: addq   $0x8, %r15
```

That consumption pattern exactly matches the writer:

- `-0x4(%r15)` reads the first 32-bit field of the record
- `(%r15)` reads the second 32-bit field of the record
- advancing by 8 bytes moves to the next pair

### What is resolved and what is still not proven

Resolved for this bundle:

- the dst-coordinate array is real
- its backing buffer holds packed int32 pairs
- the pair spacing is an 8-pixel lattice, not a dense `+1/+1` full-image grid
- `0xf540` allocates/prepares the storage, but does not itself write the `(x, y)` values

Still not proven here:

- the full high-level semantic name of the pair grid
- the exact closed-form meaning of the starting values held in `-0x43e8(%rbp)` and `-0x43f0(%rbp)` beyond "earlier integer bases computed in the same function"
- whether the grid should be described as "tile-local", "canvas-space", or by some stronger label

Those labels would require more decoding than the current instructions alone justify.

## Precision Corrections To Existing Notes

These corrections are supported by direct bundle evidence above.

| Existing wording | Proven correction |
|---|---|
| `OPEN-FSCALE` is still unresolved because `0x5c3580` may decode as four floats | For this bundle, the bytes at `0x5c3580` begin with the two doubles `(1.0, 1.0)`. The four-float reading came from the wrong file offset. |
| `libcp+0xf540` writes the dst-coordinate array | `0xf540` prepares 8-byte-element storage and records metadata. The actual pair writes occur later at `0x366520..0x366523` inside `libcp+0x3661b0`. |
| the warp loop iterates a dense pixel grid | The proven writer and reader both operate on an 8-step lattice of packed int32 pairs. |

## Not Proven Here

The following were intentionally not promoted to truth in this document:

- any symbolic name for `___lldb_unnamed_symbol1007` beyond what its instructions prove
- any claim that the dst-coordinate array is definitively tile-local, canvas-global, or anchor-indexed
- any claim about how the start bases at `-0x43e8/-0x43f0` should be interpreted outside the exact arithmetic visible in `0x3661b0`
- any bundle behavior not directly inspected from the installed `Lumen.app` or from matching primary-evidence scratch docs

## Primary Evidence Paths

- Live bundle:
  - `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
  - `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen`
- Matching scratch docs:
  - `/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md`
  - `/Volumes/Dev/lumen-phoenix-scratch/ceres_residual_bodies.md`
  - `/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md`
  - `/Volumes/Dev/lumen-phoenix-scratch/va_registry.md`
