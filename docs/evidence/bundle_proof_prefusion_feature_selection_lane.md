# Bundle Proof: Prefusion Feature-Selection Lane

## Scope

This note proves only what the installed `libcp.dylib` shows for the broader `0x258fe0` / `0x2598a0` lane left open by the block-geometry proof.

It proves:

- `0x258fe0` builds pyramid / ROI descriptor records and appends 0x30-byte entries
- `0x2598a0` populates per-level feature/candidate containers and scaled coordinate-pair output
- `0x259b40` builds a downsampled feature grid, dispatches callback work, optionally invokes `0x25a010`, and filters 0x24-byte records by coordinate windows
- the callback object built in `0x259b40` uses vtable address point `0x658b80`, whose substantive `+0x30` slot is `0x25a360`
- `0x25a360` fills feature/candidate map records and writes 36-byte output records or sentinel records
- `0x25a010` counts candidate records, derives a small mode value, and dispatches another callback object with vtable address point `0x658c08`
- the substantive `+0x30` slot of the `0x25a010` callback family is `0x25ab50`
- `0x25ab50` performs neighbor/top-candidate suppression over 36-byte record-grid entries, with sorting support from `0x25adf0`

It does not prove that the exact `src1` / `src2` N-to-1 reducer has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Feature-selection lane disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x258fe0 --count 1900'`
- Direct `0x2598a0` lane disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x2598a0 --count 1900'`
- Callback vtable bytes:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format x --size 8 --count 24 0x658b78' -o 'memory read --format x --size 8 --count 24 0x658bb8'`
- Callback body disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25a360 --count 520' -o 'disassemble --start-address 0x25ab50 --count 760' -o 'disassemble --start-address 0x25adc0 --count 220'`

## Proven Facts

### 1. `0x258fe0` builds descriptor/pyramid records, not a reducer

- `0x258ff7` reads a callable pointer from object offset `0x20`.
- `0x258ffb` reads an object pointer from offset `0x38`.
- `0x259002` and `0x259005` read width/height-like fields at offsets `0x10` and `0x14` from the offset-`0x38` object.
- `0x259014` calls `log2` after deriving `min(width, height) / esi`.
- `0x259030` dispatches the callable through vtable slot `+0x30`.
- `0x259081..0x2590cc` appends or grows a vector rooted at object offsets `0x48..0x58` with 0x30-byte descriptor entries using `0xf340` or `0x25bc20`.
- The loop body repeatedly builds ROI/intersection descriptor objects through `0xf540`, `0xf7c0`, `0x12fd0`, `0xf340`, and `0xf4e0`.
- The outer loop advances by `0x30` per level and stops at the `log2`-derived level count.

Therefore the visible body of `0x258fe0` is descriptor / pyramid / ROI construction. It does not expose a multi-camera image reduction loop.

### 2. `0x2598a0` populates feature/candidate vectors and scaled coordinate-pair output

- `0x2598ba..0x25999c` iterates the vector at object offsets `0x48..0x50` in 0x30-byte units.
- Each 0x30-byte entry either appends a 0x18-byte result entry at object offsets `0x60..0x70` through `0x259b40`, or grows that vector through `0x25be50`.
- `0x2598f0..0x259900` requires the object callable at offset `0x20` and dispatches through vtable slot `+0x30`.
- `0x259ac1..0x259aea` throws `std::__1::bad_function_call` when the callable is missing.
- `0x2599c0..0x259aac` performs a second phase over the vector at `0x60`, using `ldexp` to derive a scale for each level.
- `0x259a00..0x259a27` reads two floats from each 36-byte record, multiplies both by the `ldexp`-derived scale, and appends an 8-byte two-float coordinate pair to the vector rooted at object offsets `0x78..0x80`.
- `0x259a60..0x259a68` grows that coordinate-pair vector through `0x25c0b0` when direct append capacity is exhausted.

Therefore `0x2598a0` visibly converts per-level feature/candidate records into scaled coordinate-pair output. It does not expose reducer math.

### 3. `0x259b40` builds a downsampled feature grid and filters 0x24-byte records

