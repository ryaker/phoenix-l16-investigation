# Bundle Proof: Prefusion Block Geometry Helpers

## Scope

This note proves only what the installed `libcp.dylib` shows for the candidate block-geometry helper family named by prior prefusion evidence.

It proves:

- `0x25c990` is a two-float coordinate delta / scale helper
- `0x25ca70` is a geometry / shape acceptance predicate over float descriptor fields
- `0x25d050`, `0x25d060`, `0x25d070`, and `0x25d080` are block initialization / accessor helpers
- `0x25d090` propagates coordinate pairs into active block vectors, validates them through `0x25d2a0` and `0x25ca70`, and may clear the block-active byte
- `0x25d2a0` builds a descriptor from block-owned pair vectors and writes it into the block descriptor payload
- `0x25d4d0` is an 8-byte int-pair vector insertion / copy helper

It does not prove that the exact `src1` / `src2` N-to-1 reducer has been found.

Follow-up proof for the broader `0x258fe0` / `0x2598a0` feature-selection lane now lives in:
[bundle_proof_prefusion_feature_selection_lane.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_feature_selection_lane.md)

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Coordinate helper / geometry predicate disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25c990 --count 20' -o 'disassemble --start-address 0x25ca70 --count 260'`
- Block-helper family disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25d050 --count 170' -o 'disassemble --start-address 0x25d2a0 --count 250' -o 'disassemble --start-address 0x25d4d0 --count 260'`

## Proven Facts

### 1. `0x25c990` is a two-float coordinate delta / scale helper

- `0x25c994` loads the first float from `(%rdi)`.
- `0x25c998` loads the second float from `0x4(%rdi)`.
- `0x25c99d` subtracts the first float from `(%rsi)`.
- `0x25c9a1` subtracts the second float from `0x4(%rsi)`.
- `0x25c9a6` and `0x25c9aa` multiply both deltas by the scalar in `%xmm0`.
- `0x25c9ae` and `0x25c9b2` write the two floats back to `(%rdi)` and `0x4(%rdi)`.
- The function returns at `0x25c9b8`.

Therefore `0x25c990` visibly transforms one two-float coordinate pair in place. It does not expose image buffers, camera vectors, or a multi-source reduction loop.

### 2. `0x25ca70` is a geometry / shape acceptance predicate

- `0x25ca78..0x25cad7` reads float descriptor fields from `%rdi` offsets:
  `0x0`, `0x4`, `0x8`, `0xc`, `0x10`, `0x14`, `0x18`, `0x1c`, and `0x20`.
- `0x25cc00..0x25cc7c` performs cross-product-like sign tests using `ucomiss`, `seta`, and XOR checks.
- `0x25cca6`, `0x25cce7`, `0x25cd26`, and `0x25cd62` execute scalar square roots.
- `0x25ccbe`, `0x25ccf6`, `0x25cd32`, and `0x25cd71` call `acos`.
- `0x25cd86..0x25cdb3` compares the computed double values against a threshold and folds the result into `%al`.
- The function returns at `0x25cdba`.

Therefore `0x25ca70` visibly evaluates descriptor geometry and returns an accept / reject byte. It does not expose image-buffer traversal or N-to-1 camera reduction math.

### 3. `0x25d050` / `0x25d060` / `0x25d070` / `0x25d080` are block init / accessor helpers

- `0x25d050` zero-extends `%dl` and tail-jumps to `0x25cdf0`.
- `0x25d060` returns `rdi + 0x8`.
- `0x25d070` reads the block-active byte at `0x4(%rdi)` into `%al`.
- `0x25d080` writes `%sil` into the block-active byte at `0x4(%rdi)`.

These helpers provide block initialization, descriptor-pointer access, and active-byte access. They do not expose reducer work.

### 4. `0x25d090` propagates coordinate pairs into active block vectors and validates the block

