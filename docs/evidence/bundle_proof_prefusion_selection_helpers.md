# Bundle Proof: Prefusion Selection Helpers and Bitset Acceptance Path

## Scope

This note proves only what the installed `libcp.dylib` shows for the next helper tranche beneath the already-bounded dispatch / selector layer.

It proves:

- `0x249020` is a selection-offset helper used to permute a temporary integer index vector inside `0x2416d0`
- `0x247900` is a 32-bit vector range-copy / growth helper, not image math
- `0x249410` materializes an array of repeated 24-byte bitset entries copied from a source bitset container
- the visible continuation of `0x2416d0` after these helpers is still bitset-driven record acceptance and `record+0x24 = 5` promotion
- `0x5670` is a generic range / chunk executor; it is not the missing reducer

Follow-up callback-identity proof now lives in:
[bundle_proof_prefusion_callback_reuses_known_runner.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_callback_reuses_known_runner.md)

That follow-up shows the callback object built after this helper tranche uses an
adjacent `SparseLNR::markInliers(..., void(int,int,int))` table whose `+0x30`
body is `0x247390`. It is not the `runHigherGroupCams::$_12`
`CalibDataProcessor::State()` runner; the corrected terminal State body is
`0x22e1d0`.

This note does not by itself prove that the exact `src1` / `src2` N-to-1 reducer has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Selector / helper disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x2416d0 --count 1800' -o 'disassemble --start-address 0x249020 --count 1800' -o 'disassemble --start-address 0x247900 --count 1800' -o 'disassemble --start-address 0x249410 --count 1800'`
- Executor helper disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x5670 --count 400'`

## Proven Facts

### 1. `0x249020` is a selection-offset helper, not a visible image reducer

- Inside `0x2416d0`, the call site is:
  `0x2419b9: callq 0x249020`
- Immediately after that call, the return value in `%rax` is used only as a swap offset inside the temporary integer index vector:
  - `movl (%r12), %ecx`
  - `movl (%r12,%rax,4), %edx`
  - swap those two 32-bit entries
- The body of `0x249020` repeatedly calls `0x249210`.
- `0x249210` mutates 32-bit words in caller-owned state and folds them into bounded integer results using constants:
  - `0xbc8f1391`
  - `0xadc8`
  - `0xbc8f`
  - `0xd47`
- No image-width x image-height loops, pixel buffers, or visible image-object fields appear in `0x249020` / `0x249210`.
- Therefore the visible role of `0x249020` is selection-index generation for permutation of a candidate-index list, not direct reduction math.

### 2. `0x247900` is a 32-bit vector range-copy / growth helper

- `0x247900` computes its range lengths in units of 4-byte elements.
- Its visible operations are vector-capacity and copy mechanics:
  - capacity checks
  - `operator new`
  - `memcpy`
  - `memmove`
  - bulk `movups` copies
  - scalar 32-bit element moves
- At the `0x2416d0` call site:
  `0x241a09: callq 0x247900`
  the helper receives the temporary integer-vector object at `-0xd0(%rbp)` and a source range derived from the selected index list.
- No visible image-state fields such as `record+0x24`, `record+0x28`, `PipelineCache`, or image buffer pointers are read or written inside `0x247900`.
- Therefore `0x247900` is a generic integer-vector copy / insertion surface, not a hidden merge kernel.

### 3. `0x249410` materializes repeated 24-byte bitset entries from a source bitset container

- At function entry, `0x249410` zero-initializes the destination vector object at `%r14`.
- It allocates:
  `count * 0x18`
  bytes for the destination element array, so the visible element stride is 24 bytes.
- For each 24-byte destination entry, it:
  - zero-initializes the 24-byte entry
  - reads the source bit-count and source word-storage pointer from the source container passed in `%rdx`
  - allocates 64-bit word storage when the source bitset has payload
  - copies word data with `memmove`
  - masks trailing high bits in the last word when the active bit-count is not a multiple of 64
- The visible per-entry layout is three 8-byte fields, with the first field used as a word-storage pointer and the remaining two fields used as size / capacity-like metadata.
- At the `0x2416d0` call site:
  `0x241b40: callq 0x249410`
  the arguments are:
  - destination vector at `-0x108(%rbp)`
  - count from `%r12d`
  - source bitset container at `-0x120(%rbp)`
- Therefore `0x249410` is a bitset-entry materialization helper, not a direct image reducer.

### 4. The visible continuation of `0x2416d0` remains bitset-driven record acceptance and state promotion

- After `0x249410`, `0x2416d0` allocates a 0x48-byte vtable-backed object and stores into it pointers to:
  - the materialized bitset-entry vector at `-0x108(%rbp)`
  - the selected-count slot at `-0xa8(%rbp)`
  - the copied integer-vector object at `-0xd0(%rbp)`
  - upstream arguments from `-0x158(%rbp)` and `-0x148(%rbp)`
  - local scratch slots at `-0xa0(%rbp)`, `-0x84(%rbp)`, and `-0x88(%rbp)`
- Control then passes onward through `0x5670`.
- After that handoff returns, the visible body of `0x2416d0` still does not expose pixel accumulation.
- Instead it:
  - walks the selected index list
  - loads bit words from the materialized 24-byte entry array
  - tests candidate bits
  - writes `record+0x24 = 5` for accepted selected records
- The fallback paths later in the function also remain state-promotion loops over the selected integer indices, again writing only:
  `record+0x24 = 5`
- Therefore the visible post-helper continuation is still candidate acceptance / promotion logic, not the missing N-to-1 reducer.

### 5. `0x5670` is a generic range / chunk executor, not the missing reducer

- `0x5670` computes a rounded chunk count from its integer range arguments.
- If the computed work count is small enough, it directly invokes a callback through a callable stored in the passed context.
- Otherwise it allocates a 0x30-byte job object, fills it with:
  - start
  - end
  - step
  - callback/context pointers
  - computed chunk count
  and dispatches through another helper path.
- The visible body of `0x5670` is range partitioning, callback dispatch, and cleanup.
- Therefore `0x5670` itself is still only an executor / chunking helper.
- The callback-object identity is now separately proven in:
  [bundle_proof_prefusion_callback_reuses_known_runner.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_callback_reuses_known_runner.md)

## Safe Conclusion

- Proven:
  `0x249020`, `0x247900`, and `0x249410` are all selector-support helpers.
- Proven:
  the visible continuation of `0x2416d0` after those helpers remains bitset-driven acceptance and record-state promotion.
- Proven:
  `0x5670` is only a generic executor / chunking helper.
- Proven:
  follow-up bundle proof now shows the callback object reached after this helper
  tranche is not the `CalibDataProcessor::State()` runner; it is the adjacent
  `SparseLNR::markInliers` callback table with body `0x247390`.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work can now treat this helper tranche as bounded:

1. selection-offset helper `0x249020`
2. integer-vector range-copy helper `0x247900`
3. bitset-entry materializer `0x249410`
4. generic range executor `0x5670`
5. callback-object identity, which now separately resolves to the adjacent
   `SparseLNR::markInliers` / `0x247390` callback table, not the corrected
   `runHigherGroupCams::$_12` / `0x22e1d0` State runner

This selector branch no longer introduces a fresh unresolved callback surface.

The reducer blocker remains elsewhere, not in this already-bounded selector-support path.