- `0x259b7b..0x259ba8` derives downsampled dimensions by dividing fields at offsets `0x10` and `0x14` by 16.
- `0x259be0` calls `0x25c260` to allocate storage for the downsampled grid when the derived product is non-zero.
- `0x259c87` calls `0x212c40` in one branch, while `0x259c98` calls `0x25bb60` in the other branch.
- `0x259d01` installs vtable address point `0x658b80` into a 0x40-byte callback object.
- `0x259d12..0x259d4a` stores only pointers to stack descriptor/grid/threshold/context fields into that callback object.
- `0x259d64` dispatches the callback through generic executor `0x5440`.
- `0x259da7` calls `0x25a010` when the incoming count argument is positive.
- `0x259dc0..0x259e36` walks 0x24-byte records, filters records by two coordinate windows, and appends accepted records into the destination vector at `%r14` either directly or through `0x25c540`.

Therefore `0x259b40` is feature-grid construction, callback dispatch, and coordinate-window filtering over 0x24-byte records. It is not an exposed N-to-1 pixel reducer.

### 4. The `0x259b40` callback vtable lands at `0x25a360`

- At `0x259d01`, the instruction is:
  `leaq 0x3fee78(%rip), %rcx`
- The next instruction address is `0x259d08`.
- Address arithmetic gives:
  `0x259d08 + 0x3fee78 = 0x658b80`
- Raw memory around the vtable shows:
  - `0x658b78 = 0x658bd0`
  - `0x658b80 = 0x25a2a0`
  - `0x658b88 = 0x25a2b0`
  - `0x658b90 = 0x25a2c0`
  - `0x658b98 = 0x25a310`
  - `0x658ba0 = 0x25a340`
  - `0x658ba8 = 0x25a350`
  - `0x658bb0 = 0x25a360`
- Therefore the callback object's substantive `+0x30` slot is:
  `0x658b80 + 0x30 = 0x658bb0 = 0x25a360`

### 5. `0x25a360` writes feature/candidate map records, not reducer output

- `0x25a37e..0x25a390` multiplies the incoming grid coordinate fields by 16.
- `0x25a39d..0x25a425` intersects that 16-pixel tile region with a source rectangle and constructs a local descriptor over the intersected region.
- `0x25a469` and `0x25a4aa` call `0xa8740` to build two temporary descriptor objects from the intersected region.
- `0x25a4e9` calls `0xf540` to build another 16-sized descriptor.
- `0x25a5d8..0x25a6a4` walks derived float grids and writes 16-byte records made from products of two float inputs.
- `0x25a710`, `0x25a723`, and `0x25a72f` produce another temporary descriptor object and copy it into the local descriptor flow.
- `0x25a770..0x25a7d7` scans a fixed 16x16 region, computes scalar scores, and tracks a best coordinate/index pair.
- `0x25a824..0x25a845` checks the resulting coordinate pair against a four-float window.
- `0x25a87e` calls the already-bounded two-float coordinate delta / scale helper `0x25c990`.
- `0x25a8b6..0x25a8e6` writes a valid 36-byte output record containing two original floats, two transformed coordinates, a scalar score, and zeroed tail bytes.
- `0x25a921..0x25a934` writes a sentinel output record and sets byte `+0x20 = 1` for rejection/fallback.

Therefore `0x25a360` fills feature/candidate map records. It writes per-cell candidate state, not a blended image.

### 6. `0x25a010` counts candidate records and dispatches a second callback family

- `0x25a035..0x25a044` receives a vector range through `%rcx`.
- The record-size arithmetic uses the same 0x24-byte stride pattern:
  `0xe38e38e38e38e38f` after subtracting `0x24` from the end pointer.
- `0x25a0c0..0x25a126` performs a SIMD count over four 0x24-byte records at a time, checking whether the first two float fields are positive.
- `0x25a150..0x25a172` performs the same positive-first-two-floats check for the scalar tail.
- `0x25a174..0x25a1d3` derives a small mode value in `-0x68(%rbp)` from the ratio of the incoming count argument to the positive-record count.
- `0x25a205` installs vtable address point `0x658c08` into a stack callback object.
- `0x25a210..0x25a220` stores pointers to the count, record-vector, and mode state into that callback object.
- `0x25a22f` dispatches through generic executor `0x5440`.

