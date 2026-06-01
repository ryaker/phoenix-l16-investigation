# Bundle Proof: `CalibDataProcessor` Lambda Surface Family

## Scope

This note proves only that the installed `libcp.dylib` contains a concrete upstream family of `std::__function::__func` surfaces tied by embedded typeinfo names to:

- `lt::CalibDataProcessor::runReferenceGroupCams`
- `lt::CalibDataProcessor::runHigherGroupCams`

It also proves which slot in each family vtable holds the last substantive body.

It does not prove that any one of those bodies is the exact `src1` / `src2` N-to-1 reducer.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Embedded name strings:
  `strings -a /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib | rg -n "runReferenceGroupCams|runHigherGroupCams"`
- Raw typeinfo / vtable region:
  `xxd -g 8 -U -s 0x6583b8 -l 0x660 /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Representative body disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x229ec0 --count 140' -o 'disassemble --start-address 0x22bee0 --count 140' -o 'disassemble --start-address 0x247390 --count 140'`
- Quick family spot-check:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x229ec0 --count 12' -o 'disassemble --start-address 0x22a0e0 --count 12' -o 'disassemble --start-address 0x22a9b0 --count 12' -o 'disassemble --start-address 0x22aaf0 --count 12' -o 'disassemble --start-address 0x22ae60 --count 12' -o 'disassemble --start-address 0x22af80 --count 12' -o 'disassemble --start-address 0x22bdf0 --count 12' -o 'disassemble --start-address 0x22bee0 --count 12' -o 'disassemble --start-address 0x22c350 --count 12' -o 'disassemble --start-address 0x22cd00 --count 12' -o 'disassemble --start-address 0x22d250 --count 12' -o 'disassemble --start-address 0x22e1d0 --count 12' -o 'disassemble --start-address 0x247390 --count 12'`
- libc++ primary-source vtable layout:
  `nl -ba /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/c++/v1/__functional/function.h | sed -n '248,336p'`
- Typeinfo-name decode:
  `printf '%s\n' '_ZTSNSt3__110__function6__funcIZN2lt18CalibDataProcessor21runReferenceGroupCamsEvE3$_0NS_9allocatorIS4_EEFNS3_5StateEvEEE' '_ZTSNSt3__110__function6__funcIZN2lt18CalibDataProcessor18runHigherGroupCamsEvE4$_12NS_9allocatorIS4_EEFNS3_5StateEvEEE' | xcrun llvm-cxxfilt -n`

## Proven Facts

### 1. The shipped bundle embeds 13 lambda-function-object names for the two camera-group runners

- `strings -a` exposes 13 `std::__function::__func<...>` names tied to:
  - `runReferenceGroupCams::$_0 .. $_6`
  - `runHigherGroupCams::$_7 .. $_9`
  - `runHigherGroupCams::$_10 .. $_12`
- Therefore the installed bundle really does contain a discrete family of function-object surfaces for those two runner names.

### 2. The corresponding typeinfo / vtable family is present in one contiguous raw region

- At `0x6583b8`, the raw bytes show a typeinfo-struct-like record whose name pointer is `0x5d6830`, followed immediately by a function-pointer table at `0x6583d8`.
- The same pattern repeats at:
  - `0x658458`
  - `0x6584d8`
  - `0x658558`
  - `0x6585d8`
  - `0x658658`
  - `0x6586d8`
  - `0x658758`
  - `0x6587d8`
  - `0x658858`
  - `0x6588d8`
  - `0x658958`
  - `0x6589d8`
- Therefore the candidate family is not just a loose string match; it has concrete vtable-backed callable surfaces in the installed bundle.

### 3. For this family, the `+0x30` slot is the last substantive body slot

- In the first family vtable at `0x6583d8`, the entries at:
  - `+0x38 = 0x22a010`
  - `+0x40 = 0x22a030`
  are not work bodies.
- `0x22a010` is a type-check helper:
  it compares an incoming typeinfo pointer and conditionally returns `rdi+0x8` or `0`.
- `0x22a030` is a typeinfo-return helper:
  it loads a constant pointer and returns immediately.
- Therefore the immediately preceding slot, `+0x30`, is the last substantive behavior slot in this vtable family.

### 4. The `+0x30` slot is specifically the virtual `operator()` slot of libc++ `std::__function::__func`

- The Xcode-shipped libc++ header at:
  `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/c++/v1/__functional/function.h`
  declares `__function::__base<_Rp(_ArgTypes...)>` virtuals in this order:
  - `__clone() const`
  - `__clone(__base*) const`
  - `destroy()`
  - `destroy_deallocate()`
  - `operator()(_ArgTypes&&...)`
  - `target(const type_info&)`
  - `target_type()`
