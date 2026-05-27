# Bundle Proof: `src1` / `src2` Visible Wrapper Layer

## Scope

This note proves only what the installed `libcp.dylib` exposes about the first visible `src1` / `src2` wrapper layer.

It does not prove the exact upstream N-to-1 reducer.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Constructor / install path:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3eb3c0 --count 80'`
- Second wrapper store:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3eb533 --count 40'`
- First visible wrapper body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ecc10 --count 120'`
- Second visible wrapper body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ecd80 --count 80'`
- Supporting callee body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d01b0 --count 120'`
- Vtable bytes:
  `xxd -g 8 -U -s 0x65f668 -l 0x100 /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

## Proven Facts

### 1. `initResAmp` constructs two wrapper objects and installs them into `PipelineCache`

- At `libcp+0x3eb4d1`, the first constructed object stores `PipelineCache*` at `+0x28`.
- At `libcp+0x3eb4d5` and `libcp+0x3eb4d8`, that same object stores width and height at `+0x50` and `+0x54`.
- At `libcp+0x3eb4df`, the inner pointer `rsi = rax + 0x20` is written to `PipelineCache+0x238`.
- At `libcp+0x3eb549`, the second constructed object again stores `PipelineCache*` at `+0x28`.
- At `libcp+0x3eb54d` and `libcp+0x3eb550`, the second object stores width and height at `+0x50` and `+0x54`.
- At `libcp+0x3eb557`, the second inner pointer is written to `PipelineCache+0x248`.
- Therefore `src1` and `src2` are installed wrapper-owned objects created during `initResAmp`; they are not raw camera-image pointers.
- Follow-up four-zoom runtime proof in [lldb_pipelinecache_level_vector_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_pipelinecache_level_vector_four_zoom.md) identifies the source of those wrapper dimensions: both wrappers read vector entry `1 = 4160x3120` from the packed level-vector begin pointer stored at `PipelineCache+0x8`.

### 2. The inner wrapper pointers are subobjects whose `+0x8` field is `PipelineCache*`

- The first wrapper allocation writes:
  `0x20(%rax) = some class-local header pointer` and `0x28(%rax) = PipelineCache*`.
- The inner pointer stored into `PipelineCache+0x238` is `rsi = rax + 0x20`.
- Therefore when the visible wrapper body later receives `rdi = PipelineCache+0x238`, its `0x8(%rdi)` field resolves to the stored `PipelineCache*`.
- The second wrapper allocation repeats the same layout:
  `0x20(%rax) = class-local header pointer`, `0x28(%rax) = PipelineCache*`, then stores `rax + 0x20` into `PipelineCache+0x248`.
- Therefore both visible wrapper bodies are not abstract detached callables; they are concrete views back onto `PipelineCache`.

### 3. The installed-bundle vtable regions for those wrappers are recoverable

- The vtable region at `0x65f668` contains the pointer sequence:
  `0x3ecb80, 0x3ecb90, 0x3ecba0, 0x3ecbd0, 0x3ecbf0, 0x3ecc00, 0x3ecc10, 0x3eccc0, 0x3ecce0, ...`
- The vtable region at `0x65f6e8` contains the pointer sequence:
  `0x3eccf0, 0x3ecd00, 0x3ecd10, 0x3ecd40, 0x3ecd60, 0x3ecd70, 0x3ecd80, 0x3ece10, 0x3ece30, ...`
- This is enough to re-anchor the wrapper investigation on the shipped bundle instead of relying on older slot assumptions.

### 4. The first visible wrapper bodies map to concrete `PipelineCache` backing fields

- `libcp+0x3ecc10` begins with:
  `movq 0x8(%rdi), %rax` then `movq 0x170(%rax), %rdi`
- Because `0x8(%rdi)` is the stored `PipelineCache*`, this visible body immediately resolves to `PipelineCache+0x170`.
- The shipped `PipelineCache` constructor copies its incoming shared object into `0x170(%r14)` / `0x178(%r14)` at `libcp+0x3ea83d..0x3ea848`.
- Existing admitted registry work identifies `PipelineCache+0x170` as the `ReferenceImageCache` shared pointer.
- `libcp+0x3ecd80` begins with:
  `movq 0x8(%rdi), %rdi` then `callq 0x3ebb80`
- Because `0x8(%rdi)` again resolves to `PipelineCache*`, the second visible wrapper body dispatches directly on the `PipelineCache` instance.

### 5. The visible `src2` path is bounded to `PipelineCache+0x1e0` hot path and `PipelineCache+0x1d8` fallback

- `libcp+0x3ebb80` starts by loading `movq 0x1e0(%r14), %r12`.
- If that pointer is non-null, the body continues through a state-driven descriptor / table / executor orchestration path.
- If `PipelineCache+0x1e0` is null, the body falls back at `libcp+0x3ebd8a`.
- That fallback validates dimensions via `PipelineCache+0x170`, then loads `movq 0x1d8(%r14), %rdi` and calls `*0x18(%rax)` on the object stored there.
- Therefore the visible `src2` side is not an unbounded mystery call chain:
  it is statically bounded to `PipelineCache+0x1e0` on the hot path and `PipelineCache+0x1d8` on the cold path.

### 6. `PipelineCache+0x1d8` is the `FusionCacheBayer` object

- In the `PipelineCache` constructor, a fresh `0x138`-byte object is allocated and initialized via `libcp+0x406960`, then stored through the local `&PipelineCache+0x1d8` holder at `libcp+0x3eab58`.
- `libcp+0x406960` is a thunk into `libcp+0x4064c0`.
- `libcp+0x4064ed` writes the vtable pointer for that object at offset `0`.
- The shipped vtable bytes at `0x6600c0` decode to:
  `0x407950, 0x4079a0, 0x406970, 0x406a10, ...`
- Existing shipped-bundle proof already identifies that same vtable family as `lt::FusionCacheBayer`, with `0x406970` and `0x406a10` as the relevant methods.
- Therefore `PipelineCache+0x1d8` is the `FusionCacheBayer` object used by the visible fallback path.

### 7. `PipelineCache+0x1e0` is a separately constructed state object, not the hidden reducer body

- If `PipelineCache+0x180` is non-null, the constructor allocates `0x50` bytes, initializes them via `libcp+0x1449f0`, and stores the result to `PipelineCache+0x1e0`.
- If `PipelineCache+0x180` is null, the constructor throws:
  `"Cannot process undistortion without Stereo!"`
- `libcp+0x1449f0` initializes a float-backed state block and allocates a `0x4000`-byte backing store.
- This is structurally distinct from the `FusionCacheBayer` object at `+0x1d8`.
- Therefore the visible `src2` hot path is already bounded to a separately built state object rather than an already-proven multi-camera reducer.

### 8. The first visible wrapper bodies do not by themselves close the reducer blocker

- `libcp+0x3ecc10` begins by loading one stored object pointer from `0x8(%rdi)`, then loading state from `0x170(%rax)`, then calling:
  `0x3e0af0`, `0x3d01b0`, and `0x3edb80`
- `libcp+0x3ecd80` begins by loading one stored object pointer from `0x8(%rdi)`, then calling:
  `0x3ebb80` and `0x3edb80`
- The visible `0x3ecc10` body therefore exposes stored-state plumbing and helper dispatch, not a directly visible IRAMP-like multi-source argument shape.
- The visible `0x3ecd80` body is even narrower: it is a wrapper-stage call into `0x3ebb80` followed by `0x3edb80`.

### 9. The second visible body now has repo-local static boundary proof

- [bundle_lldb_src2_state_3ebb80_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_src2_state_3ebb80_static.md) replaces the older scratch citation for `libcp+0x3ebb80`.
- That repo-local proof shows `libcp+0x3ecd80` calls `0x3ebb80` at `libcp+0x3ecda8`, then calls the one-image `sqrt(max())` normalization body `0x3edb80` at `libcp+0x3ecdc7`.
- It also bounds `0x3ebb80` to `PipelineCache+0x1e0` state, `PipelineCache+0x1d8` fallback/source-descriptor plumbing, descriptor validation, a 64-entry scalar table, and generic tiled executor dispatch.
- Therefore the second visible wrapper body is not itself the proven upstream `src1` / `src2` merge/reduction closure.
- The exact semantic `src2` contents and final callable math behind the generic executor dispatch remain unproven.

## Safe Conclusion

- Proven:
  `src1` and `src2` are installed wrapper objects.
- Proven:
  the installed-bundle vtable regions for those wrappers are known.
- Proven:
  the visible wrapper layer maps to concrete `PipelineCache` backing fields: `+0x170`, `+0x1e0`, and fallback `+0x1d8`.
- Proven:
  `PipelineCache+0x1d8` is the `FusionCacheBayer` object used by the visible fallback path.
- Proven:
  the first visible wrapper bodies at `0x3ecc10` and `0x3ecd80` are not enough to claim the exact pre-fusion reducer has been found.
- Proven:
  the visible `src2` body `0x3ecd80 -> 0x3ebb80 -> 0x3edb80` is now bounded by repo-local installed-bundle evidence, without relying on the old scratch citation.
- Still unproven:
  exact reducer body, exact inputs, exact outputs, exact math.

## Consequence For Blocker Work

Future decode should start from the proven constructor stores at `0x3eb4df` and `0x3eb557`, use the installed vtable regions at `0x65f668` and `0x65f6e8`, and then move upstream of the now-identified backing fields instead of treating the visible wrapper bodies as reducer closure.
