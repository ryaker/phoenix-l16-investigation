# Bundle Proof: `src1` Alternate Cache Setup

## Scope

This note extends the `src1` / `src2` blocker chain beyond the owner cache-selection proof.

It proves:

- the owner constructs optional `+0x698/+0x6a0` from the existing `+0x6a8/+0x6b0` and `+0x678/+0x680` owner pairs through `0x3d8b70 -> 0x3d8780`
- the owner constructs `+0x6b8/+0x6c0` from `+0x688/+0x690`, `+0x698/+0x6a0`, and a `0x18`-byte state block through `0x3f06f0 -> 0x3f04d0`
- the inspected `+0x6b8` constructor body is base dimension/pyramid setup, state/scalar copy, shared-ptr-like pair copy, and callable-slot installation
- the inspected optional `+0x698` setup body stores pair references, dimensions, mutexes, vectors, and callback slots
- the visible `+0x678` constructor prefix at `0x3f46d0 -> 0x3f2c40` overlaps the already-bounded `state+0x448` tree/control setup

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not fully decode the `+0x678/+0x680` helper object.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Owner alternate-cache construction region:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3b3170 --end-address 0x3b3560'`
- `+0x6b8` constructor body and base constructor:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3f04d0 --end-address 0x3f0720' -o 'disassemble --start-address 0x3cfd80 --end-address 0x3d0160'`
- Optional `+0x698` constructor and callback setters:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3d8780 --end-address 0x3d9020'`
- `+0x6b8` vtable slots:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'memory read --format x --size 8 --count 24 0x66a208' -o 'disassemble --start-address 0x3c2160 --end-address 0x3c2200'`
- State-block and scalar setup helpers:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3b4970 --end-address 0x3b4af0' -o 'disassemble --start-address 0x3c5ff0 --end-address 0x3c6080' -o 'disassemble --start-address 0x3c8be0 --end-address 0x3c8c80'`
- `+0x678` constructor prefix:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3f46d0 --end-address 0x3f4aa0' -o 'disassemble --start-address 0x3f2c40 --end-address 0x3f3150'`

## Proven Facts

### 1. The owner conditionally constructs `+0x698/+0x6a0`

- At `0x3b317e`, the owner path calls `0x40b010`.
- At `0x3b3183..0x3b3185`, it tests the return value and skips to `0x3b33d2` when false.
- At `0x3b318b`, it reads `owner+0xc8`.
- At `0x3b3192`, it calls `0x40b0e0`.
- At `0x3b319a..0x3b31a1`, it reads `owner+0x4d8/+0x4e0`.
- At `0x3b31a8`, it allocates `0x290` bytes.
- At `0x3b31eb`, it computes inner pointer `allocation + 0x20`.
- At `0x3b31ef`, it passes that inner pointer as `%rdi`.
- At `0x3b31f2`, it passes the stack-held dimension/record pointer as `%rdx`.
- At `0x3b31f9`, it passes the saved `owner+0x6a8` pair as `%rcx`.
- At `0x3b3200`, it passes the saved `owner+0x678` pair as `%r8`.
- At `0x3b3207`, it calls `0x3d8b70`, the thunk to `0x3d8780`.
- At `0x3b320c`, it stores the inner pointer at `owner+0x698`.
- At `0x3b321a`, it stores the allocation/control pointer at `owner+0x6a0`.

Therefore the optional `+0x698/+0x6a0` pair is constructed from existing owner-held `+0x6a8/+0x6b0` and `+0x678/+0x680` pairs plus a selected dimension/record input.

### 2. The owner installs four callbacks on the `+0x698` object

After storing `owner+0x698`, the owner path calls four setter bodies with stack callback objects:

- `0x3b324f` calls `0x3d8ba0`.
- `0x3b32ee` calls `0x3d8d90`.
- `0x3b3347` calls `0x3d8f10`.
- `0x3b33a3` calls `0x3d8e50`.

The setter bodies each lock `this+0x170`, replace one callable pointer field, and unlock:

- `0x3d8ba0` replaces `this+0x160`.
- `0x3d8d90` replaces `this+0xd0`.
- `0x3d8e50` replaces `this+0x100`.
- `0x3d8f10` replaces `this+0x130`.

These inspected setter bodies are callback-slot registration surfaces.

### 3. `0x3d8780` stores pair references, dimensions, vectors, mutexes, and callback slots

The `0x3d8b70 -> 0x3d8780` constructor body:

