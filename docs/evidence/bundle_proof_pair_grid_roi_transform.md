# Bundle Proof: IRAMP Pair-Grid ROI Basis and Transform

## Scope

This note proves only what the installed `libcp.dylib` shows about the IRAMP pair-grid path around `0x365960`, `0x3661b0`, `0x366c70`, and `0x374ac0`.

It proves:

- `0x365960` treats the ROI rectangle as a separate 4-int argument and resizes the output image to that ROI on the non-empty-ROI path before calling `0x3661b0`
- `0x3661b0` builds the first pair grid from that ROI rectangle plus the closure scale, aligns it to the 8-pixel lattice, and writes packed int32 `(x, y)` pairs at `0x366520..0x366523`
- `0x366b40..0x366dc7` allocates a second same-sized pair grid, reads the first grid back, bounds-checks it against an image-like object's dimensions at `+0x30/+0x34`, samples a float map, and writes transformed int32 pairs into the second grid
- `0x366dff..0x366f1c` accumulates a bbox over the valid transformed pairs and passes that block to `0x374ac0`
- `0x374ac0` clamps / intersects that block against image dimensions and then zero-fills out-of-block margins through a callback sink

It does not prove a human-readable class name for the per-level transform record.

It does not prove the final spec-ready algebra for the per-level transform fields.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- IRAMP setup + ROI path:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x365960 --count 260' -o 'disassemble --start-address 0x365e3a --count 220'`
- IRAMP pair-grid writer + consumer:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3661b0 --count 320' -o 'disassemble --start-address 0x366b00 --count 360' -o 'disassemble --start-address 0x366c50 --count 260'`
- IRAMP caller context:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ec770 --count 120'`
- Bbox/intersection helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x374ac0 --count 320'`

## Proven Facts

### 1. `0x365960` keeps the ROI rectangle separate and resizes the output image from it

- At `0x3659a8..0x3659cd`, the function proves two paired 16-byte-stride vectors must have matching counts or it throws `warpfield count does not match the source image count!`.
- At `0x365efe..0x365f0f`, `%rbx` is read as four ints:
  - `(%rbx)`
  - `0x4(%rbx)`
  - `0x8(%rbx)`
  - `0xc(%rbx)`
- At `0x365f03..0x365f0f`, those ints are used as rectangle extents:
  - width = `rect[2] - rect[0]`
  - height = `rect[3] - rect[1]`
- At `0x365f2d..0x365f3c`, the output object in `%r12` is resized through `0xf540` using that width/height pair.
- At `0x365f41..0x365f4b`, the function then calls `0x3661b0` with:
  - `%rdi = &closure`
  - `%rsi = %rbx`
  where `%rbx` is still the same 4-int ROI rectangle.

Therefore the non-empty-ROI path hands `0x3661b0` the same ROI rectangle that was just used to size the output image.

### 2. The first written pair grid is ROI-derived and 8-pixel aligned

- At `0x3661ed..0x36621c`, `0x3661b0` reads the four ROI ints from `%rsi`.
- At `0x3661e9..0x36620c`, each ROI component is multiplied by the closure scale loaded through `(%r15)->(%rax)->(%rax)`.
- At `0x366220..0x366264`, the left/top values are masked with `& -8`, while the right/bottom side goes through the visible align-up / round-up sequence before the later grid dimensions are formed.
- At `0x366307..0x366337`, the derived integer start bases are stored at:
  - `-0x43e8(%rbp)`
  - `-0x43f0(%rbp)`
- At `0x36649d..0x3664bc`, a descriptor rooted at `-0x1760(%rbp)` is allocated through `0xf540` with `edx = 8`.
- At `0x3664ce..0x366553`, that descriptor is filled as a lattice of packed int32 pairs:
  - `0x366520: movl %esi, -0x4(%rcx)`
  - `0x366523: movl %edx, (%rcx)`
