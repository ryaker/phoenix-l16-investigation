# Bundle Proof: `src1` Project-ROI Worker

## Scope

This note extends `bundle_proof_src1_payload_runtime_surfaces.md` for the deeper worker reached from the large payload ROI/process body at `0x3e2e90`.

It proves:

- `0x3e2e90` builds a `0x30`-byte callback object and installs address point `0x65f408`
- the installed callback address point contains substantive worker slot `+0x30 = 0x3e4c50`
- the visible `0x3e4c50` body is a row/range worker over one output region
- each output sample calls one projection callable through slot `+0x30`
- the visible pixel body samples one source image/cache buffer using a 4x4 float-vector neighborhood and a 64-entry stack-resident cubic weight table
- the visible output is one `vec4f` store per output pixel

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not prove a cross-camera blend body.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Callback vtable/address-point bytes:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format x --size 8 --count 20 0x65f3f0' -o 'memory read --format x --size 8 --count 20 0x65f408'`
- Worker setup and body:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e3810 --end-address 0x3e3bd0' -o 'disassemble --start-address 0x3e4c50 --end-address 0x3e52e5' -o 'disassemble --start-address 0x3e4ba0 --end-address 0x3e4c50'`
- Worker loop tail and fixed vector constant:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e52ce --end-address 0x3e5360' -o 'memory read --format f --size 4 --count 8 0x5d9a20'`

## Proven Facts

### 1. `0x3e2e90` installs callback address point `0x65f408`

- At `0x3e3b6d`, the body allocates `0x30` bytes.
- At `0x3e3b77`, the body loads the address `0x65f408`.
- At `0x3e3b7e`, it writes that address into the new callback object at `+0x00`.
- At `0x3e3b81`, it writes `-0x21c0(%rbp)` into callback field `+0x08`.
- At `0x3e3b85`, it writes `%rbx` into callback field `+0x10`.
- At `0x3e3b90`, it writes `-0x2120(%rbp)` into callback field `+0x18`.
- At `0x3e3b9b`, it writes `-0x2380(%rbp)` into callback field `+0x20`.
- At `0x3e3ba6`, it writes `-0x2030(%rbp)` into callback field `+0x28`.
- At `0x3e3bc9`, it calls generic executor/helper `0x5440` with the prepared callback state.

Therefore `0x3e2e90` constructs a concrete `0x30`-byte callback object and dispatches it through `0x5440`.

### 2. The callback address point reaches worker `0x3e4c50`

Raw memory at `0x65f408` shows:

- `0x65f408 = 0x3e4ba0`
- `0x65f410 = 0x3e4bb0`
- `0x65f418 = 0x3e4bc0`
- `0x65f420 = 0x3e4c00`
- `0x65f428 = 0x3e4c30`
- `0x65f430 = 0x3e4c40`
- `0x65f438 = 0x3e4c50`
- `0x65f440 = 0x3e5370`
- `0x65f448 = 0x3e5390`

Because `0x65f438 - 0x65f408 = 0x30`, the callback's `+0x30` slot is `0x3e4c50`.

The neighboring bodies before `0x3e4c50` are short support stubs:

- `0x3e4ba0` returns
- `0x3e4bb0` tail-calls `operator delete`
- `0x3e4bc0` allocates `0x30` bytes and copies callback fields
- `0x3e4c00` copies callback fields into a destination object
- `0x3e4c30` returns
- `0x3e4c40` tail-calls `operator delete`

The first large substantive visible body in this callback family is `0x3e4c50`.

### 3. `0x3e4c50` is a range worker over one output region

- At entry, it saves `%rdi` at `-0x1a8(%rbp)` and `%rsi` at `-0x158(%rbp)`.
- It reads row start and row end from the range object:
  - `0x3e4c80`: `ebx = *(int32 *)(range + 0x4)`
  - `0x3e4c83`: `eax = *(int32 *)(range + 0xc)`
  - `0x3e4c86..0x3e4c88`: exits if start is already past end
- It reads the horizontal range from the same object:
  - `0x3e4ce6`: inner end from `range + 0x8`
  - `0x3e4cf7`: inner start from `range + 0x0`
- The loop tail stores one output vector, increments the inner coordinate, and loops:
  - `0x3e52d5`: `movaps %xmm0, (%rcx)`
  - `0x3e52df`: increments the inner coordinate
  - `0x3e52f4`: branches back to `0x3e4d40` while inside the inner range
  - `0x3e530a..0x3e530e`: increments the row coordinate and branches back to `0x3e4cf0`

Therefore `0x3e4c50` is a row/range worker writing one SIMD vector per output sample.