- calls `0x292070` at `0x3d87ae`
- zeroes object fields `+0x18..+0x78` at `0x3d87b3..0x3d87ca`
- copies and retains the `%rcx` pair into `this+0x80/+0x88` at `0x3d87ce..0x3d87ea`
- stores constant `0xa` at `this+0x90` at `0x3d87ef`
- copies and retains the `%r8` pair into `this+0x98/+0xa0` at `0x3d87f9..0x3d8813`
- initializes callback pointer fields `+0xd0`, `+0x100`, `+0x130`, and `+0x160` to zero at `0x3d881c..0x3d8843`
- initializes mutexes at `this+0x170` and `this+0x1b0` at `0x3d8848..0x3d8865`
- zeroes vector/storage fields `+0x1f0..+0x260` at `0x3d886a..0x3d889e`
- copies two dimensions from `%r15` into `this+0x268/+0x26c` at `0x3d88a9..0x3d88b6`
- builds a stack/vector descriptor through `0x18e800` and `0xf340` at `0x3d88cd..0x3d88ea`
- calls `0x3f7b20` with the object at `this+0x98` and a callback object at `0x3d88ff..0x3d8920`

This inspected constructor shape is setup/state/callback plumbing. It does not expose N-to-1 pixel reduction math.

### 4. The owner constructs `+0x6b8/+0x6c0` from `+0x688`, `+0x698`, and a state block

- At `0x3b33d2`, the owner path calls `0x3b4970` with output at stack `-0x2f8` and the owner as input.
- At `0x3b33e1`, it allocates `0xe0` bytes.
- At `0x3b33ee`, it computes `%r9 = owner + 0x688`.
- At `0x3b33f5`, it computes the stack argument as `owner + 0x698`.
- At `0x3b3404`, it writes the vtable/address-point value for the allocation.
- At `0x3b3411`, it computes inner pointer `allocation + 0x20`.
- At `0x3b3415`, it writes the `owner+0x698` pair address as the stack argument.
- At `0x3b3419`, it passes the `0x3b4970` output block as `%rcx`.
- At `0x3b3420`, it passes the inner pointer as `%rdi`.
- At `0x3b3423`, it passes the same dimension/record input used by the owner setup path as `%rsi`.
- At `0x3b342a`, it passes another stack-held dimension/record pointer as `%rdx`.
- At `0x3b3431`, it passes another stack-held pair as `%r8`.
- At `0x3b3438`, it calls `0x3f06f0`, the thunk to `0x3f04d0`.
- At `0x3b343d`, it stores the inner pointer at `owner+0x6b8`.
- At `0x3b344b`, it stores the allocation/control pointer at `owner+0x6c0`.

Therefore `+0x6b8/+0x6c0` is an owner-held alternate cache/helper pair constructed from `+0x688/+0x690`, `+0x698/+0x6a0`, and a local state block.

### 5. `0x3f04d0` is constructor/setup work for the `+0x6b8` object

The `0x3f06f0 -> 0x3f04d0` body:

- saves `%r9`, `%rcx`, `%rdi`, and the stack argument at `0x3f04e1..0x3f04ea`
- passes `%r8` as `%rcx` and calls base constructor `0x3cfd80` at `0x3f04fd..0x3f0500`
- copies a `0x18`-byte state block from `%rcx`/`%rbx` into `this+0x80`, `this+0x90`, and `this+0x94` at `0x3f0505..0x3f051f`
- computes `float(this+0x88) * float(this+0x84) / float(this+0x80)` into `this+0x98` at `0x3f0527..0x3f0545`
- copies and retains the `%r9` pair into `this+0xa0/+0xa8` at `0x3f054f..0x3f056b`
- copies and retains the stack-argument pair into `this+0xb0/+0xb8` at `0x3f0570..0x3f058c`
- builds a stack callback object and calls `0x3d0120` at `0x3f0591..0x3f05ae`
- has cleanup paths that release `+0xb8`, `+0xa8`, callable slot `+0x70`, pair `+0x40`, and vector storage `+0x20/+0x8`

At the owner call site, `%r9` is `owner+0x688` and the stack argument is `owner+0x698`.

### 6. `0x3cfd80` is base dimension/pyramid record setup

The base constructor at `0x3cfd80`:

- copies two dimensions from `%rdx` into `this+0/+0x4` at `0x3cfd97..0x3cfda0`
- initializes vector/storage at `this+0x8` through `0x292070`
- zeroes fields at `this+0x20/+0x30`
- copies and retains the `%rcx` pair into `this+0x38/+0x40`
- initializes callable slot `+0x70` to zero
- iterates dimension-pair records from `this+0x8..+0x10`
- checks sorting of those records at `0x3cfe20..0x3cfe3e`
- builds derived dimension records into `this+0x20..+0x30`
- throws string `TileCache pyramid not sorted!` when the sort check fails

