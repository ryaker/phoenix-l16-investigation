# Bundle Proof: `src1` `+0x678` Constructor And Runtime Surface

## Scope

This note extends `bundle_proof_src1_alternate_cache_setup.md`.

It proves:

- the visible remainder of the owner-held `+0x678/+0x680` constructor body at `0x3f2c40` is setup, keyed-record construction, descriptor/layer seeding, `this+0x280` helper construction, and bitset storage setup
- the inspected immediate methods at `0x3f75e0`, `0x3f7a40`, `0x3f7b20`, `0x3f7c00`, and `0x3f7ec0` are stop/cleanup, level-gate, callable-slot replacement, byte-count, and record/buffer-materialization surfaces
- the descriptor helper `0x27abb0`, layer-push helper `0x267e80`, start/upsample-push helper `0x267fb0`, list builder `0x22ee10`, scale helper `0x260e40`, and large helper constructor `0x225160` do not by themselves expose the exact `src1` / `src2` N-to-1 reducer

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not prove that the virtual targets reached by the layer-push helpers are non-critical.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Constructor prefix:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3f2c40 --end-address 0x3f2e60'`
- Constructor middle and tail:
  `sed -n '966300,966560p' /Volumes/Dev/lumen-phoenix-scratch/oqd/libcp_disasm.txt` and `sed -n '966880,967120p' /Volumes/Dev/lumen-phoenix-scratch/oqd/libcp_disasm.txt`
- Descriptor and layer helpers:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x27abb0 --end-address 0x27acc0' -o 'disassemble --start-address 0x267e80 --end-address 0x267fb0' -o 'disassemble --start-address 0x267fb0 --end-address 0x268090'`
- Layer constructors:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x26b750 --end-address 0x26ba80' -o 'disassemble --start-address 0x26a890 --end-address 0x26aae0'`
- List and geometry helpers:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x22ee10 --end-address 0x22f080' -o 'disassemble --start-address 0x260e40 --end-address 0x260f40'`
- Large helper constructor:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x225160 --end-address 0x225900'`
- Immediate runtime methods:
  `arch -x86_64 lldb --batch /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib -o 'disassemble --start-address 0x3f75e0 --end-address 0x3f7c30' -o 'disassemble --start-address 0x3f7c00 --end-address 0x3f8230'`
- `0x3f7ec0` continuation:
  `/Volumes/Dev/lumen-phoenix-scratch/oqd/libcp_disasm.txt` lines `970549..971321`

## Proven Facts

### 1. `0x3f2c40` starts as object and state setup

- `0x3f2c77..0x3f2c7e` installs the object vtable.
- `0x3f2ce0..0x3f2cfa` copies and retains the incoming pair into `this+0xe0/+0xe8`.
- `0x3f2cff..0x3f2d20` initializes subobjects at `this+0xf0` and `this+0x190`.
- `0x3f2d25..0x3f2e54` initializes scalar/config/storage fields through at least `this+0x3c0`.
- The constructor prefix already bounded in `bundle_proof_src1_alternate_cache_setup.md` initializes `this+0x448/+0x450` and related mutex/condition fields.

### 2. The post-prefix loop builds integer-keyed records, not a visible reducer closure

- `0x3f3183..0x3f319e` calls `0x1bdfa0(this+0xe0)` and then `0x22ee10(..., edx=1)` to build an integer list.
- `0x22ee10` initializes an output vector, optionally pushes the primary `e6cf0((*r13))` integer when `dl != 0`, iterates objects from `e78d0((*r13))`, and pushes `f2720(object)` only when the visible filter chain passes:
  `f3320(object) == 0`, `object+0x30 != 0`, `f2720(object) != e6cf0((*r13))`, and `f6c60(f2720(object)) == f6c60(e6cf0((*r13)))`.
- `0x3f31c8..0x3f3215` resolves each key through `0x1be970`, copies an object-derived record through `0x264440`, and calls `0x145980` into a stack record.
- `0x3f3221..0x3f3300` inserts or finds records in the separate `this+0x418/+0x420` keyed structure and increments `this+0x428`.
- `0x3f3307..0x3f3374` looks up the same key in the `this+0x448` tree and calls `0x23faf0` with that payload plus the stack record.
- `0x3f3379..0x3f3480` writes the composed data into the separate `this+0x418/+0x420` record, not directly into `this+0x448`.
- `0x3f3503..0x3f352c` calls `0xf3350` and then `0x260e40`.
- `0x260e40` converts a rectangle origin to floats, computes two dimension-over-extent scale values, and optionally collapses them to their max when `dl != 0`.
- `0x3f3531..0x3f35f5` performs keyed lookups in `this+0x448` and calls `0x2415d0` / `0x2415f0`, the direct payload writes already bounded in `bundle_proof_iramp_state_448_later_payload_writes.md`.