### 4. Each sample uses one projection callable through slot `+0x30`

- At `0x3e4d40..0x3e4d76`, the body builds per-sample coordinate inputs.
- At `0x3e4d86`, it loads one callable pointer from `0x170(%r8,%rax)`.
- At `0x3e4d8e..0x3e4d91`, null callable throws through the later bad-function-call path.
- At `0x3e4da8`, it reads that callable object's vtable.
- At `0x3e4dbc`, it calls `*0x30(%rax)` with:
  - output pointer `-0x140(%rbp)`
  - coordinate pointer `-0x134(%rbp)`
  - coordinate pointer `-0x138(%rbp)`

Therefore the worker projects each output sample through one callable slot, not through a visible vector of source cameras.

### 5. The pixel body samples one source image/cache buffer through a 4x4 neighborhood

- The worker reads source/bounds fields through the callback object:
  - `0x3e4c8e`: callback `+0x08`
  - `0x3e4d02`: callback `+0x10`
  - `0x3e4d06`: callback `+0x18`
  - `0x3e4d40`: callback `+0x20`
- The in-bounds direct source pointer path computes a source pixel address from one buffer:
  - `0x3e4e47`: reloads callback `+0x08`
  - `0x3e4e4b`: reads stride/dimension field at `+0x18`
  - `0x3e4e5c`: adds data pointer at `+0x20`
- The clamped edge path loads a 4x4 neighborhood of `vec4f` samples:
  - first row stores to stack at `-0x130`, `-0x120`, `-0x110`, `-0x100`
  - second row stores to stack at `-0xf0`, `-0xe0`, `-0xd0`, `-0xc0`
  - third row stores to stack at `-0xb0`, `-0xa0`, `-0x90`, `-0x80`
  - fourth row stores to stack at `-0x70`, `-0x60`, `-0x50`, `-0x40`

Therefore the visible body samples one source image/cache buffer using a 4x4 SIMD neighborhood.

### 6. The weight table is stack-resident and has 64 entries

- The table-builder loop begins at `0x3e3810`.
- At `0x3e3a76`, it increments the loop index.
- At `0x3e3a7c`, it compares that index against `0x40`.
- At `0x3e3a7f`, it loops back to `0x3e3810` until 64 entries are built.
- Each iteration advances the destination pointer by `0x80` at `0x3e3a78`.
- Each iteration writes positive and negative split components using `maxps` / `minps` into stack slots around the current table pointer at `0x3e3a26..0x3e3a73`.
- The arithmetic inside the loop uses cubic terms from scalar float multiply chains before the packed writes.

Therefore the table consumed by the worker is a 64-entry stack-resident cubic weight table. This note does not assert the public kernel name of that cubic filter.

### 7. The output combine is SIMD resampling, not visible N-to-1 reduction

- At `0x3e5065..0x3e5079`, the worker masks a fractional index with `0x3f`, shifts it, and loads weights from callback `+0x28`.
- At `0x3e507d..0x3e52ba`, the worker repeatedly combines source vectors and table vectors through `mulps` and `addps`.
- At `0x3e52c1`, it multiplies by the fixed vector at `0x5d9a20`.
- Reading `0x5d9a20` as floats gives four `-0.25` values at `0x5d9a20..0x5d9a2c`.
- At `0x3e52c8..0x3e52cb`, it applies `maxps` and `addps`.
- At `0x3e52d5`, it stores one final `xmm0` vector to the output pointer.

Therefore the visible math is SIMD interpolation/resampling over one sampled source buffer plus fixed vector constants. The visible body does not expose a loop over multiple source images, multiple camera buffers, or N-to-1 contributor accumulation.

## Safe Conclusion

- Proven:
  `0x3e2e90` builds and dispatches a callback whose `+0x30` worker slot is `0x3e4c50`.
- Proven:
  `0x3e4c50` is a row/range worker that projects output coordinates through one callable and writes one `vec4f` result per output sample.
- Proven:
  the visible worker samples one source image/cache buffer with a 4x4 SIMD neighborhood and a 64-entry cubic weight table.
- Excluded under the visible installed-bundle body:
  `0x3e4c50` is not the exposed `src1` / `src2` N-to-1 reducer.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer body, its input shape, output shape, and math.

## Consequence For Blocker Work

Future anchor pre-fusion work should not reopen the large `0x3e2e90` / `0x3e4c50` ROI worker as the missing reducer unless new evidence proves a different call path with real N-to-1 input shape.

The blocker remains open, but the search boundary is narrower: the first visible payload ROI body and its dispatched worker are bounded as single-source projection / resampling surfaces.
