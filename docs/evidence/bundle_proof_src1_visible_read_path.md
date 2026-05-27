# Bundle Proof: `src1` Visible Read Path

## Scope

This note proves only what the installed `libcp.dylib` shows for the visible `src1` read path after the first wrapper resolves to `PipelineCache+0x170`.

It proves:

- `0x3ecc10` resolves through `PipelineCache+0x170`, calls `0x3e0af0`, then reads a level/ROI from the returned payload through `0x3d01b0`
- `0x3e0af0` is a map/tree lookup that returns one stored payload pointer
- `0x3d01b0` is a checked single-source level/ROI tile-read dispatcher
- `0x3edb80` is a one-image square-root normalization/copy stage
- `0x3ecd80` uses the same final `0x3edb80` normalization after the already-bounded `0x3ebb80` path

It does not prove the producer of the payloads returned by `0x3e0af0`.

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Visible `src1` / `src2` wrapper bodies:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ecc10 --count 180' -o 'disassemble --start-address 0x3ecd80 --count 120'`
- `src1` backing lookup:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0af0 --count 500' -o 'disassemble --start-address 0x3e0b90 --count 260'`
- Level/ROI read and normalization callees:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d01b0 --count 360' -o 'disassemble --start-address 0x3edb80 --count 420'`

## Proven Facts

### 1. `0x3ecc10` resolves `src1` through `PipelineCache+0x170`

- At `0x3ecc23`, the visible wrapper body loads `0x8(%rdi)` into `%rax`.
- Prior wrapper proof shows this field is the wrapper-owned `PipelineCache*`.
- At `0x3ecc27`, the body loads `0x170(%rax)` into `%rdi`.
- At `0x3ecc3d`, the body calls `0x3e0af0`.
- At `0x3ecc42`, the body adds `0x10` to the returned pointer.
- At `0x3ecc4c..0x3ecc55`, the body calls `0x3d01b0` with the returned pointer plus `0x10`, a stack output descriptor, the incoming request geometry, and `ecx = 0`.
- At `0x3ecc71..0x3ecc74`, the body calls `0x3edb80` with the requested output and the stack intermediate descriptor.
- At `0x3ecc79`, the body destroys the intermediate descriptor through `0xf4e0`.

Therefore the visible `src1` wrapper body is not itself a multi-camera reducer. It is a lookup, level-0 source read, and final normalization path.

### 2. `0x3e0af0` is a map/tree lookup returning one stored payload

- At `0x3e0afa`, the body loads `(%rbx)` and calls `0x1bea00`, producing the lookup key in `%eax`.
- At `0x3e0b02`, the tree walk starts from the pointer at `0x18(%rbx)`.
- At `0x3e0b13..0x3e0b27`, the body compares the lookup key to the node field at `0x20(%rcx)`.
- At `0x3e0b2e`, a matching node returns the payload pointer at `0x28(%rcx)`.
- At `0x3e0b37..0x3e0b72`, the failure path throws the explicit string `map::at:  key not found`.

Therefore `0x3e0af0` proves lookup semantics only. It does not expose the producer or math behind the returned stored payload.

### 3. `0x3d01b0` is a checked single-source level/ROI tile-read dispatcher

- At `0x3d01e1..0x3d01fa`, the body validates the requested level against a vector-like range at source object offsets `+0x8..+0x10`.
- At `0x3d0200..0x3d022d`, the body validates the requested ROI against the selected level dimensions.
- At `0x3d024f..0x3d0259`, the body resizes the output descriptor through `0xf540`.
- At `0x3d0265..0x3d02e5`, the body derives tile-coordinate bounds from the selected source object and requested ROI.
- At `0x3d0333`, the body calls `0x3d45a0` to allocate a tile-coordinate vector.
- At `0x3d0374..0x3d03ad`, the body builds a 0x30-byte closure containing the source object pointer, selected level pointer, ROI/tile descriptors, and tile-coordinate vector.
- At `0x3d03c3..0x3d03d1`, the body dispatches that closure through `0x5440`.
- At `0x3d0408..0x3d042b`, the body dispatches follow-up work through `0x5670`.
- The visible exception strings are `Requested level is not supported!`, `Requested ROI is out-of-bounds!`, and `No tiles in ROI!`.

Therefore `0x3d01b0` proves a single-source level/ROI read path. It does not expose a vector-of-cameras input shape or an N-to-1 reducer loop.

### 4. `0x3edb80` is a one-image square-root normalization/copy stage

- At `0x3edb9f..0x3edbae`, the body reads width and height from the input image descriptor.
- At `0x3edbb1..0x3edbba`, the body resizes the output descriptor through `0xf540`.
- At `0x3edbc5..0x3ede9c`, the body loops over output height and width.
- The inner SIMD path repeatedly uses `maxps`, then `sqrtps`, then stores the result with `movaps`.

Therefore `0x3edb80` is a one-image normalization/copy stage. It is not a multi-input merge reducer.

### 5. `0x3ecd80` reaches the same final one-image normalization

- At `0x3ecda8`, the visible `src2` body calls the already-bounded `0x3ebb80` path.
- At `0x3ecdc4..0x3ecdc7`, it calls the same final `0x3edb80` normalization body.
- Existing wrapper proof already bounds `0x3ebb80` to `PipelineCache+0x1e0` on the hot path and `PipelineCache+0x1d8` fallback.

Therefore this new proof does not reopen `src2` as the reducer. It only adds that the visible `src2` body also ends in the same one-image square-root normalization stage.

## Bounded Conclusion

The visible `src1` read path is now bounded to:

1. wrapper-owned `PipelineCache*`
2. `PipelineCache+0x170`
3. map/tree lookup at `0x3e0af0`
4. checked single-source level/ROI tile read at `0x3d01b0`
5. one-image square-root normalization at `0x3edb80`

The exact reducer blocker remains open. This proof moves the remaining question to the provenance and construction of the backing payloads returned by `0x3e0af0`; it does not close that question.
