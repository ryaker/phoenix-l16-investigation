# Bundle Proof: `src1` Payload Provenance

## Scope

This note proves only what the installed `libcp.dylib` shows about the provenance of the payload returned by the visible `src1` lookup at `0x3e0af0`.

It proves:

- `PipelineCache+0x170/+0x178` is copied from the incoming `r8` shared-ptr-like argument in the `0x3ea7d0` constructor body
- the caller at `0x3b3145` passes the address of the `+0x6a8/+0x6b0` shared-ptr-like pair as that `r8` argument
- the raw pointer stored at `+0x6a8` is the object constructed by `0x3e02d0 -> 0x3dfcc0`
- `0x3dfcc0` initializes the first map/tree root at object `+0x18`
- `0x3dfcc0` inserts keyed nodes into that first map/tree and stores a newly allocated `0x490`-byte payload at node `+0x28`
- the `0x490`-byte payload is constructed through `0x3e2db0 -> 0x3e27a0`
- `0x3e0af0` later walks that same first map/tree by key and returns node `+0x28`

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not prove the final output math of the payload's process-level bodies.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- `PipelineCache` constructor body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ea7d0 --count 120'`
- Caller that builds and passes the backing shared pointer:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3b3000 --count 120'`
- Backing object constructor:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3dfcc0 --count 260'`
- Lookup and thunk checks:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e0af0 --count 90' -o 'disassemble --start-address 0x3e02d0 --count 20' -o 'disassemble --start-address 0x3e2db0 --count 20' -o 'disassemble --start-address 0x3eaf00 --count 20'`
- Payload constructor:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e27a0 --count 220' -o 'disassemble --start-address 0x3e2bcb --count 30'`

## Proven Facts

### 1. `0x3ea7d0` copies the incoming `r8` shared pointer into `PipelineCache+0x170/+0x178`

- At `0x3ea7e7`, the constructor copies incoming `%r8` into `%rbx`.
- At `0x3ea83a`, it reads `(%rbx)`.
- At `0x3ea83d`, it stores that raw pointer into `0x170(%r14)`.
- At `0x3ea844`, it reads `0x8(%rbx)`.
- At `0x3ea848`, it stores that control pointer into `0x178(%r14)`.
- At `0x3ea854`, it calls `std::__1::__shared_weak_count::__add_shared()` when the control pointer is non-null.

Therefore `PipelineCache+0x170/+0x178` is a copied shared-ptr-like pair from the constructor's incoming `r8` argument. The `0x3ea7d0` constructor does not itself allocate or produce the object stored there.

The same constructor immediately validates that copied object:

- `0x3ea8f5` loads `0x170(%r14)` and calls `0x3e0af0`
- `0x3ea930` calls `0x3e0b90`
- `0x3ea9b9` throws `Image cache has incorrect number of levels`
- `0x3ea9ff` throws `PipelineCache level 1 must be same as sensor ressolution`

### 2. The caller at `0x3b3145` passes the `+0x6a8/+0x6b0` pair as that `r8` argument

- At `0x3b3069`, the caller allocates `0x80` bytes.
- At `0x3b3073`, it saves that allocation in `%r13`.
- At `0x3b30b3..0x3b30b6`, it computes `%r15 = %r13 + 0x18`.
- At `0x3b30ba`, it passes `%r15` as the destination object to `0x3e02d0`.
- At `0x3b30c3`, it calls `0x3e02d0`.
- At `0x3b30c8`, it stores `%r15` into `0x6a8(%rbx)`.
- At `0x3b30d6`, it stores `%r13` into `0x6b0(%rbx)`.
- At `0x3b30fe`, it computes `%r13 = object + 0x6a8`.
- At `0x3b313b`, it moves that address into `%r8`.
- At `0x3b3145`, it calls `0x3eaf00`.
- `0x3eaf00` is a thunk that jumps to `0x3ea7d0`.

Therefore the `PipelineCache+0x170/+0x178` shared-ptr-like pair is copied from the object field pair at `+0x6a8/+0x6b0`, and the raw pointer at `+0x6a8` is the object constructed at `%r13 + 0x18` by `0x3e02d0`.

### 3. `0x3e02d0` is a thunk to the backing object constructor at `0x3dfcc0`

- `0x3e02d0` immediately jumps to `0x3dfcc0`.
- At `0x3dfcee..0x3dfd02`, `0x3dfcc0` copies an incoming shared-ptr-like pair from `%rcx` into object offsets `+0/+8`.
- At `0x3dfd07`, it computes object `+0x18`.
- At `0x3dfd0e`, it clears object `+0x18`.
- At `0x3dfd12`, it stores object `+0x18` into object `+0x10`.
- At `0x3dfd16..0x3dfd1e`, it initializes a second tree/map-like root at object `+0x30` and stores that root address at object `+0x28`.
- At `0x3dfd29..0x3dfd33`, it copies incoming dimensions into object `+0x48/+0x4c`.
- At `0x3dfd36..0x3dfd51`, it copies another incoming shared-ptr-like pair into object `+0x50/+0x58`.
- At `0x3dfd61..0x3dfd6b`, it copies `*(incoming r9 pointer)` into object `+0x60`.

Therefore the object used as `PipelineCache+0x170` is an object built by `0x3dfcc0`, with a first map/tree rooted at object `+0x18`.

### 4. `0x3dfcc0` creates the exact map payload later returned by `0x3e0af0`

