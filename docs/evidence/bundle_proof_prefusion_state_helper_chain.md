# Bundle Proof: First Post-`State()` Helper Chain Beneath Anchor Pre-Fusion

## Scope

This note proves only what the installed `libcp.dylib` shows for the first helper chain reached beneath the verified `CalibDataProcessor::State()` `operator()` family.

It proves:

- `0x224cc0` and `0x224d70` are orchestrators around a subobject at `state+0x70`
- `0x242a80`, `0x258ea0`, `0x258f00`, `0x242d00`, `0x242dc0`, `0x243770`, and `0x243870` are setup / copy / container-reset surfaces
- the earlier broad attribution of a SIMD record scan to `0x243870` is wrong; that later scan begins in the next symbol at `0x2439b0`
- the first clearly heavier downstream consumers reached from this chain are `0x244560` and `0x245a40`

It does not prove that `0x244560` or `0x245a40` is the exact `src1` / `src2` N-to-1 reducer.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Orchestrator disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x224cc0 --count 180' -o 'disassemble --start-address 0x224d70 --count 220'`
- Setup-helper disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x242a80 --count 120' -o 'disassemble --start-address 0x242b30 --count 80' -o 'disassemble --start-address 0x242b50 --count 80' -o 'disassemble --start-address 0x242b70 --count 80' -o 'disassemble --start-address 0x242b90 --count 100' -o 'disassemble --start-address 0x242d00 --count 180' -o 'disassemble --start-address 0x242dc0 --count 180' -o 'disassemble --start-address 0x243770 --count 120' -o 'disassemble --start-address 0x243870 --count 180' -o 'disassemble --start-address 0x258ea0 --count 160'`
- Downstream-consumer disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x2443d0 --count 140' -o 'disassemble --start-address 0x244560 --count 160' -o 'disassemble --start-address 0x245a20 --count 100' -o 'disassemble --start-address 0x245a40 --count 160'`

## Proven Facts

### 1. `0x224cc0` is an orchestrator around a subobject at `state+0x70`

- `0x224cc0` computes `r14 = rbx + 0x70`.
- It stages a shared source pair from `(%rbx)` / `0x8(%rbx)` into stack temporaries, with the usual `__add_shared()` / `__release_shared()` calls.
- It calls:
  - `0x242a80` with destination `state+0x70`
  - `0x242b30`
  - `0x242b50`
- It then:
  - adds `0x20` to the outer-state pointer
  - calls `0x242b70`
  - compares the returned pointer against `state+0x20`
  - conditionally copies 16 bytes with `0xe8e70`
- Therefore the visible body is orchestration around the `+0x70` subobject and a possible 16-byte header sync.
- No image-width x image-height traversal appears in `0x224cc0` itself.

### 2. `0x224d70` is the parallel orchestrator for the richer path under the same `+0x70` subobject

- `0x224d70` also computes `r14 = rbx + 0x70`.
- It stages a shared source pair from `0x10(%rbx)` / `0x18(%rbx)`.
- It reads:
  - `float` values from `0x54(%rbx)` and `0x58(%rbx)`
  - an `int` from `0x5c(%rbx)`
  - a pointer to outer-state data at `0x68(%rbx)`
- It calls, in order:
  - `0x243870`
  - `0x242d00`
  - `0x242dc0`
  - `0x245a40`
- It then:
  - adds `0x38` to the outer-state pointer
  - calls `0x242b90`
  - compares the returned pointer against `state+0x38`
  - conditionally copies 16 bytes with `0xe8e70`
- Therefore `0x224d70` is still an orchestrator over the `+0x70` subobject plus deeper helpers.
- The heavy work, if any, is downstream of this symbol.

### 3. `0x242a80` installs a shared source pair, normalizes two floats, stores two small scalar fields, then tail-calls `0x258ea0`

- `0x242a80` copies the incoming shared object pair from `(%r13)` / `0x8(%r13)` into `(%rbx)` / `0x8(%rbx)` with proper retain/release handling.
- It then reads image dimensions from the installed source object:
  - `0x10(%rax)`
  - `0x14(%rax)`
- It divides the two floats at `(%r12)` / `0x4(%r12)` by those dimensions and stores the normalized results into:
  - `0x10(%rbx)`
  - `0x14(%rbx)`
- It stores:
  - the `int` argument into `0x234(%rbx)`
  - the low byte of the flag argument into `0x231(%rbx)`
- It then tail-calls `0x258ea0` with:
  - `rdi = 0x3c8(%rbx)`
  - `rsi = rbx`
  - `edx = 6`
  - `ecx = zero-extended low byte flag`
- Therefore `0x242a80` is a setup helper that populates fields from an installed shared source and normalized coordinate-like inputs before delegating onward.

### 4. `0x258ea0` and `0x258f00` store source/flag fields and clear container-like regions

- `0x258ea0`:
  - copies the shared pair from `(%rsi)` / `0x8(%rsi)` into `0x38(%rbx)` / `0x40(%rbx)`
  - stores `edx` into `0x30(%rbx)`
  - stores `cl` into `0x34(%rbx)`
  - tail-calls `0x258f00`
- `0x258f00` then walks and clears three container-like regions in the object at `rbx`:
  - `0x48 .. 0x50`
  - `0x60 .. 0x68`
  - `0x78 .. 0x80`
- The `0x60 .. 0x68` region is cleared in `0x18`-byte steps.
- The `0x78 .. 0x80` region is end-aligned back to its base.
- Therefore this stage is still object-state installation and reset, not reducer closure.