- The inner loop increments `%esi` by `8` at `0x366532`.
- The outer loop advances the row counter and pointer using the same 8-byte pair stride at `0x366545..0x366551`.

Therefore the first pair grid is not arbitrary memory. It is an ROI-derived coordinate lattice built from the scaled ROI rectangle and written on an 8-pixel step.

### 3. IRAMP then builds a second same-sized transformed pair grid

- At `0x366b40..0x366b53`, a second `edx = 8` descriptor rooted at `-0x1830(%rbp)` is allocated from the same size qword `-0x1750(%rbp)`.
- At `0x366bcc..0x366c06`, the loop sets:
  - `%r15 = -0x1740(%rbp)` as the first grid's data
  - `%r12 = -0x1810(%rbp)` as the second grid's data
  - matching row strides derived from `-0x1748` and `-0x1818`
- At `0x366b92..0x366bc7`, the active per-level record contributes visible fields at:
  - `+0x48`
  - `+0x4c`
  - `+0x40`
  - `+0x10`
  - `+0x20`
  - `+0x30`
- At `0x366c70..0x366c82`, each input pair from the first grid is bounds-checked against the dimensions at `0x30(%r13)` and `0x34(%r13)`.
- At `0x366ca5..0x366cd3`, the pair is scaled by the floats at `+0x48/+0x4c`, then used to sample one float from the image-like object at `+0x40`.
- At `0x366cd8..0x366d0a`, that sampled float and the scaled coordinates are combined with the visible 16-byte vectors at `+0x10/+0x20/+0x30`.
- At `0x366d44..0x366d59`, successful results are rounded and written into the second grid as int32 pairs.
- At `0x366da0..0x366daa`, failed results write the sentinel `0x8000000080000000`.

Therefore the installed bundle shows two distinct grids:

- the first grid is the ROI-derived input lattice
- the second grid is a transformed same-sized lattice produced from the first grid through per-level image / map / transform state

### 4. The transformed-grid bbox is passed into `0x374ac0` for clipping and zero-fill handling

- At `0x366dff..0x366e42`, the loop computes min/max extents over the valid transformed pairs and rejects empty results.
- At `0x366eda..0x366f0c`, those extents are assembled into the four-int block at:
  - `-0x1420`
  - `-0x141c`
  - `-0x1418`
  - `-0x1414`
- At `0x366f12..0x366f1c`, that block is passed to `0x374ac0`.
- Inside `0x374ac0`, `0x374b0a..0x374b41` clamps / intersects against target dimensions at `0x30/+0x34`.
- At `0x374ce2..0x374cf1`, the helper calls a callback through `object->0x20->vtable[+0x30]`.
- At `0x374d70..0x374fce`, the helper uses repeated `__bzero` calls to zero-fill out-of-block regions around the clipped rectangle.

Therefore the transformed-grid bbox is not dead bookkeeping. It directly feeds the later clipped working block and margin clearing path.

## Safe Conclusion

- Proven:
  the first IRAMP pair grid is derived from the ROI rectangle argument, scaled, aligned to the 8-pixel lattice, and written at `0x366520..0x366523`.
- Proven:
  IRAMP then allocates a second same-sized pair grid and fills it by transforming the first grid through per-level image / map / vector state before bbox handling.
- Proven:
  the transformed-grid bbox is clipped and used by `0x374ac0` before callback-backed zero-fill handling.
- Still unproven:
  the exact field-level algebra and public naming for that per-level transform state.

## Consequence For Blocker Work

Future geometry work should no longer treat the pair-grid blocker as "what are these pairs at all?"

The installed bundle now proves:

- where the first grid comes from
- that it is ROI-derived
- that a second transformed grid exists
- that the transformed-grid bbox feeds the later clipped working block

The remaining geometry blocker is narrower:

- consumer-side transform formula is now proven by later evidence
- producer-side row/map calibration semantics, not the existence or basic role of the pair-grid path