- The same header then declares `__func<_Fp, _Alloc, _Rp(_ArgTypes...)>` as the concrete implementation of those virtuals.
- The first family vtable at `0x6583d8` matches that exact layout in the installed bundle:
  - `+0x10 = 0x229e50` allocates and copies a new function object, matching `__clone() const`
  - `+0x18 = 0x229e80` placement-copies into caller-provided storage, matching `__clone(__base*) const`
  - `+0x20 = 0x229ea0` is a no-op destroy path, matching `destroy()`
  - `+0x28 = 0x229eb0` jumps to `operator delete(void*)`, matching `destroy_deallocate()`
  - `+0x38 = 0x22a010` compares typeinfo and returns either `rdi+0x8` or `0`, matching `target(const type_info&)`
  - `+0x40 = 0x22a030` returns a constant typeinfo pointer, matching `target_type()`
- Therefore the intervening `+0x30` entry is not just the "last substantive body":
  it is the actual virtual `operator()` slot for this `std::__function::__func` family.

### 5. The stored typeinfo names decode to `lt::CalibDataProcessor::State ()`

- Adding the standard `_ZTS` prefix to the stored typeinfo-name payload and decoding with `llvm-cxxfilt` yields:
  - `typeinfo name for std::__1::__function::__func<lt::CalibDataProcessor::runReferenceGroupCams()::$_0, std::__1::allocator<...>, lt::CalibDataProcessor::State ()>`
  - `typeinfo name for std::__1::__function::__func<lt::CalibDataProcessor::runHigherGroupCams()::$_12, std::__1::allocator<...>, lt::CalibDataProcessor::State ()>`
- Therefore this family is not an arbitrary `std::__function::__func` population:
  its callable signature is `lt::CalibDataProcessor::State ()`.

### 6. The reference-group family has seven concrete `+0x30` `operator()` body addresses

Verified `+0x30` slots:

| Family | Vtable | `+0x30` body |
|---|---|---|
| `runReferenceGroupCams::$_0` | `0x6583d8` | `0x229ec0` |
| `runReferenceGroupCams::$_1` | `0x658458` | `0x22a0e0` |
| `runReferenceGroupCams::$_2` | `0x6584d8` | `0x22a9b0` |
| `runReferenceGroupCams::$_3` | `0x658558` | `0x22aaf0` |
| `runReferenceGroupCams::$_4` | `0x6585d8` | `0x22ae60` |
| `runReferenceGroupCams::$_5` | `0x658658` | `0x22af80` |
| `runReferenceGroupCams::$_6` | `0x6586d8` | `0x22bdf0` |

### 7. The higher-group family has six concrete `+0x30` `operator()` body addresses

Verified `+0x30` slots:

| Family | Vtable | `+0x30` body |
|---|---|---|
| `runHigherGroupCams::$_7` | `0x658758` | `0x22bee0` |
| `runHigherGroupCams::$_8` | `0x6587d8` | `0x22c350` |
| `runHigherGroupCams::$_9` | `0x658858` | `0x22cd00` |
| `runHigherGroupCams::$_10` | `0x6588d8` | `0x22d250` |
| `runHigherGroupCams::$_11` | `0x658958` | `0x22e1d0` |
| `runHigherGroupCams::$_12` | `0x6589d8` | `0x247390` |

### 8. One scratch address in this family was wrong: `0x247380` is not the terminal `operator()` slot

- At the final higher-group vtable `0x6589d8`, the relevant trailing entries are:
  - `+0x28 = 0x247380`
  - `+0x30 = 0x247390`
- Disassembly proves:
  - `0x247380` is a tiny delete stub that immediately jumps to `operator delete(void*)`
  - `0x247390` is the real substantive body with a full prologue and stack frame
- Therefore the correct last higher-group `operator()` slot is `0x247390`, not `0x247380`.

### 9. The family contains real `operator()` bodies, not only stubs

- `0x229ec0` has a full prologue, a `0x38` stack frame, shared-state mutation, and a loop that appends fixed-size records.
- `0x229ec0` returns through `%eax`, ending with `movl $0x3, %eax` before `retq`, which is consistent with the decoded `lt::CalibDataProcessor::State ()` return type.
- `0x22bee0` has a full prologue, a `0x58` stack frame, tree walks, allocations, and multi-step state updates.
- `0x247390` has a full prologue, a `0xc8` stack frame, multi-argument setup, allocations, and indexed table reads.
- `0x22bdf0` is a trivial constant-return `operator()` body inside the same verified family.
- Therefore the family is behaviorally real, but heterogeneous.

### 10. `0x226410` is a `map::at`-style shared-object lookup helper, not image reduction

- `0x226410` walks a tree rooted at `0x78(%rsi)` comparing `*(int32*)rdx` against node key `0x20(%node)`.
- On success it copies two qwords from `node+0x28/+0x30` into the destination object and bumps the shared-count if needed.
- On failure it throws `std::logic_error("map::at:  key not found")`.
- Therefore `0x226410` is a tree lookup plus shared-object materialization helper.
- It is not a pixel accumulator or image-tile reducer body.

### 11. `0x229ec0` is a state-materialization body over lookups and fixed-size record appends

