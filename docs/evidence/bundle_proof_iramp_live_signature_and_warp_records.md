# Bundle Proof: IRAMP Live Signature And Warp-Record Consumption

## Scope

This note proves only what the installed `libcp.dylib` shows about the live
caller, argument pack, and consumer path for IRAMP's source vector and
`PipelineCache+0x258` record vector.

It proves:

- `PipelineCache::processLevel0` at `0x3ec770` passes concrete `PipelineCache`
  member offsets into `0x365960`
- `PipelineCache+0x258` is the fifth argument to `0x365960`
- `0x365960` checks the `PipelineCache+0x258` record count against the
  `PipelineCache+0x270` source-vector count
- `0x365960` packs both vectors into the closure passed to `0x3661b0`
- `0x3661b0` consumes the `PipelineCache+0x258` records by matching source index
  and reads fields from the selected `0x50`-byte record while building the
  transformed pair grid

It does not prove runtime vector counts for new zoom tiers.

It does not prove the exact closed-form algebra for the transform fields.

It does not prove the exact N-to-1 reducer behind `src1` / `src2`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- IRAMP caller:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ec770 --count 120'`
- IRAMP setup / closure pack:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x365960 --count 230' -o 'disassemble --start-address 0x365df0 --count 260'`
- IRAMP consumer:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3661b0 --count 380' -o 'disassemble --start-address 0x3669f0 --count 170' -o 'disassemble --start-address 0x366b00 --count 260'`

## Proven Facts

### 1. `processLevel0` passes concrete `PipelineCache` fields into IRAMP

The caller at `0x3ec770` first verifies both required state bytes:

- `0x3ec783..0x3ec78a` checks `PipelineCache+0x190`
- `0x3ec790..0x3ec797` checks `PipelineCache+0x1f0`
- if either is zero, `0x3ec837` throws
  `Requested PipelineCache::processLevel0 before initResamp()!`

When initialized, the call setup at `0x3ec7ac..0x3ec7da` is:

- `rsi = *(PipelineCache+0x238)`
- `rdx = *(PipelineCache+0x248)`
- `xmm0 = *(float *)(PipelineCache+0x1e8)`
- `rcx = PipelineCache+0x270`
- `r8 = PipelineCache+0x258`
- `rdi = local output image`
- `r9 = original ROI rectangle`
- `call 0x365960`

Therefore the installed bundle directly ties the live IRAMP call to these
member offsets:

- `+0x238`: first anchor-side image-generator argument
- `+0x248`: second anchor-side image-generator argument
- `+0x270`: source image-generator vector argument
- `+0x258`: paired record / warpfield-vector argument
- `+0x1e8`: scalar scale argument

### 2. `0x365960` validates `+0x258` count against `+0x270` count

At function entry:

- `r8` is saved as the fifth argument, then retained as the `+0x258` vector
  pointer
- `rcx` is saved as the fourth argument, then retained as the `+0x270` vector
  pointer

The guard at `0x3659a8..0x3659d0` compares the two counts:

- `0x3659a8..0x3659c0` computes a normalized count from the fifth argument's
  begin/end pair
- that normalization matches the previously proven `0x50` element stride of
  `PipelineCache+0x258`
- `0x3659c2..0x3659c9` computes the fourth argument's count from a 16-byte
  shared-ptr-like vector stride
- `0x3659cd..0x3659d0` compares the two counts
- mismatch jumps to `0x36608b`, whose diagnostic is
  `warpfield count does not match the source image count!`

Therefore the `PipelineCache+0x258` vector is not dead setup state. It is a live
IRAMP argument whose count must match the source image-generator vector at
`PipelineCache+0x270`.

### 3. `0x365960` packs both vectors into the `0x3661b0` closure

The closure region begins at stack address `rbp-0x158` and is passed to
`0x3661b0` at `0x365f41..0x365f4b`.

The relevant closure writes are:

- `0x365ea3`: closure `+0x08` gets `src1`
- `0x365eb1`: closure `+0x10` gets `src2`
- `0x365eb8`: closure `+0x18` gets the source image-generator vector pointer
- `0x365ec6`: closure `+0x20` gets the `+0x258` record / warpfield vector
  pointer
- `0x365edb`: closure `+0x38` gets the output image pointer

On the non-empty-ROI path:

- `0x365efe..0x365f0f` reads the four ROI ints
- `0x365f21..0x365f3c` sizes the output image to the ROI width and height
- `0x365f41..0x365f4b` calls `0x3661b0` with `rdi = &closure` and
  `rsi = ROI`

Therefore the source vector and the `PipelineCache+0x258` record vector enter
the inner IRAMP body through closure slots `+0x18` and `+0x20`.

### 4. `0x3661b0` iterates the source vector and selects the matching `0x50` record

At `0x366a50..0x366ae4`, `0x3661b0` reads closure `+0x18`:

- `0x366a50`: loads closure `+0x18`
- `0x366a54..0x366a61`: reads source-vector begin/end and computes the count
- `0x366ae1..0x366ae4`: exits the source-vector path if begin equals end

Inside the source-index loop:

- `0x366b1c`: loads closure `+0x20`
- `0x366b20`: reads the `+0x258` vector begin pointer into `r14`
- `0x366b23..0x366b34`: uses the same source index to select a source
  image-generator from the `+0x18` vector
- `0x366b66..0x366b75`: computes `index * 0x50` and selects the matching
  record from the `+0x258` vector

Therefore the installed bundle uses one `0x50` record from `PipelineCache+0x258`
for each source image-generator entry from `PipelineCache+0x270`.

### 5. The selected `0x50` record feeds the transformed-pair-grid math

After selecting the matching `0x50` record, `0x3661b0` takes field addresses
from that record:

- `record+0x48` at `0x366b92..0x366b97`
- `record+0x4c` at `0x366b9e..0x366ba3`
- `record+0x40` at `0x366baa..0x366baf`
- `record+0x10` at `0x366bb6..0x366bbb`
- `record+0x20` at `0x366bc2`
- `record+0x30` at `0x366bc7`

The transformed-grid loop at `0x366c70..0x366d59` then:

- reads each first-grid pair
- bounds-checks it against the source image dimensions at `+0x30/+0x34`
- scales coordinates through fields `record+0x48/+0x4c`
- samples a float map through field `record+0x40`
- combines the sampled scalar and scaled coordinates with vector fields at
  `record+0x10/+0x20/+0x30`
- writes transformed int32 pairs into the second grid
- writes sentinel `0x8000000080000000` for rejected pairs

Therefore the `PipelineCache+0x258` records are live per-source transform
records for IRAMP's second pair-grid construction.

## Safe Conclusion

- Proven:
  `PipelineCache+0x258` is passed from `processLevel0` into `0x365960` as the
  live paired record / warpfield-vector argument.
- Proven:
  `0x365960` validates the `PipelineCache+0x258` record count against the
  `PipelineCache+0x270` source-vector count and packs both vectors into the
  `0x3661b0` closure.
- Proven:
  `0x3661b0` iterates the source vector and consumes the matching
  `PipelineCache+0x258` `0x50`-byte record while producing the transformed pair
  grid.
- Still unproven:
  the closed-form algebra and public field names for the transform record.
- Still unproven:
  the exact N-to-1 reducer behind `src1` / `src2`.

## Consequence For Blocker Work

The `PipelineCache+0x258` vector should no longer be treated as merely a
construction artifact. It is the live per-source transform / warpfield-record
vector consumed by IRAMP.

This narrows the pair-grid blocker: future work should decode the fields of the
already-located `0x50` records created in `initResAmp` and consumed at
`0x366b92..0x366d59`.

This does not close `CLM-PREFUSION-002`; those records are paired with the
`PipelineCache+0x270` contributor vector and do not expose the upstream reducer
behind `src1` / `src2`.