Therefore `0x25a010` is candidate counting and mode-driven callback dispatch over 0x24-byte records. It is not reducer closure.

### 7. The `0x25a010` callback vtable lands at `0x25ab50`

- At `0x25a205`, the instruction is:
  `leaq 0x3fe9fc(%rip), %rax`
- The next instruction address is `0x25a20c`.
- Address arithmetic gives:
  `0x25a20c + 0x3fe9fc = 0x658c08`
- Raw memory around the vtable shows:
  - `0x658c00 = 0x658c50`
  - `0x658c08 = 0x25aab0`
  - `0x658c10 = 0x25aac0`
  - `0x658c18 = 0x25aad0`
  - `0x658c20 = 0x25ab10`
  - `0x658c28 = 0x25ab30`
  - `0x658c30 = 0x25ab40`
  - `0x658c38 = 0x25ab50`
  - `0x658c40 = 0x25adc0`
  - `0x658c48 = 0x25ade0`
- Therefore the callback object's substantive `+0x30` slot is:
  `0x658c08 + 0x30 = 0x658c38 = 0x25ab50`

### 8. `0x25ab50` performs neighbor/top-candidate suppression over record-grid entries

- `0x25ab64..0x25ab7d` converts the supplied grid coordinate into a linear record index using the row width stored through callback field `+0x8`.
- `0x25ab93..0x25acda` checks neighboring entries in the 36-byte record grid and collects 8-byte `(index, score)`-style pairs when those neighbor entries have positive first-two-float fields.
- `0x25abba` calls `0x25c6c0` for the first collected candidate vector.
- `0x25ac11`, `0x25ac6e`, and `0x25acd5` call `0x25c810` to append candidate pairs when direct capacity is exhausted.
- `0x25acf5` calls `0x25adf0` when the collected candidate count exceeds the configured limit.
- `0x25ad24` loads `0xbf800000bf800000`, i.e. two `-1.0` floats packed into one qword.
- `0x25ad30..0x25ad43` writes that `(-1.0, -1.0)` sentinel pair into selected 36-byte records.
- The visible work is neighbor inspection, score-pair collection, optional top-candidate limiting, and sentinel marking.

Therefore `0x25ab50` is candidate suppression / marking over feature records, not image reduction.

### 9. `0x25adf0` is sorting / top-candidate support over 8-byte pairs

- `0x25adf0` operates on ranges whose unit is 8 bytes.
- The visible comparisons use the float at pair offset `+0x4`.
- The visible swaps move the 32-bit index at pair offset `+0x0` together with the float score at pair offset `+0x4`.
- It calls helper sort/partition bodies such as `0x25b6b0` and `0x25b800`.

Therefore `0x25adf0` is support code for ordering or limiting `(index, score)` pairs. It is not reducer math.

## Safe Conclusion

- Proven:
  the visible `0x258fe0` / `0x2598a0` lane is feature / pyramid / candidate / coordinate-output work.
- Proven:
  `0x259b40` dispatches a concrete callback object at vtable address point `0x658b80`, whose substantive `+0x30` slot is `0x25a360`.
- Proven:
  `0x25a360` writes feature/candidate map records or sentinel records.
- Proven:
  `0x25a010` dispatches a second concrete callback object at vtable address point `0x658c08`, whose substantive `+0x30` slot is `0x25ab50`.
- Proven:
  `0x25ab50` performs neighbor/top-candidate suppression and sentinel marking over 36-byte feature records.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work should not cite the visible `0x258fe0` / `0x2598a0` lane as reducer closure.

This lane is now bounded as feature-selection, candidate-record generation, candidate suppression, and scaled coordinate-output support.

The reducer blocker remains elsewhere and may only close when a different surface is proven to have real N-to-1 input shape or reduction math.