- `0x229ec0` begins by:
  - looking up a shared object via `0x226410`
  - computing two int fields via `0x228db0`
  - storing those fields into `+0x60/+0x64`
  - storing one small enum-like value into `+0x450`
  - calling `0x224cc0`
- Its only visible loop walks 8-byte elements from `[state+0x20 .. +0x28]`.
- The loop appends 20-byte records whose last 12 bytes are zero-filled.
- The body returns through `%eax` with a constant `3`.
- Therefore the visible work in `0x229ec0` is state-object mutation and fixed-size record packing.
- No visible image-width×height traversal, per-pixel write pattern, or multi-source arithmetic blend body appears in this operator itself.

### 12. `0x228db0` and `0x22bee0` use the same pair-list / stereo-rect helper chain seen in depth-pair construction

- `0x228db0` performs:
  - tree walk over `0xa0(%r12)`
  - `0xe6ba0`
  - `0x264440`
  - `0x23faf0`
  - `0x241590`
  - `0x2415b0`
- The external scratch note:
  `/Volumes/Dev/lumen-phoenix-scratch/depth_pair_anchor_selection.md`
  already proves that:
  - `0x264440` is used as pair-list copy in the stereo-pair constructor path
  - `0x241590` copies primary stereo-rect params
  - `0x2415b0` copies secondary stereo-rect params
- `0x22bee0` starts with the same helper family:
  - `0xe6ba0`
  - `0xf3360`
  - `0x226410`
  - tree walks and node insertion/update
  - `0x210c10`
- Therefore at least one representative higher-group operator and one of its main helpers are already bounded to tree / pair-list / rect-param state work.
- This does not prove what later state consumers do, but it does bound these bodies themselves away from direct reducer closure.

### 13. `0x247390` builds thresholded coordinate/bitset state, not a visible image reducer

- `0x247390` allocates:
  - a bitset-like buffer sized from a count at `0x10(%rbx)`
  - two 32-byte coordinate tables assembled from 4-tuples of int fields
- It repeatedly reads coordinate pairs from indexed tables, computes:
  - `dx`
  - `dy`
  - `sqrt(dx*dx + dy*dy)`
- It compares that scalar distance against a float threshold from `0x38(%rbx)`.
- When the threshold passes, it sets membership bits in the allocated bitset.
- A second loop ORs those bits into an output mask.
- Therefore the visible body is geometric neighborhood / membership-mask construction over indexed coordinate tables.
- No visible image-tile buffer traversal or multi-source pixel blend loop appears in this operator itself.

### 14. Representative `State()` operators do not themselves expose the exact pre-fusion reducer body

- `0x229ec0` visibly performs lookup, field writes, and fixed-size record appends.
- `0x22bee0` visibly performs lookup, tree walk, allocation, and pair/rect helper dispatch.
- `0x247390` visibly performs coordinate-table assembly, scalar distance tests, and bitmask construction.
- `0x226410` is a lookup helper and `0x228db0` is a pair/rect state helper chain.
- Therefore the representative surfaces examined so far are state-materialization operators over helper structures, not direct proof of the `src1` / `src2` N-to-1 pixel reducer.

## Safe Conclusion

- Proven:
  the installed bundle exposes a concrete upstream `operator()` family associated with `runReferenceGroupCams` and `runHigherGroupCams`.
- Proven:
  the `+0x30` vtable slot for that family is the actual libc++ `std::__function::__func::operator()` slot.
- Proven:
  the callable signature stored in that family is `lt::CalibDataProcessor::State ()`.
- Proven:
  the final higher-group `operator()` slot is `0x247390`; `0x247380` is the preceding delete stub.
- Proven:
  the representative operators inspected so far (`0x229ec0`, `0x22bee0`, `0x247390`) are state-materialization bodies over lookup / pair-list / rect-param / bitset helpers.
- Still unproven:
  which, if any, of these state-returning runner `operator()` bodies dispatches the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future `src1` / `src2` reducer work no longer needs to search the entire binary for an upstream runner family or guess which slot is callable.

The next bundle-verified candidate surfaces above the visible wrapper layer are:

- reference-group `operator()` bodies:
  `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80`, `0x22bdf0`
- higher-group `operator()` bodies:
  `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, `0x22e1d0`, `0x247390`

These are proven `lt::CalibDataProcessor::State ()` runner surfaces. The representative bodies inspected so far are state-materializers, not direct reducer closure. That still does not close the reducer blocker, but it materially narrows the next decode surface toward later state consumers or deeper image-producing callees rather than these visible state operators themselves.

Follow-up runtime liveness is documented in
[lldb_calib_state_operator_runtime_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_calib_state_operator_runtime_four_zoom.md):
all thirteen `operator()` bodies are live in complete accepted bridge HDR renders
across `28mm`, `35mm`, `70mm`, and `150mm`. That follow-up adds entry counts and
caller context only; it does not change this static document's body-classification
boundary or close the reducer blocker.
