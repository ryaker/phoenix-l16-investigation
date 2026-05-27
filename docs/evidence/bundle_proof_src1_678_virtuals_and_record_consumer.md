# Bundle Proof: `src1` `+0x678` Virtual Targets And Record Consumer

## Scope

This note extends `bundle_proof_src1_678_constructor_runtime_surface.md`.

It proves:

- the `+0x40` virtual targets reached by `0x267e80` and `0x267fb0` are direct setter methods on the newly pushed layer object
- the `+0x90` virtual targets reached through `0x268480` / `0x2684a0` are direct pointer accessors for the two layer classes inspected here
- the `0x3f8b30` method consumes the record and byte buffer materialized by `0x3f7ec0` and writes them through a caller-supplied sink
- the `StereoLayer<false>::runPass(int)` action vtable `0x667cc8` has `operator()` at `0x276790`

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not decode the full math inside `0x276860` or `0x277e70`, the two heavy bodies reached from `0x276790`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Vtable reads:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "memory read --format x --size 8 --count 24 0x667ae0" -o "memory read --format x --size 8 --count 24 0x658eb0" -o "memory read --format x --size 8 --count 16 0x667cc8" -o "memory read --format x --size 8 --count 16 0x667d50" -o "memory read --format x --size 8 --count 16 0x65f900"`
- Typeinfo reads:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "memory read --format x --size 8 --count 8 0x667ab0" -o "memory read --format c --size 1 --count 96 0x5dad90" -o "memory read --format x --size 8 --count 8 0x658f50" -o "memory read --format c --size 1 --count 96 0x5db2c0" -o "memory read --format c --size 1 --count 112 0x5db000" -o "memory read --format c --size 1 --count 112 0x5db0b0"`
- Layer push helpers:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "disassemble --start-address 0x267e80 --end-address 0x267fb0" -o "disassemble --start-address 0x267fb0 --end-address 0x268090"`
- Selected virtual targets:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "disassemble --start-address 0x26bbd0 --end-address 0x26bd20" -o "disassemble --start-address 0x26fb50 --end-address 0x26fc10" -o "disassemble --start-address 0x26a920 --end-address 0x26aa20" -o "disassemble --start-address 0x26b590 --end-address 0x26b620"`
- Vector access helpers:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "disassemble --start-address 0x268480 --end-address 0x2684d0" -o "disassemble --start-address 0x2684a0 --end-address 0x268510"`
- `StereoLayer<false>::runPass(int)` action vtable and visible branch head:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "disassemble --start-address 0x276790 --end-address 0x276980" -o "disassemble --start-address 0x276860 --end-address 0x276f80" -o "disassemble --start-address 0x277e70 --end-address 0x278360"`
- Record consumer:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o "disassemble --start-address 0x3f8b30 --end-address 0x3f8e80"`

## Proven Facts

### 1. The `StereoLayer<false>` vtable used by `0x267e80` is at address point `0x667ae0`

- `0x26b761` installs address point `0x667ae0` in the `0x310`-byte object constructed by `0x26b750`.
- The vtable prefix at `0x667ad8` points to typeinfo `0x667ab0`.
- The typeinfo name pointer at `0x667ab8` is `0x5dad90`.
- The string at `0x5dad90` is `N2lt11StereoLayerILb0EEE`.

The direct vtable bytes at `0x667ae0` include:

| Slot | Target |
|---|---:|
| `+0x40` | `0x26bbd0` |
| `+0x88` | `0x26bcf0` |
| `+0x90` | `0x26fb50` |
| `+0x98` | `0x26fb60` |

### 2. `0x267e80` tail-calls `StereoLayer<false>` slot `+0x40`, which is only a setter

`0x267e80` does this sequence after constructing and pushing the new object:

- `0x267f12` loads the vector end pointer.
- `0x267f16` loads the just-pushed object from `end - 8`.
- `0x267f1a..0x267f1d` loads the object's vtable slot `+0x40`.
- `0x267f21..0x267f29` computes the newly pushed index.
- `0x267f35` tail-jumps to the slot target with that index in `esi`.

For `StereoLayer<false>`, slot `+0x40` is `0x26bbd0`.

`0x26bbd0`:

- writes `esi` to `this+0x8`
- returns

This selected `+0x40` target is not a reducer.

### 3. `StereoLayer<false>` slot `+0x90` is a pointer accessor

`0x2684a0` bounds-checks a vector and calls the selected object's slot `+0x90`.

For `StereoLayer<false>`, slot `+0x90` is `0x26fb50`.

`0x26fb50`:

- returns `this+0x2a8`

`0x268480` also calls slot `+0x90` on the last vector object. For `StereoLayer<false>`, this reaches the same `this+0x2a8` accessor.

This selected `+0x90` target is not a reducer.

### 4. `0x267e80` throws the SGM-after-upsample error only when the previous layer's slot `+0x88` returns `1`

The guard is exact:

- `0x267e9d..0x267ea4` calls the previous vector element's slot `+0x88`.
- `0x267eaa..0x267ead` compares the return value to `1`.
- if equal, `0x267f4a..0x267f96` constructs and throws the string `SGM after upsampled depth is not allowed.`
- otherwise, `0x267eb3` allocates the new `0x310`-byte object.

For `StereoLayer<false>`, slot `+0x88` is `0x26bcf0`, which returns `0`.

### 5. The `UpsampleLayer` vtable used by `0x267fb0` is at address point `0x658eb0`

- `0x26a894` installs address point `0x658eb0` in the `0xf0`-byte object constructed by `0x26a890`.
- The vtable prefix at `0x658ea8` points to typeinfo `0x658f50`.
- The typeinfo name pointer at `0x658f58` is `0x5db2c0`.
- The string at `0x5db2c0` is `N2lt13UpsampleLayerE`.

The direct vtable bytes at `0x658eb0` include:

| Slot | Target |
|---|---:|
| `+0x40` | `0x26a920` |
| `+0x88` | `0x26b610` |
| `+0x90` | `0x26b590` |
| `+0x98` | `0x26b5a0` |

### 6. `0x267fb0` tail-calls `UpsampleLayer` slot `+0x40`, which is only a setter

`0x267fb0` constructs and pushes a `0xf0`-byte object, then:

- `0x26803a` loads the vector end pointer.
- `0x26803e` loads the just-pushed object from `end - 8`.
- `0x268042..0x268045` loads the object's vtable slot `+0x40`.
- `0x268049..0x268051` computes the newly pushed index.
- `0x26805d` tail-jumps to the slot target with that index in `esi`.

For `UpsampleLayer`, slot `+0x40` is `0x26a920`.

`0x26a920`:

- writes `esi` to `this+0x30`
- returns

This selected `+0x40` target is not a reducer.

### 7. `UpsampleLayer` slot `+0x90` is a pointer accessor

For `UpsampleLayer`, slot `+0x90` is `0x26b590`.

`0x26b590`:

- returns `this+0x90`

This selected `+0x90` target is not a reducer.

### 8. `UpsampleLayer` slot `+0x88` returns `1`

For `UpsampleLayer`, slot `+0x88` is `0x26b610`.

`0x26b610`:

- returns integer `1`

Together with the `0x267e80` guard, this proves the visible meaning of that guard branch: adding a `StereoLayer<false>` after an upsample layer triggers the `SGM after upsampled depth is not allowed.` throw path.

### 9. The `StereoLayer<false>::runPass(int)` action vtable at `0x667cc8` has operator body `0x276790`

The raw vtable bytes at `0x667cc8` include:

| Slot | Target |
|---|---:|
| `+0x30` | `0x276790` |
| `+0x38` | `0x276830` |
| `+0x40` | `0x276850` |

The associated typeinfo name at `0x5db000` is:

`NSt3__110__function6__funcIZN2lt11StereoLayerILb0EE7runPassEiEUlRKNS2_4Vec2IiEEiE_NS_9allocatorIS9_EEFvS6_iEEE`

`0x26df30..0x26df86` builds a pair of function objects and calls `0x5860`:

- `0x26df30` installs vtable/address point `0x667cc8` into a local function object.
- `0x26df5d` installs vtable/address point `0x667d50` into a second function object.
- `0x26df86` calls `0x5860` with both function objects.

The companion vtable `0x667d50` has slot `+0x30 = 0x279ac0`; its typeinfo name at `0x5db0b0` is the bool-returning `StereoLayer<false>::runPass(int)` lambda:

`NSt3__110__function6__funcIZN2lt11StereoLayerILb0EE7runPassEiEUlRKNS2_4Vec2IiEEE_NS_9allocatorIS9_EEFbS6_EEE`

This proves the action entry address `0x276790`.

It does not prove the full action math.

### 10. `0x276790` is only bounded through its first dispatch branch here

`0x276790`:

- loads a captured object from `function+0x8`
- calls a callable at `object+0xb0` if present and returns early when that callable returns nonzero
- reads `object+0x74`, the caller's first integer argument, and a pointer from the action function object
- if `object+0xc == 8`, tail-jumps to `0x276860`
- otherwise tail-jumps to `0x277e70`

The heads of `0x276860` and `0x277e70` are large image/level-processing bodies:

- both copy shared-ptr-like vectors from `this+0x240/+0x248`
- both allocate and zero a temporary buffer sized from `this+0x23c`
- both call `0x275630` after assembling vectors and object fields
- both continue into long loops over dimension and level-like state

This proof records those branch targets only. It does not classify the math inside either heavy body.

### 11. `0x3f8b30` is a consumer of `0x3f7ec0` output, not the missing reducer

The `StereoAsyncAPI` vtable at `0x65f900` contains:

| Slot | Target |
|---|---:|
| `+0x18` | `0x3f8b30` |

`0x3f8b30`:

- optionally waits on a condition variable when `edx == 2` and `this+0x8 != 8`
- constructs a large stack record through `0x29b170`
- copies the caller-provided state code from `r12+0x8` into `this+0xc`
- calls `0x3f7ec0` at `0x3f8be4`
- computes the byte length of the buffer materialized by `0x3f7ec0`
- obtains sizes / offsets from the stack record and the caller-supplied sink object
- writes a 0x20-byte header and the materialized buffer through the sink object's virtual slot `+0x18`
- when a depth-payload condition is met, writes additional bytes from `this+0x3e8/+0x3f0`
- in the alternate `this+0xc == 8` branch, obtains the pointer returned by `0x268480`, constructs the string `.dp`, calls `0x233ca0`, and writes additional sink records through virtual slots `+0x20` and `+0x18`
- finalizes through `0x13d4a0`, `0x4c2a40`, `0x13d4e0`, and cleanup

The visible body consumes already-materialized record/vector bytes and writes them to a caller-supplied sink. It does not expose the upstream N-to-1 reducer body or merge math.

## Safe Conclusion

- Proven:
  the selected `+0x40` virtual targets reached by `0x267e80` and `0x267fb0` are setter methods.
- Proven:
  the selected `+0x90` virtual targets reached through `0x268480` / `0x2684a0` are pointer accessors for the inspected `StereoLayer<false>` and `UpsampleLayer` classes.
- Proven:
  the `0x3f8b30` method is a consumer/writer of `0x3f7ec0` materialized record and buffer output.
- Proven:
  the `StereoLayer<false>::runPass(int)` action operator body is at `0x276790`, with first heavy branch targets `0x276860` and `0x277e70`.
- Still unproven:
  the full math inside `0x276860` and `0x277e70`.
- Still unproven:
  the exact reducer body, input shape, output shape, and math behind `src1` / `src2`.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work should not reopen the selected `+0x40` or `+0x90` virtual targets from `0x267e80`, `0x267fb0`, `0x268480`, or `0x2684a0` as closure points.

Future work should also not treat `0x3f8b30` as the missing reducer; its visible body is a record/buffer consumer and sink writer.

The remaining useful path inside this branch is the explicit `StereoLayer<false>::runPass(int)` action body:

- `0x276790`
- `0x276860`
- `0x277e70`

Those addresses are now located but not decoded by this proof.
