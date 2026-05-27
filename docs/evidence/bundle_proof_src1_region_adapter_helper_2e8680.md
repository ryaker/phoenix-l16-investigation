# Bundle Proof: `0x2e8680` Helper Under Visible `src1` Region Adapter

## Scope

This note bounds the installed-bundle helper `libcp+0x2e8680`, which is called
inside the already identified visible-`src1` per-source virtual target
`libcp+0x341770`.

It builds on:

- [bundle_proof_src1_source_image_producer_topology.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_source_image_producer_topology.md)
- [lldb_src1_visible_gated_virtual_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_visible_gated_virtual_four_zoom.md)

It proves:

- `0x341770` calls `0x2e8680` from its per-source region-adapter body
- `0x2e8680` validates one source region / Bayer image descriptor
- `0x2e8680` allocates/prepares one output descriptor through `0xf540`
- `0x2e8680` installs a single callback object with vtable/address point
  `0x659fc0`
- the callback's substantive executor slot is `0x2e8cc0`
- `0x2e8cc0` is a one-source 16-bit SIMD region/pixel kernel over one
  source/output pair
- this helper branch is not the missing multi-source reducer, final blend, C6
  routing closure, or final acceptance/rejection stage

It does not prove:

- public class or function names for these helpers
- semantic `src1` camera membership
- semantic `src1` contents
- C6 routing
- the exact upstream `src1` / `src2` merge/reduction mechanism
- that `0x2e8680` completed at runtime in the gated four-zoom probe

The last limitation matters. The four-zoom LLDB proof selected vtable slot
`0x341770`, then intentionally killed at the virtual callsite. This note
therefore uses installed-bundle static proof for the normal body reached by that
selected target. It must not be misread as an independent runtime-completion
proof for `0x2e8680`.

## Bundle + Commands

Binary:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

Commands:

```bash
arch -x86_64 lldb -b \
  -o "target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib" \
  -o "disassemble --start-address 0x341770 --count 220"

arch -x86_64 lldb -b \
  -o "target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib" \
  -o "image lookup -a 0x2e8680" \
  -o "disassemble --start-address 0x2e8680 --count 120"

arch -x86_64 lldb -b \
  -o "target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib" \
  -o "disassemble --start-address 0x2e8870 --count 180"

arch -x86_64 lldb -b \
  -o "target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib" \
  -o "memory read --format x --size 8 --count 12 0x659fc0" \
  -o "disassemble --start-address 0x2e8cc0 --end-address 0x2e9d00"
```

Additional scratch artifact:

`/private/tmp/l16_2e8cc0_disasm.txt`

## Caller Context At `0x341770`

`0x341770` is the first captured visible-`src1` per-source virtual target:

```text
0x3e4b09 -> 0x3e3279 -> 0x31af30 -> 0x33ede0 -> 0x33f180
0x33f3e8 -> vtable address point 0x65b3c8, slot +0x30 = 0x341770
```

The static caller body:

- treats incoming `rsi` as the per-source record from the lower producer path
- intersects/clips integer region fields from that record
- builds a stack source-region descriptor at `-0x50(%rbp)`
- calls `0xf2750` and `0xf32d0` on the record-associated object at `0x8(%rbx)`
- loads another record/object field from `*(record[0] + 0x198)`
- calls `0x2e8680` with the stack source descriptor and an output descriptor
  local
- intersects the returned output descriptor with record fields `+0x30..+0x3c`
- writes adjusted descriptor fields back to the original record around
  `+0x100..+0x128`

Instruction anchors:

```text
0x341847: callq 0xf2750
0x341857: callq 0xf32d0
0x341863: movq 0x198(%rax), %rcx
0x341880: callq 0x2e8680
0x34194b..0x3419c5: writes back record fields around +0x100..+0x128
```

Safe conclusion: `0x2e8680` is reached from a per-source record-adapter body.
The caller context is one record/source at a time, not an exposed multi-source
merge closure.

## Helper Body At `0x2e8680`

`image lookup -a 0x2e8680` identifies the body as an installed-bundle text
symbol at:

```text
libcp.dylib[0x2e8680] (libcp.dylib.__TEXT.__text + 3040304)
```

The helper begins by saving:

- `rdi` into `r15`
- `rsi` into `rbx`
- `rdx` into `r14`
- `rcx` into `r13`
- one scalar float from `xmm1`

It then performs guard checks before doing any executor work:

- `0x2e86b6..0x2e86c3`: ORs the first four 32-bit fields of the source
  descriptor and rejects an odd domain bit
- `0x2e86c9..0x2e86d1`: ORs source image size fields at `+0x10/+0x14` and
  rejects an odd image-size bit
- `0x2e86d7..0x2e86e4`: compares the descriptor bit-depth field against a
  constant and rejects unsupported depth
- reject strings are:
  `"invalid source domain!"`, `"invalid bayer image size!"`, and
  `"unsupported bit-depth!"`

The normal path:

- calls `0xef120` using the incoming descriptor/object pointer
- selects four pointer/row fields from the returned object, with branch shape
  dependent on fields in `r13` / `r14`
- calls `0xf540` with `edx = 2` using destination dimensions from source fields
  `+0x10/+0x14`