- At `0x3dfd7f`, `0x3dfcc0` calls `0x1bea00` to derive a key from the incoming object at `(%r13)`.
- At `0x3dfd8d`, it calls `0x1be970` with that key to obtain an image-like object.
- At `0x3dfda0..0x3dfdb5`, it calls `0xf3350` and copies width/height-like fields into object `+0x40/+0x44`.
- At `0x3dfdd6..0x3dfe84`, it builds four dimension pairs by repeatedly appending width/height and halving with rounding.
- At `0x3dfeb9`, it calls `0x1bea00` again to derive the map key stored in `%r15d`.
- At `0x3dff63..0x3dffd1`, it walks or creates the first map/tree rooted through object `+0x18`.
- At `0x3dffd1`, it allocates a `0x30`-byte map/tree node.
- At `0x3dffde`, it stores the key into node `+0x20`.
- At `0x3dffe2`, it initializes node `+0x28` to null.
- At `0x3dfff0`, it stores the parent pointer into node `+0x10`.
- At `0x3dfff4`, it links the node into the tree.
- At `0x3e0019`, it calls `0xdb240` as tree insert/balance support.
- At `0x3e0026`, it allocates a `0x490`-byte payload.
- At `0x3e005d`, it calls `0x3e2db0` to construct that payload.
- At `0x3e0062`, it reads the old node payload at `+0x28`.
- At `0x3e0066`, it stores the newly constructed payload into node `+0x28`.

Therefore the payload pointer returned by `0x3e0af0` is produced inside `0x3dfcc0`, allocated as `0x490` bytes, constructed through `0x3e2db0`, and stored in the first map/tree node field `+0x28`.

### 5. `0x3e0af0` returns that first map/tree node payload

- At `0x3e0afa`, `0x3e0af0` reads `(%rbx)` and calls `0x1bea00` to derive the lookup key.
- At `0x3e0b02`, it starts the tree walk from `0x18(%rbx)`.
- At `0x3e0b18..0x3e0b27`, it compares the lookup key against node `+0x20`.
- At `0x3e0b2e`, it returns node `+0x28`.
- At `0x3e0b44`, the failure path throws `map::at:  key not found`.

This is the same first map/tree rooted at object `+0x18` that `0x3dfcc0` initializes and populates.

### 6. `0x3e2db0` is a thunk to the `0x490`-byte payload constructor at `0x3e27a0`

- `0x3e2db0` immediately jumps to `0x3e27a0`.
- At `0x3e27d0..0x3e27d7`, `0x3e27a0` writes a vtable/address pointer into payload offset `+0`.
- At `0x3e27db`, it writes `0` to payload `+0xf4`.
- At `0x3e27e6`, it initializes the subobject at payload `+0xf8`.
- At `0x3e2800..0x3e2821`, it clears pointer/function-like slots at payload `+0x170`, `+0x1a0`, `+0x1d0`, and `+0x200`.
- At `0x3e282c..0x3e2866`, it constructs four subobjects at payload `+0x210`, `+0x2b0`, `+0x350`, and `+0x3f0`.
- At `0x3e286b..0x3e2879`, it loads an incoming object through `%r8` and calls `0x1be970` with the key in `%r15d`.
- At `0x3e288a..0x3e28a2`, it checks the returned object and branches to an explicit `ReferenceImageCache not implemented for mono camera!` error if that check fails.
- At `0x3e28a8..0x3e28c5`, it validates returned level-0 dimensions against payload `+0xa8/+0xac` and branches to `ReferenceImageCache requested with incorrect level 0 size!` on mismatch.
- At `0x3e28cb..0x3e2a26`, it conditionally calls `0x3f6170`, stores returned descriptor fields into payload `+0xf8..+0x140`, and sets up callable/function-like slots through repeated calls to `0x3e55f0`.
- At `0x3e2a26`, it writes byte `+0xf0 = 0` when the incoming optional object is absent.
- At `0x3e2aeb` and `0x3e2afb`, it writes byte `+0xf0 = 1` when the callable/function-like slots are installed.
- At `0x3e2b03..0x3e2b2a`, it calls `0x3d0120` with payload `+0x10` and a stack callable object.

Therefore the payload constructor is cache/level/setup-oriented and is guarded by explicit `ReferenceImageCache` error strings. The constructor path does not, by itself, expose an N-to-1 image reducer.

## Bounded Conclusion

The visible `src1` payload provenance is now bounded to this chain:

1. caller constructs object at `%r13 + 0x18` by `0x3e02d0 -> 0x3dfcc0`
2. caller stores that object/control pair at `+0x6a8/+0x6b0`
3. caller passes address of `+0x6a8` as `r8` to `0x3eaf00 -> 0x3ea7d0`
4. `0x3ea7d0` copies the pair into `PipelineCache+0x170/+0x178`
5. `0x3dfcc0` builds a first map/tree rooted at the object `+0x18`
6. `0x3dfcc0` inserts a keyed node and stores a `0x490`-byte payload constructed by `0x3e2db0 -> 0x3e27a0` into node `+0x28`
7. `0x3e0af0` later walks the same map/tree and returns node `+0x28`

This closes the narrower provenance question left by [bundle_proof_src1_visible_read_path.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_visible_read_path.md).

It does not close the parity blocker. The exact `src1` / `src2` N-to-1 reducer body, input shape, output shape, and math remain unproven.