This segment is construction and record population over keyed calibration/object state. It does not expose the final N-to-1 reducer.

### 3. The constructor tail seeds six descriptor/layer records

The constructor tail builds six descriptor records and pushes each into the same layer vector:

- calls to `0x27abb0` at `0x3f3bfa`, `0x3f3cf7`, `0x3f3ded`, `0x3f3ee3`, `0x3f3fd9`, and `0x3f40d7`
- corresponding calls to `0x267e80` at `0x3f3c10`, `0x3f3d06`, `0x3f3dfc`, `0x3f3ef2`, `0x3f3fe8`, and `0x3f40e6`
- visible descriptor scale / level constants include `0x20`, `0x10`, `0x8`, `0x4`, `0x2`, and `0x1`, plus float constants including `2.0`, `0.5`, and `16.0`

`0x27abb0` is a descriptor writer:

- writes integer, byte, and float arguments into `rdi+0x00..+0x69`
- copies three 16-bit fields from a stack pointer into `+0x20/+0x22/+0x24`
- copies three scalar values into `+0x30..+0x38`
- computes three reciprocal floats into `+0x50`

`0x267e80` is a layer push surface:

- checks the previous vector element's virtual `+0x88` result and throws `SGM after upsampled depth is not allowed.` when that guard fails
- allocates `0x310` bytes
- calls `0x26ba80 -> 0x26b750` to construct the layer object
- pushes the pointer into the vector at `this+0x10/+0x18/+0x20`
- tail-calls the newly pushed object's virtual `+0x40`

Therefore the visible `0x267e80` body is not a reducer closure by itself. Its virtual tail-call target is a separate downstream runtime target and remains outside this proof.

### 4. The layer constructors inspected here are object setup

- `0x26b750` copies descriptor fields into a `0x310`-byte object, initializes callback/storage fields, allocates four `0x40` blocks, and zeroes the final `0x110`-byte region.
- `0x26a890` initializes a smaller `0xf0`-byte object with a vtable, scalar fields, default constants, byte flags, and zeroed vector/storage fields.

These inspected constructor bodies are object setup, not exposed N-to-1 reducer math.

### 5. The constructor then adds a start/upsample object, builds `this+0x280`, and allocates bitset storage

- `0x3f40fb` calls `0x267fb0`.
- `0x267fb0` requires the layer vector to be nonempty, allocates `0xf0` bytes, calls `0x26a890`, pushes the new object into the same vector, and tail-calls that new object's virtual `+0x40`.
- `0x267fb0` throws `Start by upsample layer is not allowed.` when the vector is empty.
- `0x3f4126..0x3f414a` calls `0x225160` with the object at `this+0x280`, the result of `0x1bdfa0(this+0xe0)`, the `this+0x448` pair, and a two-dword stack configuration.
- `0x225160` copies and retains input pairs into `+0x30/+0x38` and `+0xa0/+0xa8`, copies two dwords to `+0x100/+0x104`, computes/stores a scalar at `+0x108`, constructs multiple owned helper objects, resets local vector/string-like containers, and stores a final byte at `+0x10c`.
- `0x3f414f..0x3f42c7` sizes bitset-like storage from `(this+0xc8 - this+0xc0) / 8` and stores it into `this+0x10/+0x18/+0x20`.
- `0x3f4307..0x3f432c` performs the stack-cookie check and returns.

This closes the visible constructor body through its normal return.

### 6. `0x3f75e0` and `0x3f7600` are stop / cleanup surfaces

- `0x3f75e0` writes byte `1` to `this+0x3f8`, adjusts `this+0x30`, and jumps to `0x2650`.
- `0x3f7600` is a destructor/cleanup body: it sets the vtable, writes byte `1` to `this+0x3f8`, destroys condition/mutex/exception fields, releases shared pointers, tears down `this+0x430`, `this+0x418`, `this+0x400`, `this+0x3e8`, `this+0x3e0`, `this+0x3c8`, callable storage at `this+0x390`, `this+0x280`, subobjects at `this+0x190` and `this+0xf0`, and vector elements at `this+0xc0..+0xc8`.

These inspected bodies are cleanup/stop surfaces.

### 7. `0x3f7a40` is a level-finished gate plus vector dispatch