This body is dimension/pyramid record setup.

### 7. The `+0x6b8` address-point slots inspected here are cleanup slots

The address point read at `0x66a208` contains:

- `0x66a208 = 0x3c2160`
- `0x66a210 = 0x3c2190`
- `0x66a218 = 0x3c21d0`
- `0x66a220 = 0`
- `0x66a228 = 0x3c21e0`

The corresponding bodies are cleanup/destructor/delete surfaces:

- `0x3c2160` resets the vtable, calls `0x3f07c0` on `this+0x20`, then calls `std::__1::__shared_weak_count::~__shared_weak_count()`.
- `0x3c2190` does the same cleanup and then calls `operator delete`.
- `0x3c21d0` adjusts `this` by `+0x20` and jumps to `0x3f07c0`.
- `0x3c21e0` jumps to `operator delete`.

These inspected slots do not expose reducer work.

### 8. `0x3b4970` fills the state block consumed by `0x3f04d0`

The state-block helper at `0x3b4970`:

- reads `owner+0x6a8` at `0x3b4980`
- calls `0x3e0b90` at `0x3b498b`
- writes two dwords from the stack result into output `+0x10/+0x14` at `0x3b4990..0x3b499a`
- calls owner/calibration accessors `0x3c6ac0`, `0x1bea00`, `0x1bdfa0`, `0xe76b0`, `0xe7020`, and `0xe7730`
- writes floats into output `+0x8`, `+0x4`, `+0x0`, and `+0xc`

Those output fields are copied by `0x3f04d0` into the `+0x6b8` object fields `+0x80..+0x94`.

### 9. The visible `+0x678` constructor prefix overlaps known `state+0x448` setup

- `0x3f46d0` normalizes boolean-sized arguments and calls `0x3f2c40`.
- `0x3f2c77..0x3f2c7e` installs the object vtable.
- `0x3f2ce0..0x3f2cfa` copies and retains the incoming pair into `this+0xe0/+0xe8`.
- `0x3f2cff..0x3f2d20` initializes subobjects at `this+0xf0` and `this+0x190` through `0x318030`.
- `0x3f2e73..0x3f2e96` stores config/flag fields at `this+0x3f8..+0x3fc`.
- `0x3f2ee3..0x3f2f18` allocates a `0x30`-byte object and stores the resulting tree/control pair at `this+0x448/+0x450`.
- `0x3f2f2a..0x3f2f4f` initializes mutex/condition fields at `this+0x460/+0x4a0`.
- `0x3f2f73..0x3f3011` walks records returned through `0x1bdb60` / `0x1be970`, checks `object+0x30`, and calls `0x1f0ce0` for records with that byte set.
- `0x3f3061..0x3f3145` walks another record list and uses `this+0x448` with `0xf2720`, `0x38dad0`, `0x241590`, and `0x2415b0`.

This prefix is the same `state+0x448` tree/control family bounded in `bundle_proof_iramp_state_448_tree_builder.md`.

This note does not decode the remainder of `0x3f2c40`; that continuation is handled separately in `bundle_proof_src1_678_constructor_runtime_surface.md`.

## Safe Conclusion

- Proven:
  optional `+0x698/+0x6a0` construction is setup over existing owner `+0x6a8/+0x6b0` and `+0x678/+0x680` pairs, selected dimensions, vectors, mutexes, and callback slots.
- Proven:
  `+0x6b8/+0x6c0` construction combines `+0x688/+0x690`, `+0x698/+0x6a0`, and a `0x18`-byte state block through constructor/setup bodies.
- Proven:
  the inspected `+0x6b8` address-point slots are cleanup/destructor/delete slots.
- Proven:
  the visible `+0x678` constructor prefix overlaps the already-bounded `state+0x448` tree/control setup.
- Excluded under the inspected installed-bundle bodies:
  the `+0x6b8` alternate-cache construction surface and optional `+0x698` callback-registration surface are not exposed `src1` / `src2` N-to-1 reducer closure.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer body, input shape, output shape, and math.
- Still unproven in this note:
  full `+0x678/+0x680` semantics beyond the inspected constructor prefix.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work should not reopen the `+0x6b8` alternate-cache constructor or optional `+0x698` callback-registration surface as reducer closure.

The useful next search boundary after this note was the remainder of `0x3f2c40` after `0x3f3150` and downstream uses of the owner-held `+0x678/+0x680` pair. That boundary is now advanced by `bundle_proof_src1_678_constructor_runtime_surface.md`; closure still requires a different surface with real N-to-1 input shape or reduction math.
