# Bundle Proof: First Heavy Consumers Beneath Anchor Pre-Fusion

## Scope

This note proves only what the installed `libcp.dylib` shows for the first heavier consumers reached beneath the already-bounded post-`State()` helper chain.

It proves:

- helper family `0x251dd0`, `0x251e00`, `0x251f60`, and `0x252970` is pyramid / descriptor / coordinate-pair support code
- `0x243cd0` is a coarse geometric projection-and-validity stage over a 4-pixel lattice
- `0x244560` is a feature / pyramid / descriptor consumer that builds and replaces multiple state blocks and vectors, with feature-size guardrails
- `0x245a40` is a candidate-filtering / mask / coordinate-pair consumer that also emits multiple descriptor blocks after three scale passes

It does not prove that the exact `src1` / `src2` N-to-1 reducer has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Heavy-consumer disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x244560 --count 1500' -o 'disassemble --start-address 0x245a40 --count 1600' -o 'disassemble --start-address 0x243cd0 --count 900'`
- Helper disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x251dd0 --count 220' -o 'disassemble --start-address 0x251e00 --count 260' -o 'disassemble --start-address 0x252970 --count 260' -o 'disassemble --start-address 0x25d050 --count 220'`

## Proven Facts

### 1. `0x251dd0` is a zero-initializer for a fixed 0x90-byte descriptor block

- `0x251dd0` zeroes:
  - `(%rdi)`
  - `0x30(%rdi)`
  - `0x40(%rdi)`
  - `0x50(%rdi)`
  - `0x60(%rdi)`
  - `0x70(%rdi)`
  - `0x80(%rdi)`
- The highest written offset is `0x80`.
- Therefore `0x251dd0` is a pure fixed-size zero-initializer for the descriptor object later consumed by `0x244560`.

### 2. `0x251e00` installs two validated descriptor payloads and carries an explicit `"image size mismatch!"` guard

- `0x251e00` stores:
  - `esi` at `0x10(%rbx)`
  - `rdx` at `(%rbx)`
  - `rcx` at `0x8(%rbx)`
  - one `xmm` block from `(%r8)` at `0x20(%rbx)`
- It then derives two source pointers from:
  - `0x8(%rdx) - 0x30`
  - `0x8(0x8(%rbx)) - 0x30`
- For each derived pointer it calls:
  - `0x212c40`
  - `0x251f60`
  - `0xf340`
- `0x251f60` compares two derived image-size fields and, on mismatch, throws with the explicit string:
  `"image size mismatch!"`
- Therefore `0x251e00` is descriptor-installation code over two validated size-matched payloads, not image reduction.

### 3. `0x252970` is ref/src pyramid and coordinate-pair support code with explicit null and size guards

- `0x252970` rejects null inputs with the explicit string:
  `"ref/src pyr must not be null"`
- It rejects ref/src pyramid-size mismatch with the explicit string:
  `"ref/src pyr size mismatch!"`
- It compares the number of 16-byte entries in the two input pyramid-like vectors and requires equality before continuing.
- It ensures capacity in the output vector at `r15`.
- It reads two scale factors from `(%r13)` and `0x4(%r13)`.
- It multiplies integer fields from the current source record by those scale factors, converts back to ints, and stores them as a pair.
- It then iterates through coarser-to-finer support records via repeated calls to `0x252110`, updating and appending int-pair results into 8-byte output slots.
- Therefore `0x252970` is a pyramid-backed coordinate-pair propagation helper, not a pixel reducer.

### 4. `0x243cd0` is a coarse projection-and-validity stage over a 4-pixel lattice

- `0x243cd0` computes quarter-resolution dimensions from the shared object at `0x1c0(%r13)` by dividing width and height by 4.
- It then creates a local output object at `r15` and checks `0x14(%r15)` before entering the main loop.
- The visible nested loops increment:
  - the outer row index by `1`, while also advancing a row-scale accumulator by `4`
  - the inner column index by `1`, while also advancing a column-scale accumulator by `4`
- Inside the inner loop it:
  - scales row/column coordinates by floats at `0x1b8(%r13)` and `0x1bc(%r13)`
  - samples a scalar map through the object at `0x1b0(%r13)`
  - broadcasts that scalar and applies four-vector multiply-adds using the blocks at:
    - `0x170(%r13)`
    - `0x180(%r13)`
    - `0x190(%r13)`
    - `0x1a0(%r13)`
  - converts projected results back to ints
  - bounds-checks against the rectangle in `r12`
- On out-of-bounds or failed cases it writes zero bytes into the mask buffer at `0x20(%r15)`.
- On valid cases it writes 16-byte records into the table whose base is held at `-0xb8(%rbp)`.
- Therefore the visible core of `0x243cd0` is geometric projection, bounds checking, record emission, and mask-byte clearing over a 4-pixel lattice.

### 5. `0x244560` consumes pyramids and feature-like records, not a direct pixel-blend loop

- `0x244560` requires a callable at `0x220(%r14)` and throws `std::__1::bad_function_call` if it is absent.
- It also requires the vector at `0x3c8(%r14)->0x60..0x68` to be non-empty; otherwise it throws with the explicit string:
  `"must compute ref features first"`
- It stores the incoming float at `0x238(%r14)` and derives a boolean flag at `0x3c0(%r14)`.
- It calls:
  - `0x2443d0`
  - `0x242f40`
  - `0x251dd0`
  - `0x251e00`
  - `0x251e00`
  - `0x252970`