- `0x25d0a8` checks the block-active byte at `0x4(%r12)` and exits if the block is inactive.
- `0x25d0b8..0x25d0e6` validates the requested level against two block-owned 24-byte-entry vector families rooted at `0x30..0x38` and `0x48..0x50`.
- `0x25d124` constructs the explicit error string:
  `"level > pyr.size()"`
- `0x25d157` compares a 0x2c-stride record field against the block target stored at `(%r12)`.
- `0x25d166` requires the same record's state field to equal `5`.
- `0x25d172..0x25d1ad` appends an 8-byte int pair into the vector family rooted at block offset `0x30`.
- `0x25d1c7..0x25d1ef` appends another 8-byte int pair into the vector family rooted at block offset `0x48`.
- `0x25d23e` calls `0x25d2a0`.
- `0x25d24c` calls `0x25ca70` on the block descriptor at `r12 + 0x8` when `0x25d2a0` succeeds.
- `0x25d259` clears the active byte at `0x4(%r12)` when the geometry predicate rejects.

Therefore `0x25d090` is visible active-block coordinate-pair propagation plus descriptor validation. It operates on 0x2c-stride records and block-owned pair vectors, not on image pixels.

### 5. `0x25d2a0` builds a block descriptor from pair-vector slices

- `0x25d2c6..0x25d2e1` copies the current-level pair-vector slices from block offsets `0x30` and `0x48` into stack vectors via `0xe0ae0`.
- `0x25d31b` and `0x25d335` call `0x25d4d0` to append next-level pair ranges when the next level exists.
- `0x25d346..0x25d35b` dispatches the four-pair case to `0x255b70`.
- `0x25d379..0x25d38e` dispatches the five-or-more-pair case to `0x255f30`.
- `0x25d3bb..0x25d3ce` optionally calls `0x2564d0` and rejects when the computed value fails the threshold comparison.
- `0x25d3d3`, `0x25d3df`, and `0x25d3e4` write the computed descriptor payload into the block descriptor region.
- The function returns a boolean in `%al`.

Therefore `0x25d2a0` visibly builds and validates a geometric descriptor from coordinate-pair vectors. It does not expose a pixel reducer.

### 6. `0x25d4d0` is an 8-byte int-pair vector insertion / copy helper

- `0x25d4f0..0x25d4fc` computes the incoming range length in 8-byte units.
- `0x25d500..0x25d56d` performs vector capacity / length arithmetic in 8-byte units.
- `0x25d600..0x25d64b` copies repeated 4-byte fields that together form 8-byte pair entries.
- `0x25d6a0` allocates new storage through `operator new` when growth is required.
- Later copy loops continue moving repeated 8-byte entries with paired 4-byte loads / stores.

Therefore `0x25d4d0` is vector insertion / copy support for int-pair entries. It does not expose image-buffer traversal or reducer arithmetic.

## Safe Conclusion

- Proven:
  `0x25c990` is a two-float coordinate delta / scale helper.
- Proven:
  `0x25ca70` is a geometry / shape acceptance predicate.
- Proven:
  `0x25d070` and `0x25d080` read and write the block-active byte at `+0x4`.
- Proven:
  `0x25d090` propagates validated coordinate pairs into active block vectors and may clear the active byte after geometry rejection.
- Proven:
  `0x25d2a0` builds a block descriptor from pair-vector slices.
- Proven:
  `0x25d4d0` is an int-pair vector insertion / copy helper.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer.
- Follow-up:
  the broader `0x258fe0` / `0x2598a0` feature-selection lane is now separately bounded in [bundle_proof_prefusion_feature_selection_lane.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_feature_selection_lane.md).

## Consequence For Blocker Work

Future anchor pre-fusion work should not cite `0x25c990`, `0x25ca70`, `0x25d090`, `0x25d2a0`, or `0x25d4d0` as reducer closure.

This helper family is now bounded as coordinate, geometry, active-block, descriptor, and int-pair vector support.

The reducer blocker remains elsewhere and may only close when a different downstream surface is proven to have real N-to-1 input shape or reduction math.
