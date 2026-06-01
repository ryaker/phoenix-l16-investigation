# Bundle Proof: Prefusion Callback Uses Adjacent `SparseLNR::markInliers` Table

## Scope

This note proves the identity of the callback object that `0x2416d0` allocates
immediately before dispatch through `0x5670`.

It corrects earlier wording that treated the callback as the
`runHigherGroupCams::$_12` `CalibDataProcessor::State()` runner. The corrected
vtable/typeinfo proof shows:

- the object built at `0x241b56..0x241bb7` installs vtable address point
  `0x6589e0`
- `0x6589e0` is an address point whose `+0x30` slot is `0x247390`
- the metadata for that table points to
  `std::__function::__func<lt::SparseLNR::markInliers(... )::$_0, ..., void (int, int, int)>`
- therefore `0x247390` is not a `CalibDataProcessor::State()` operator body
- the field layout written by `0x2416d0` matches the field range read by
  `0x247390`

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
- Typeinfo-name byte check:
  read the string referenced by the typeinfo object at `0x658a30`; the name
  payload starts at `0x5d8450` and names the `SparseLNR::markInliers` function
  object with `void(int,int,int)` signature.
- Address-point arithmetic:
  `printf '0x%x\n' $((0x241b67 + 0x416e79))`

## Proven Facts

### 1. `0x2416d0` installs vtable address point `0x6589e0`

- At `0x241b60`, the object-construction code performs:
  `leaq 0x416e79(%rip), %rcx`
- The next instruction address is `0x241b67`.
- The address arithmetic resolves to:
  `0x241b67 + 0x416e79 = 0x6589e0`
- `0x241b67` stores that qword into the first field of the newly allocated
  `0x48`-byte object.
- Therefore the callback object built by `0x2416d0` uses vtable address point
  `0x6589e0`.

### 2. The `+0x30` callback body is `0x247390`

Raw memory at `0x6589d8` is:

| Address | Qword |
|---:|---:|
| `0x6589d8` | `0x658a30` |
| `0x6589e0` | `0x2472d0` |
| `0x6589e8` | `0x2472e0` |
| `0x6589f0` | `0x2472f0` |
| `0x6589f8` | `0x247340` |
| `0x658a00` | `0x247370` |
| `0x658a08` | `0x247380` |
| `0x658a10` | `0x247390` |
| `0x658a18` | `0x2478d0` |
| `0x658a20` | `0x2478f0` |

Therefore the substantive `+0x30` slot at this address point is `0x247390`.

### 3. This table is not the `CalibDataProcessor::State()` table

- The metadata pointer at `0x6589d8` is `0x658a30`.
- The typeinfo-name payload referenced from `0x658a30` starts at `0x5d8450`.
- That payload names:
  `std::__1::__function::__func<lt::SparseLNR::markInliers(... )::$_0, ..., void (int, int, int)>`.
- The corrected `CalibDataProcessor::State()` terminal table is instead
  address point `0x658958` with `+0x30 = 0x22e1d0`.
- Therefore the callback object built by `0x2416d0` is an adjacent
  `SparseLNR::markInliers` callback object, not the higher-group State runner.

### 4. The field layout written at `0x241b6a..0x241bb7` matches the field range read by `0x247390`

- `0x2416d0` writes the callback-object fields:
  - `+0x08` = pointer to the materialized 24-byte bitset-entry vector at
    `-0x108(%rbp)`
  - `+0x10` = pointer to selected-count cell `-0xa8(%rbp)`
  - `+0x18` = pointer to copied integer-vector object `-0xd0(%rbp)`
  - `+0x20` = upstream pointer from `-0x158(%rbp)`
  - `+0x28` = upstream pointer from `-0x148(%rbp)`
  - `+0x30` = pointer to local scratch/output slot `-0xa0(%rbp)`
  - `+0x38` = pointer to local float threshold slot `-0x84(%rbp)`
  - `+0x40` = pointer to local integer threshold slot `-0x88(%rbp)`
- The body at `0x247390` visibly reads object fields across that same range:
  `0x08`, `0x10`, `0x18`, `0x20`, `0x28`, `0x30`, `0x38`, and `0x40`.
- Therefore the callback object allocated inside `0x2416d0` matches the field
  shape consumed by `0x247390`.

### 5. The callback worker is not a State-family reducer proof

- `0x247390` visibly performs coordinate-table assembly, scalar distance tests,
  threshold checks, bitset membership updates, and output-mask mutation.
- No visible image-width x image-height pixel-blend loop appears in this body.
- Because the table type is `SparseLNR::markInliers(..., void(int,int,int))`,
  this body cannot be used as evidence that `runHigherGroupCams::$_12`
  `State()` semantics were decoded.

## Safe Conclusion

- Proven:
  the callback object allocated by `0x2416d0` installs vtable address point
  `0x6589e0`.
- Proven:
  that table's substantive `+0x30` callback body is `0x247390`.
- Proven:
  that table is the adjacent `SparseLNR::markInliers` function-object family,
  not the `CalibDataProcessor::State()` family.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work should not reopen the post-`0x249410` callback
object as a `CalibDataProcessor::State()` runner. It is now bounded as an
adjacent SparseLNR mark-inliers callback surface.

The reducer blocker remains open elsewhere, with the corrected terminal State
body now being `0x22e1d0`.