- `0x3f7a40` computes an index from `this+0xc0/+0xc8`, `this+0x3c0`, and the input level.
- It checks the bitset at `this+0x10/+0x18`.
- If the bit is set, it calls `0x2684a0` on `this+0xb0` with the computed layer index.
- If the bit is not set, it throws `Depth level not finished yet`.
- `0x2684a0` bounds-checks a vector and calls the selected element's virtual `+0x90`.

This inspected path is a level-completion gate and vector dispatch. The selected virtual `+0x90` target remains outside this proof.

### 8. `0x3f7b20` replaces a callable slot

- `0x3f7b20` clears any existing callable at `this+0x3b0`.
- It then transfers or copies a callable-like object from the input `rsi+0x20` into `this+0x3b0`.
- If the input object is self-contained, it invokes the source object's virtual copy path into `this+0x390`.

This is callable-slot replacement. It is not the merge reducer.

### 9. `0x3f7c00` counts bytes for record/vector materialization

- `0x3f7c00` returns immediately unless `this+0xc == 8`.
- It calls `0x1bea00(this+0xe0)` to get a primary integer.
- It walks the integer list from `0x1bdb60(this+0xe0)`.
- In the first pass, it keeps records with `object+0x30 != 0` and matching `f6c60` category, uses `0x226620(this+0x280)` for the primary integer, uses `0x226580(this+0x280, &key)` for other same-category integers, and adds each selected vector byte length to the caller's counter.
- In the second pass, it keeps records with `object+0x30 != 0` and non-matching `f6c60` category, uses `0x226580(this+0x280, &key)`, and adds each selected vector byte length to the caller's counter.

This body computes required bytes over vectors already stored under `this+0x280`.

### 10. `0x3f7ec0` materializes record metadata and copies selected vector bytes

- `0x3f7ec0` sets flags on the output record at `rsi+0x10` and clears fields at `+0x58/+0x60`.
- If `this+0xc != 8`, it marks `rsi+0x10` with `0x14`, writes `rsi+0x60 = 0`, and returns.
- If `this+0xc == 8`, it calls `0x3f7c00` to compute the needed buffer byte count and resizes the caller-provided buffer descriptor at `rdx`.
- It then marks the output record with `0x10` and writes `rsi+0x60 = 3`.
- It walks same-category records first, then non-matching-category records.
- For each accepted key, it resolves an object through `0x1be970`, requires `object+0x30 != 0`, obtains a per-key vector from `this+0x280` through `0x226620` or `0x226580`, creates or reuses metadata objects, writes flag/scalar fields into those metadata objects, and copies the vector bytes into the caller-provided buffer via `memcpy`.
- At the end, it scans the bitset at `this+0x10/+0x18`, computes `output+0x5c`, sets `output+0x10 |= 0xa`, and stores a scalar derived from the caller buffer descriptor into `output+0x50`.

This body is a record/buffer materialization surface over already-built per-key vectors. It does not expose the arithmetic N-to-1 reducer.

## Safe Conclusion

- Proven:
  the visible `+0x678/+0x680` constructor body is now bounded through normal return.
- Proven:
  the constructor builds keyed records, writes known `state+0x448` payload fields through already-bounded helpers, seeds six descriptor/layer objects, constructs `this+0x280`, and allocates bitset storage.
- Proven:
  immediate methods `0x3f75e0`, `0x3f7a40`, `0x3f7b20`, `0x3f7c00`, and `0x3f7ec0` are stop/cleanup, level-gate, callable-slot replacement, byte-count, and record/buffer-materialization surfaces.
- Excluded under the inspected visible bodies:
  the constructor body and these immediate methods do not by themselves close the exact `src1` / `src2` N-to-1 reducer.
- Still unproven:
  the selected virtual targets reached from `0x267e80`, `0x267fb0`, and `0x2684a0`.
- Still unproven:
  the consumers of the record/buffer output materialized by `0x3f7ec0`.
- Still unproven:
  the exact reducer body, input shape, output shape, and math behind `src1` / `src2`.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work should not reopen the visible `0x3f2c40` constructor body, the `0x3f7b20` callable-slot setter, or the `0x3f7c00` / `0x3f7ec0` byte-count and record-pack surfaces as closure points.

The useful next search boundaries are:

- the virtual targets reached by `0x267e80` and `0x267fb0` through newly pushed layer objects' `+0x40` slot
- the virtual target reached by `0x2684a0` through selected layer objects' `+0x90` slot
- the caller/consumer path that uses the record and buffer materialized by `0x3f7ec0`, including the `0x3f8b30` path that calls `0x3f7ec0` at `0x3f8be4`
