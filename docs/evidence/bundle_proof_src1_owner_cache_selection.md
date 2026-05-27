# Bundle Proof: `src1` Owner Cache Selection

## Scope

This note extends the `src1` / `src2` blocker chain one layer above the `PipelineCache+0x170` provenance proof.

It proves:

- the owner object constructs and stores the `+0x6a8/+0x6b0` pair that later feeds `PipelineCache+0x170/+0x178`
- the same owner constructs and stores a cache pair at `+0x688/+0x690` through the `0x3eaf00 -> 0x3ea7d0` constructor path
- that `+0x688` construction passes `&owner+0x6a8` and `&owner+0x678` into the `0x3ea7d0` constructor path
- the runtime read selector at `0x3b0740` chooses between `owner+0x688` and `owner+0x6b8`, then calls `0x3d0650`
- `0x3d0650` is a one-cache level/ROI read and rescale dispatcher, not an exposed N-to-1 reducer

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not decode every field in the owner object.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Owner construction / store region:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3b2fc0 --end-address 0x3b3310'`
- Runtime selector and helper:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3b0740 --end-address 0x3b07b8' -o 'disassemble --start-address 0x3f06d0 --end-address 0x3f0720' -o 'disassemble --start-address 0x3c6f80 --end-address 0x3c7000'`
- Selected read target:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d0650 --end-address 0x3d0b60'`
- Resampling setup target:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x36f800 --end-address 0x36fb80'`
- Owner cleanup / field family:
  `sed -n '903900,905300p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`

## Proven Facts

### 1. The owner stores the upstream object pair at `+0x6a8/+0x6b0`

- At `0x3b3069`, the owner path allocates `0x80` bytes.
- At `0x3b3073`, it saves the allocation in `%r13`.
- At `0x3b30b3..0x3b30b6`, it computes inner pointer `%r15 = allocation + 0x18`.
- At `0x3b30ba`, it passes that inner pointer as `%rdi` to `0x3e02d0`.
- At `0x3b30c3`, it calls `0x3e02d0`.
- At `0x3b30c8`, it stores the inner pointer at `owner+0x6a8`.
- At `0x3b30d6`, it stores the allocation/control pointer at `owner+0x6b0`.

This is the same `+0x6a8/+0x6b0` pair proven in `bundle_proof_src1_payload_provenance.md` as the source copied into `PipelineCache+0x170/+0x178`.

### 2. The owner stores a cache pair at `+0x688/+0x690`

- At `0x3b30ee`, the owner path allocates `0x2b0` bytes.
- At `0x3b30fe`, it computes `%r13 = owner + 0x6a8`.
- At `0x3b311b`, it computes inner pointer `%rbx = allocation + 0x20`.
- At `0x3b3123`, it passes that inner pointer as `%rdi`.
- At `0x3b313b`, it passes `%r8 = owner + 0x6a8`.
- At `0x3b313e`, it passes `%r9 = owner + 0x678`.
- At `0x3b3145`, it calls `0x3eaf00`, the thunk to `0x3ea7d0`.
- At `0x3b3151`, it stores the inner pointer at `owner+0x688`.
- At `0x3b3161`, it stores the allocation/control pointer at `owner+0x690`.

Therefore the owner constructs the `+0x688/+0x690` cache pair from the previously built `+0x6a8/+0x6b0` source pair and the `+0x678/+0x680` source/helper pair.

### 3. The `+0x678/+0x680` pair is also constructed in the same owner setup path

- At `0x3b2fde`, the path allocates `0x4d0` bytes.
- At `0x3b3011`, it calls `0x3f46d0` to initialize that allocation.
- At `0x3b3038`, it stores the initialized object pointer at `owner+0x678`.
- At `0x3b3046`, it stores the control pointer at `owner+0x680`.
- At `0x3b3092..0x3b3099`, it saves `owner+0x678` for the later `0x3eaf00` call.

This proves the `+0x678` argument passed into `0x3ea7d0` is another owner-held constructed object pair, not an unbounded hidden argument.

### 4. The owner cleanup path treats these as shared-ptr-like pairs

The cleanup path releases and zeroes the same field-family:

