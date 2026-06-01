# Bundle Proof: Corrected `CalibDataProcessor::State()` Lambda Surface Family

## Scope

This note proves that the installed `libcp.dylib` contains a concrete
`std::__function::__func` family tied by embedded typeinfo names to:

- `lt::CalibDataProcessor::runReferenceGroupCams`
- `lt::CalibDataProcessor::runHigherGroupCams`

It also corrects a prior adjacent-vtable mistake:

- the first `State()` operator body is `0x229df0`
- the terminal `State()` operator body is `0x22e1d0`
- `0x247390` is not a `CalibDataProcessor::State()` operator body; its vtable
  typeinfo belongs to `lt::SparseLNR::markInliers(..., void(int,int,int))`

It does not prove that any one of these `State()` bodies is the exact `src1` /
`src2` N-to-1 reducer.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Embedded name strings:
  `strings -a /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib | rg -n "runReferenceGroupCams|runHigherGroupCams|SparseLNR11markInliers"`
- Raw typeinfo / vtable region:
  `xxd -g 8 -U -s 0x658320 -l 0x720 /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Representative body disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x229d80 --count 40' -o 'disassemble --start-address 0x229ec0 --count 140' -o 'disassemble --start-address 0x22bee0 --count 140' -o 'disassemble --start-address 0x22e1d0 --count 140' -o 'disassemble --start-address 0x247390 --count 40'`
- libc++ primary-source vtable layout:
  `nl -ba /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/c++/v1/__functional/function.h | sed -n '248,336p'`

## Proven Facts

### 1. The shipped bundle embeds 13 State-returning camera-runner function-object names

- The embedded typeinfo-name payloads expose:
  - `runReferenceGroupCams::$_0 .. $_6`
  - `runHigherGroupCams::$_7 .. $_12`
- The corresponding `std::__function::__func<..., lt::CalibDataProcessor::State ()>`
  records occupy vtable address points from `0x658350` through `0x658958`.
- Therefore the installed bundle contains a concrete thirteen-body
  `CalibDataProcessor::State()` function-object family.

### 2. The `+0x30` slot is the virtual `operator()` slot for this family

- The Xcode-shipped libc++ header declares the relevant `__function::__base`
  virtuals in this order:
  - `__clone() const`
  - `__clone(__base*) const`
  - `destroy()`
  - `destroy_deallocate()`
  - `operator()(_ArgTypes&&...)`
  - `target(const type_info&)`
  - `target_type()`
- The representative `runReferenceGroupCams::$_1` table at `0x6583d8` matches
  that layout:
  - `+0x10 = 0x229e50`, clone allocation/copy helper
  - `+0x18 = 0x229e80`, placement-copy helper
  - `+0x20 = 0x229ea0`, no-op destroy path
  - `+0x28 = 0x229eb0`, delete stub
  - `+0x38 = 0x22a010`, target type-check helper
  - `+0x40 = 0x22a030`, target-type return helper
- Therefore `+0x30` is the concrete `operator()` slot for the State-family
  tables below.

### 3. Corrected State-family `+0x30` body table

| Family | Vtable address point | `+0x30` body |
|---|---:|---:|
| `runReferenceGroupCams::$_0` | `0x658350` | `0x229df0` |
| `runReferenceGroupCams::$_1` | `0x6583d8` | `0x229ec0` |
| `runReferenceGroupCams::$_2` | `0x658458` | `0x22a0e0` |
| `runReferenceGroupCams::$_3` | `0x6584d8` | `0x22a9b0` |
| `runReferenceGroupCams::$_4` | `0x658558` | `0x22aaf0` |
| `runReferenceGroupCams::$_5` | `0x6585d8` | `0x22ae60` |
| `runReferenceGroupCams::$_6` | `0x658658` | `0x22af80` |
| `runHigherGroupCams::$_7` | `0x6586d8` | `0x22bdf0` |
| `runHigherGroupCams::$_8` | `0x658758` | `0x22bee0` |
| `runHigherGroupCams::$_9` | `0x6587d8` | `0x22c350` |
| `runHigherGroupCams::$_10` | `0x658858` | `0x22cd00` |
| `runHigherGroupCams::$_11` | `0x6588d8` | `0x22d250` |
| `runHigherGroupCams::$_12` | `0x658958` | `0x22e1d0` |

### 4. `0x247390` is an adjacent non-State function-object body

- The only 8-byte pointer to `0x247390` in the installed binary is at
  `0x658a10`.
- Treating that as a `+0x30` slot gives vtable address point `0x6589e0`.
- The metadata pointer at `0x6589d8` points to typeinfo whose name payload is:
  `std::__1::__function::__func<lt::SparseLNR::markInliers(... )::$_0, ..., void (int, int, int)>`.
- Therefore `0x247390` is not `runHigherGroupCams::$_12` and is not a
  `CalibDataProcessor::State()` operator body.
- The earlier `0x247380` / `0x247390` terminal-State-slot interpretation is
  refuted by this vtable/typeinfo check.

### 5. Representative body facts remain bounded

- `0x229df0` is a tiny constant-return State body: `movl $0x2, %eax; retq`.
- `0x229ec0` has a full prologue, a `0x38` stack frame, shared-state mutation,
  and a loop that appends fixed-size records; it returns constant `3`.
- `0x22bdf0` is a trivial constant-return State body inside the same corrected
  family.
- `0x22bee0` has a full prologue, tree walks, allocations, and helper dispatch
  previously bounded to pair-list / rect-param state work.
- `0x22e1d0` is the terminal corrected State body, not `0x247390`; this note
  establishes identity and table position, not full public semantics for
  `0x22e1d0`.

## Safe Conclusion

- Proven:
  the installed bundle exposes a concrete thirteen-body
  `CalibDataProcessor::State()` `operator()` family associated with
  `runReferenceGroupCams` and `runHigherGroupCams`.
- Proven:
  the corrected State-family body list is `0x229df0`, `0x229ec0`, `0x22a0e0`,
  `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80`, `0x22bdf0`, `0x22bee0`,
  `0x22c350`, `0x22cd00`, `0x22d250`, and `0x22e1d0`.
- Proven:
  `0x247390` belongs to an adjacent `SparseLNR::markInliers` function-object
  table, not this `State()` family.
- Still unproven:
  the public meanings of the returned `State` values and whether a downstream
  consumer of these states closes the exact `src1` / `src2` merge/reduction
  mechanism.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work must use the corrected State-family address
list. The next static/runtime decode target is the terminal corrected State body
`0x22e1d0` and its consumers after the `0x22f3ff` dispatcher, not `0x247390` as
if it were a State-returning runner.

Follow-up runtime liveness is documented in
[lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md).
