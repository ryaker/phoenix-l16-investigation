# Bundle Proof: Prefusion Callback Reuses Known Higher-Group Runner

## Scope

This note proves only the identity of the callback object that `0x2416d0` allocates immediately before dispatch through `0x5670`.

It proves:

- the object built at `0x241b56..0x241bb7` installs vtable address point `0x6589e0`
- `0x6589e0` is the address point of the already-verified higher-group vtable at `0x6589d8`
- that vtable is the already-bounded `runHigherGroupCams::$_12` family whose substantive `+0x30` slot is `0x247390`
- the field layout written by `0x2416d0` matches the field range read by `0x247390`

It does not prove that the exact `src1` / `src2` N-to-1 reducer has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Object-construction disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x241b56 --count 220'`
- Vtable bytes:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format x --size 8 --count 16 0x6589d8'`
- Vtable-body disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x2472d0 --count 1400'`
- Address-point arithmetic:
  `printf '0x%x\n' $((0x241b67 + 0x416e79))`

## Proven Facts

### 1. `0x2416d0` installs vtable address point `0x6589e0`

- At `0x241b60`, the object-construction code performs:
  `leaq 0x416e79(%rip), %rcx`
- The next instruction address is `0x241b67`.
- The address arithmetic therefore resolves to:
  `0x241b67 + 0x416e79 = 0x6589e0`
- `0x241b67` then stores that qword into the first field of the newly allocated 0x48-byte object:
  `movq %rcx, (%rax)`
- Therefore the callback object built by `0x2416d0` uses vtable address point `0x6589e0`.

### 2. `0x6589e0` is the address point of the final higher-group vtable at `0x6589d8`

- Raw memory at `0x6589d8` is:
  - `0x6589d8 = 0x658a30`
  - `0x6589e0 = 0x2472d0`
  - `0x6589e8 = 0x2472e0`
  - `0x6589f0 = 0x2472f0`
  - `0x6589f8 = 0x247340`
  - `0x658a00 = 0x247370`
  - `0x658a08 = 0x247380`
  - `0x658a10 = 0x247390`
  - `0x658a18 = 0x2478d0`
  - `0x658a20 = 0x2478f0`
- Therefore `0x6589e0` is not a standalone table head; it is the address point inside the vtable whose preceding metadata word begins at `0x6589d8`.
- The substantive slot at:
  `address point + 0x30`
  is:
  `0x658a10 = 0x247390`

### 3. This exact vtable is the already-verified `runHigherGroupCams::$_12` family

- The earlier bundle proof in:
  [bundle_proof_calibdataprocessor_lambda_family.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_calibdataprocessor_lambda_family.md)
  already records:
  - final higher-group vtable:
    `0x6589d8`
  - substantive `+0x30` slot:
    `0x247390`
  - preceding `+0x28` delete stub:
    `0x247380`
- The raw vtable bytes above match that earlier proof exactly.
- Therefore the callback object built by `0x2416d0` reuses the already-verified `runHigherGroupCams::$_12` vtable family.

### 4. The field layout written at `0x241b6a..0x241bb7` matches the field range read by `0x247390`

- `0x2416d0` writes the callback-object fields:
  - `+0x08` = pointer to the materialized 24-byte bitset-entry vector at `-0x108(%rbp)`
  - `+0x10` = pointer to selected-count cell `-0xa8(%rbp)`
  - `+0x18` = pointer to copied integer-vector object `-0xd0(%rbp)`
  - `+0x20` = upstream pointer from `-0x158(%rbp)`
  - `+0x28` = upstream pointer from `-0x148(%rbp)`
  - `+0x30` = pointer to local scratch/output slot `-0xa0(%rbp)`
  - `+0x38` = pointer to local float threshold slot `-0x84(%rbp)`
  - `+0x40` = pointer to local integer threshold slot `-0x88(%rbp)`
- The body at `0x247390` visibly reads object fields across that same range:
  - `0x08`
  - `0x10`
  - `0x18`
  - `0x20`
  - `0x28`
  - `0x30`
  - `0x38`
  - `0x40`
- Therefore the callback object allocated inside `0x2416d0` is not a separate unknown family with unrelated layout. Its field shape matches the already-bounded `0x247390` runner body.

### 5. The callback worker here is not a new reducer candidate

- The earlier higher-group runner proof already bounds `0x247390` to:
  - coordinate-table assembly
  - scalar `sqrt(dx*dx + dy*dy)` distance tests
  - threshold comparison
  - bitset membership / output-mask construction
- No visible image-width x image-height pixel-blend loop appears in that runner body itself.
- Therefore the callback object reached after the `0x2416d0` helper tranche does not introduce a new visible reducer candidate. It loops back into an already-bounded higher-group state runner.

## Safe Conclusion

- Proven:
  the callback object allocated by `0x2416d0` installs vtable address point `0x6589e0`.
- Proven:
  `0x6589e0` is the address point of the already-verified higher-group vtable `0x6589d8`.
- Proven:
  that family's substantive `+0x30` slot is `0x247390`.
- Proven:
  the callback object reached after the selector-helper tranche is not a fresh unknown worker; it reuses the already-bounded `runHigherGroupCams::$_12` / `0x247390` state-materialization path.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work should not reopen the post-`0x249410` callback object as a fresh reducer candidate.

That branch now lands back inside the already-bounded higher-group runner family.

The reducer blocker therefore remains open elsewhere, not in this callback-object identity.