- `0x3b1b38..0x3b1b59`: releases `owner+0x688/+0x690`
- `0x3b1b59..0x3b1b74`: releases `owner+0x6a8/+0x6b0`
- `0x3b1b74..0x3b1b95`: releases `owner+0x698/+0x6a0`
- `0x3b1b95..0x3b1bb0`: releases `owner+0x6b8/+0x6c0`
- `0x3b1bb0..0x3b1bd1`: releases `owner+0x678/+0x680`

Therefore these offsets are a coherent owner-held cache/helper family.

### 5. Runtime read dispatch chooses between `owner+0x688` and `owner+0x6b8`

The runtime selector at `0x3b0740`:

- calls `0x3c6f80` at `0x3b0767`
- reads `owner+0x6b8` at `0x3b0776`
- calls `0x3f06d0` at `0x3b077d`
- compares that result with the first float copied by `0x3c6f80`
- selects `owner+0x6b8` at `0x3b0788` when the `0x3f06d0` result is greater
- otherwise selects `owner+0x688` at `0x3b0791`
- calls `0x3d0650` at `0x3b07a4` with the selected cache and the caller's output / ROI / level arguments

Therefore this visible runtime surface is a two-cache selector feeding a common read helper.

### 6. The selector helpers are scalar/state helpers

- `0x3c6f80` locks `object+0x8`, copies bytes from object fields `+0x48..+0x7f` into the output, then unlocks.
- `0x3f06d0` computes one scalar:
  `float(owner+0x88) * float(owner+0x84) / float(owner+0x80)`.

These helpers do not expose image buffers, camera vectors, or N-to-1 reduction math.

### 7. `0x3d0650` is a one-cache level/ROI read and rescale dispatcher

- At `0x3d0670..0x3d0692`, it computes ROI width/height and calls `0xf540` to size the output.
- If the level argument is non-negative, `0x3d0697..0x3d070c` uses that level index directly.
- If the level argument is negative, `0x3d06a4..0x3d0708` chooses one level by comparing per-level dimensions stored in the selected cache object.
- If the selected level dimensions match the requested ROI dimensions, `0x3d0724..0x3d072d` calls `0x3d01b0` once and returns through the common exit.
- If the dimensions differ, `0x3d0737..0x3d0848` computes a transformed ROI, prepares one temporary image descriptor, and calls `0x3d01b0` once into that temporary.
- The dimension-mismatch path then calls `0x36f800` at `0x3d08ce`, passing the temporary, final output, offset pair, and scale pair.

Therefore the visible body of `0x3d0650` dispatches one selected cache through one level/ROI read path, with a rescale step when needed.

### 8. The inspected `0x36f800` entry is a resampling worker setup surface

- At `0x36f890..0x36fa9d`, it builds a 64-entry stack-resident cubic weight table.
- At `0x36fad1..0x36fb1f`, it allocates a `0x30`-byte callback, writes input/output/offset/scale pointers into that callback, and dispatches it through generic executor/helper `0x5440`.

This note does not decode the full worker under `0x36f800`. The inspected entry shape is resampling setup, not a visible N-to-1 camera reducer.

## Safe Conclusion

- Proven:
  the `+0x6a8/+0x6b0` source pair is built and stored by the owner immediately before the `+0x688/+0x690` cache pair.
- Proven:
  the `+0x688/+0x690` cache construction passes `&owner+0x6a8` and `&owner+0x678` into `0x3ea7d0`.
- Proven:
  runtime read dispatch chooses one cache, `owner+0x688` or `owner+0x6b8`, and calls `0x3d0650`.
- Proven:
  `0x3d0650` is a one-cache level/ROI read and rescale dispatcher.
- Excluded under the visible installed-bundle body:
  the owner cache-selection layer is not the exposed `src1` / `src2` N-to-1 reducer.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer body, input shape, output shape, and math.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work should not reopen the owner `+0x688/+0x6a8/+0x6b8` cache-selection surface as reducer closure.

The useful next search boundary is now upstream of the owner cache family: decode what the `+0x678` source/helper object and the `+0x6b8` alternate cache contain, and look only for surfaces with real N-to-1 input shape or reduction math.
