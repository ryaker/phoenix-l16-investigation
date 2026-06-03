# Lane A reducer — reproduction commands (static)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

```bash
B=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib

# Sole caller of the IRAMP entry (arg loads: src1=+0x238, src2=+0x248)
arch -x86_64 lldb --batch -o "target create $B" -o 'disassemble --start-address 0x3ec770 --count 80'

# IRAMP entry: cosf window table + dispatch to 0x3661b0 (src1/src2 pass through)
arch -x86_64 lldb --batch -o "target create $B" -o 'disassemble --start-address 0x365960 --count 400'

# Reducer body: src1 anchor (0x366c77, 0x36a004), src2 ROI (0x366915), accumulate (0x369fa1..)
arch -x86_64 lldb --batch -o "target create $B" -o 'disassemble --start-address 0x3661b0 --count 900'

# Confirm string anchoring the caller as processLevel0
arch -x86_64 lldb --batch -o "target create $B" -o 'disassemble --start-address 0x3ec820 --count 10'
```

## Key VAs (all OBSERVED via disasm)
| VA | what |
|---|---|
| `0x3ec7ac` | `movq 0x238(%rdi),%rsi` — src1 -> arg1 |
| `0x3ec7b3` | `movq 0x248(%rdi),%rdx` — src2 -> arg2 |
| `0x3ec7c2` | `leaq 0x270(%rdi),%rcx` — warpfield vector (arg3) |
| `0x3ec7c9` | `leaq 0x258(%rdi),%r8` — source-image vector (arg4) |
| `0x365960` | IRAMP entry: cosf window table + dispatch |
| `0x3661b0` | reducer body (all src1/src2 work) |
| `0x366c77` | warped coord validated vs src1 w/h `0x30/0x34(r13)` |
| `0x36a004` | output extent clamped by src1 dims |
| `0x366915` | src2 read -> separate ROI box (pad 0x8) |
| `0x369fa1` | `mulps (%rdi),%xmm1` patch*weight |
| `0x369fa4` | `addps (%rdx,%rcx,4),%xmm1` ACCUMULATE |
| `0x369fa8` | `movaps %xmm1,(%rdx,%rcx,4)` store back (running sum) |
| `0x366356` | accumulator `-0x1710(rbp)` zeroed |
| `0x36a860` | lone `maxss` — post-loop bbox finalize, NOT pixel path |

Method: static disasm only; no runtime. Re-extract to verify before any promotion.