- allocates a `0x38`-byte callback object
- writes vtable/address point `0x659fc0` into the callback
- stores exactly these callback fields:
  source descriptor pointer, one source/image accessor pointer, pointer to
  local row/pointer state, pointer to one scalar float, destination descriptor
  pointer, and pointer to a local counter
- dispatches the callback through generic executor `0x5440`
- returns the local counter value

Instruction anchors:

```text
0x2e86f8: callq 0xef120
0x2e873d: callq 0xf540
0x2e877a: operator new(0x38)
0x2e8784: writes vtable/address point 0x659fc0
0x2e878e..0x2e87b4: writes callback fields +0x08..+0x30
0x2e87d1: callq 0x5440
0x2e87f7: reads local counter into return register path
```

Safe conclusion: `0x2e8680` is a one-source Bayer/RAW image-region helper that
prepares an output descriptor and runs one callback. It does not consume an
IRAMP contributor vector, a camera list, a warp-vector array, `src1` plus
`src2`, or any other multi-input reducer shape.

## Callback Vtable At `0x659fc0`

Raw vtable/address-point bytes:

```text
0x659fc0: 0x2e8c10 0x2e8c20
0x659fd0: 0x2e8c30 0x2e8c70
0x659fe0: 0x2e8ca0 0x2e8cb0
0x659ff0: 0x2e8cc0 0x2e9d00
0x65a000: 0x2e9d20 0x0
```

The substantive executor slot is:

```text
slot +0x30 = 0x2e8cc0
```

The nearby slots are copy/clone/destructor-style plumbing:

- `0x2e8c10`: no-op return
- `0x2e8c20`: delete
- `0x2e8c30`: allocates/copies the `0x38`-byte callback
- `0x2e8c70`: placement-copy style field copy
- `0x2e8ca0`: no-op return
- `0x2e8cb0`: delete

Safe conclusion: `0x2e8cc0` is the worker body associated with the helper's
callback object.

## Callback Body At `0x2e8cc0`

The callback body is large, but its bounded shape is clear:

- builds an image/region descriptor through `0x178b0`
- allocates aligned working buffers through `0x7720`
- initializes one buffer with `0x7fffffff`
- initializes another with `memset_pattern16`
- iterates over the supplied region dimensions
- operates on 16-bit samples through `movzwl`, `movw`, and SIMD unsigned-word
  operations
- uses Bayer/parity state through low-bit XOR/AND operations
- uses `pblendvb`, `pminuw`, `pmaxuw`, and `psubusw` in the vectorized path
- uses high-bit mask tests with `0x8000`
- writes accepted output samples after clearing with `0x7fff`
- atomically adds the local accepted/sample counter to the counter pointer held
  in the callback at `+0x30`
- frees local buffers and destroys the temporary descriptor

Instruction anchors:

```text
0x2e8d02: callq 0x178b0
0x2e8d6b: callq 0x7720
0x2e8d8d: writes 0x7fffffff sentinel
0x2e8df6: callq 0x7720
0x2e8e30: callq memset_pattern16
0x2e9020..0x2e911e: vectorized 16-bit neighborhood path
0x2e9046..0x2e9076: pblendvb operations
0x2e9080..0x2e9113: pminuw/pmaxuw chain
0x2e911e: psubusw
0x2e9b01..0x2e9b0e: writes accepted 16-bit output sample after 0x7fff mask
0x2e9b93..0x2e9b94: atomic counter add
0x2e9b99..0x2e9bb1: local buffer/descriptor cleanup
```

The call-site search inside `0x2e8cc0..0x2e9d00` found only setup, allocation,
throw, cleanup, and stack-fail calls:

```text
0x178b0
0x7720
memset_pattern16
0x7760
0xf4e0
std::string init/destroy stubs
throw/helper stubs
_Unwind_Resume
__stack_chk_fail
```

There is no nested call in this callback body to a multi-source reducer, camera
selection function, warp-vector consumer, or final blend/acceptance routine.

Safe conclusion: the helper's callback is a local one-source 16-bit Bayer/RAW
region/pixel processing kernel. It may be important to source-image preparation,
but it is not the exact upstream merge/reduction mechanism behind `src1` /
`src2`.

## Safe Conclusions

- `0x2e8680` is now statically bounded as a helper under the already identified
  `0x341770` visible-`src1` region-adapter target.
- It validates one source-domain / Bayer-image descriptor and one bit-depth
  condition.
- It prepares one destination descriptor through `0xf540`.
- It dispatches one callback object through generic executor `0x5440`.
- The callback vtable/address point is `0x659fc0`, with substantive slot
  `+0x30 = 0x2e8cc0`.
- `0x2e8cc0` is a one-source 16-bit SIMD region/pixel kernel with local buffer
  allocation and cleanup.
- This closes the specific `0x2e8680` question as a region-adapter helper, not
  as the missing reducer.

## Non-Conclusions

- Do not call `0x2e8680` a blend, reducer, C6 router, or final acceptance
  routine.
- Do not claim public algorithm names for `0x2e8680` or `0x2e8cc0`.
- Do not claim `0x2e8680` independently completed in the earlier four-zoom
  runtime probe; that probe killed at the lower virtual callsite before the
  target body ran.
- Do not infer semantic `src1` membership from this helper.