- The call into `0x252970` uses the difference between:
  - `state+0x10/+0x14`
  - and `state+0x244/+0x248`
- If earlier prerequisites fail or if the function falls back before feature construction, it fills the vector at `0x1e8..0x1f0` with repeated qword `0xBF800000BF800000`, which is the float pair `(-1.0, -1.0)`.
- The visible body repeatedly calls `0x25d050` and installs the returned blocks into four state regions:
  - `0x300 .. 0x328`
  - `0x330 .. 0x358`
  - `0x360 .. 0x388`
  - `0x390 .. 0x3b8`
- It branches among three deeper helper families depending `0x234(%r14)` and current level position:
  - `0x248580`
  - `0x248960`
  - `0x2481a0`
- It stores those results into the vector family rooted at `0x1d0(%r14)`.
- It then walks 0x2c-stride records and classifies by the value at `record+0x28`, accumulating counts into the destination object at offsets:
  - `+0x14`
  - `+0x18`
  - `+0x1c`
- It calls `0x25d090` on the state blocks at `0x300` and `0x360`.
- `0x25d090` itself:
  - checks the block-active byte at `+0x4`
  - validates the requested level against pyramid size
  - copies int pairs from 0x2c-stride feature records into block-owned vectors
  - may clear the block-active byte back to `0`
- `0x2457c0`, which `0x244560` calls before returning, again fills `0x1e8..0x1f0` with `(-1.0, -1.0)`, then walks three levels and writes scaled coordinate pairs only for records whose field at `+0x24` equals `5`.
- `0x2457c0` throws the explicit string:
  `"ref/src features size mismatch"`
  if the compared feature sizes differ.
- Therefore the visible work in `0x244560` is ref/src pyramid validation, feature-record classification, coordinate-pair output, and multi-block state installation.

### 6. `0x245a40` is a three-pass candidate-filtering and coordinate-pair emitter over masks and scalar thresholds

- `0x245a40` also requires the callable at `0x220(%rbx)` and throws `std::__1::bad_function_call` if it is absent.
- It reads dimensions from the shared object at `0x1c0(%state)` and computes multiple float thresholds and windows from those dimensions plus `0x238(%state)`.
- It calls `0x243cd0`, placing the produced object on the stack.
- It then runs an outer loop for exactly three passes:
  - the pass index lives in `%rbx`
  - each pass computes a scale factor via `exp2`
- For each pass it walks the per-level record vector at `0x3c8(%state)->0x60`, with each record advanced by `0x24` bytes.
- In the inner loop it:
  - scales two float coordinates from the record by the current pass scale
  - converts them to ints
  - checks a byte mask from the stack object produced by `0x243cd0`
  - checks x/y windows against float bounds
  - checks that the sampled entry in the source map at `0x1c0(%state)->0x20` is non-zero
  - writes `0` or `1` into the record byte at `record+0x20` depending on acceptance or rejection
- For accepted candidates it compares the sampled scalar against `0x238(%state)` with an additional threshold window, calls `0x25c990`, and appends multiple `(x, y)` int pairs into stack-backed output vectors.
- After the three passes it repeatedly calls `0x25d050` and installs blocks into the same family of state regions used by `0x244560`:
  - `0x300 .. 0x328`
  - `0x330 .. 0x358`
  - `0x360 .. 0x388`
  - `0x390 .. 0x3b8`
- Therefore the visible body of `0x245a40` is candidate filtering, record marking, coordinate-pair emission, and descriptor-block installation across three scales.

### 7. The visible heavy-consumer layer still does not expose a direct N-to-1 pixel accumulation loop

- `0x244560` is guarded by:
  - pyramid and image-size checks
  - feature-size checks
  - ref-feature availability checks
- `0x245a40` is guarded by:
  - mask-byte checks
  - bounds checks
  - scalar-threshold checks
  - three-scale candidate iteration
- Both functions spend their visible work on:
  - pyramid descriptors
  - feature-like 0x2c records
  - coordinate-pair vectors
  - mask bytes
  - per-level counters
  - installed state blocks at `0x300..0x3b8`
- No visible image-width x image-height multi-source pixel accumulation or blend loop appears in either `0x244560` or `0x245a40` themselves.

## Safe Conclusion

- Proven:
  the first heavier consumers reached from the anchor pre-fusion path are still feature / pyramid / coordinate / mask surfaces.
- Proven:
  `0x243cd0` is a coarse geometric projection-and-validity stage over a 4-pixel lattice.
- Proven:
  `0x244560` and `0x245a40` both build and replace multiple descriptor blocks and vectors rooted in the state ranges `0x300..0x3b8`.
- Proven:
  the visible work in these functions is coordinate-pair, feature-record, mask, and descriptor logic rather than a direct exposed N-to-1 pixel blend loop.
- Still unproven:
  which deeper downstream helper or consumer finally closes the exact `src1` / `src2` reducer.

## Consequence For Blocker Work

Future anchor pre-fusion work can now treat the first heavy-consumer layer as bounded:

1. helper family `0x251dd0`, `0x251e00`, `0x251f60`, `0x252970`
2. coarse projection stage `0x243cd0`
3. heavy consumers `0x244560` and `0x245a40`

Follow-up bundle proofs have since bounded the originally listed deeper helper families away from reducer closure:

- `0x248580`
- `0x248960`
- `0x2481a0`
- `0x241fd0`
- `0x25d090`
- `0x25c990`

The current reducer path is therefore not this original candidate list. Use [BLOCKER_PATHS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/BLOCKER_PATHS.md) for the active path.