### 5. `0x242d00` and `0x242dc0` are direct descriptor-copy helpers into two fixed subranges

- `0x242d00` copies a descriptor-like object from `rsi` into `rdi` starting at `+0x18` and ending at `+0xb8`.
- It performs a field-by-field copy of:
  - vector-sized blocks from `0x00`, `0x10`, `0x30`, `0x40`, `0x80`, and `0x90`
  - scalar fields from `0x20`, `0x24`, `0x28`, `0x2c`, `0x50`, `0x54`, `0x58`, `0x5c`, `0x60`, and `0xa0`
- If the source object is not already the destination subobject, it also copies the shared pair at `0x68` / `0x70` using `0xf02d0`.
- `0x242dc0` does the same shape of copy into the second fixed subrange beginning at `+0xc0` and ending at `+0x160`, again with the same optional shared-pair copy via `0xf02d0`.
- Therefore these two helpers are plain struct-copy surfaces for two fixed descriptor blocks.

### 6. `0x243770` and `0x243870` populate state fields; neither function contains the later SIMD record scan

- `0x243770`:
  - installs a shared pair into `0x1c0` / `0x1c8`
  - end-aligns the `0x1e8 .. 0x1f0` region back to an 8-byte boundary
  - stores a flag to `0x230`
  - stores a float to `0x23c`
  - stores an `int` to `0x240`
  - normalizes two floats against source dimensions and stores them to `0x244` / `0x248`
  - stores another float to `0x3c4`
- `0x243870` follows the same basic pattern but instead:
  - copies eight `int` fields from `r9` into `0x24c .. 0x268`
  - copies `0x90` bytes from `r9 + 0x20` into `0x26c`
  - stores direct `int` values from `rcx` into `0x244` / `0x248`
- The function `0x243870` returns at `0x2439ae`.
- The later SIMD record-scan body begins only in the next symbol, `0x2439b0`.
- Therefore `0x243770` and `0x243870` themselves are still state-population helpers.

### 7. `0x242b70` and `0x242b90` are tiny address-return helpers, and `0x242b30` / `0x242b50` dispatch deeper work off `state->0x3c8`

- `0x242b70` returns `0x3c8(%rdi) + 0x78`.
- `0x242b90` returns `rdi + 0x1e8`.
- `0x242b30` loads `rdi = 0x3c8(%rdi)` and jumps to `0x258fe0` with constants:
  - `esi = 0x96`
  - `edx = 0x8`
- `0x242b50` loads `rdi = 0x3c8(%rdi)` and jumps to `0x2598a0` with constants:
  - `esi = 0xfa0`
  - `edx = 0x2`
- Therefore the orchestrators at `0x224cc0` and `0x224d70` are using tiny pointer-return helpers plus deeper `state->0x3c8` dispatchers, not closing the reducer themselves.

### 8. `0x245a20` is a dispatcher into a heavier common consumer at `0x244560`

- `0x245a20` computes:
  - `rsi = rdi + 0x18`
  - `rdx = rdi + 0xc0`
  - `ecx = 1`
- It then tail-jumps to `0x244560`.
- Therefore the lighter path does not end at `0x245a20`; it immediately enters a larger downstream consumer shared with the two copied descriptor blocks.

### 9. `0x244560` and `0x245a40` are the first clearly heavier downstream consumers reached from this chain

- Both `0x244560` and `0x245a40`:
  - allocate large stack frames
  - require a callable object at `0x220(%state)` and throw `std::__1::bad_function_call` if it is null
  - call the virtual slot at `+0x30` of that callable and branch on the returned boolean
  - read vector-like regions from `0x3c8(%state)`
  - call `0x242f40` before proceeding into larger numeric work
- `0x244560` additionally:
  - stores the incoming float argument at `0x238(%state)`
  - derives a boolean flag at `0x3c0(%state)` from that float
  - calls `0x2443d0`
  - uses the copied descriptor blocks at `state+0x18` and `state+0xc0`
- `0x245a40` additionally:
  - reads a count from `0x3c8(%state)->0x78 .. 0x80`
  - calls `0x2443d0`
  - reads image dimensions from the shared object at `0x1c0(%state)`
  - performs floating-point setup and later enters a large numeric loop after `0x243cd0`
- Therefore the pure setup/copy boundary is now pushed through the first helper chain and up to these two heavier downstream consumers.

## Safe Conclusion

- Proven:
  the first helper chain beneath the verified `CalibDataProcessor::State()` surfaces is still setup-oriented through:
  `0x224cc0`, `0x224d70`, `0x242a80`, `0x258ea0`, `0x258f00`, `0x242d00`, `0x242dc0`, `0x243770`, and `0x243870`.
- Proven:
  `0x243870` itself is only the copy/store helper; the later SIMD record scan starts in the next symbol at `0x2439b0`.
- Proven:
  the first clearly heavier downstream consumers reached from this chain are `0x244560` and `0x245a40`.
- Still unproven:
  whether either of those heavier consumers is the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work no longer needs to spend time re-decoding the first post-`State()` helper layer.

The bundle-proven boundary is now:

1. visible wrappers and backing fields
2. verified `CalibDataProcessor::State()` `operator()` family
3. first post-`State()` setup/copy helper chain
4. first heavier downstream consumers at `0x244560` and `0x245a40`

The remaining unknown is now narrower:
which deeper downstream consumer actually closes the exact N-to-1 reducer behind `src1` / `src2`.
