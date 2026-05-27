# Bundle Proof: IRAMP Source-Record Composition Helpers

## Scope

This note proves installed-bundle field movement and arithmetic boundaries for
the helper chain reached by the IRAMP source-record constructors:

- `0x23faf0`
- `0x264980`
- `0x264460`

It builds on:

- [bundle_proof_iramp_source_record_constructors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_source_record_constructors.md)
- [bundle_proof_iramp_row_composition_matrix_chain.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_row_composition_matrix_chain.md)

It does not prove public calibration names for the source-record fields.

It does not prove the LRI calibration-block origin or full later payload-field
semantics of `state+0x448`, the LRI calibration-block origin of `state+0xe0`,
or the object reached by the `0x268480` virtual map-provider path.

It does not rename these helpers as a public camera-model transform. The safe
names here are only installed-bundle operational descriptions.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Disassembly commands:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x23faf0 --count 760'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x264460 --count 360'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x264980 --count 360'`

## Proven Facts

### 1. `0x23faf0(dst, left, right)` is a real source-record composition helper

At entry, `0x23faf0` saves its three arguments:

- `0x23fb04`: saves `right` from `rdx`
- `0x23fb07`: saves `left` from `rsi`
- `0x23fb0e`: saves `dst` from `rdi`

The function first copies the right-hand source-record-shaped input into
`dst`.

Instruction anchors:

- `0x23fb1b..0x23fb6d`: copies scalar / SIMD fields through `+0x60`
- `0x23fb91..0x23fc1b`: copies the vector-managed region at `+0x68/+0x70/+0x78`
- `0x23fc34..0x23fc59`: copies fields from `right+0x80..+0xa0`

It then snapshots current output regions before performing composition math:

- `0x23fc62..0x23fca1`: snapshots output `+0x00..+0x2c`
- `0x23fca7..0x23fccb`: snapshots output `+0x30..+0x60`
- `0x23fd56..0x23fd77`: snapshots output `+0x80..+0xa0`

It reads left-hand record fields immediately before the first large SIMD
composition block:

- `0x23fd85`: reads `left+0x0c`
- `0x23fd8a`: reads `left+0x18`
- `0x23fd90`: reads `left+0x00`
- `0x23fd94`: reads `left+0x04`
- `0x23fd99`: reads `left+0x10`
- `0x23fd9e`: reads `left+0x1c`
- `0x23fda4`: reads `left+0x08`
- `0x23fdaa`: reads `left+0x14`
- `0x23fdaf`: reads `left+0x20`

The block at `0x23fdb5..0x23fffb` performs multiply / add / shuffle arithmetic
over left-record fields and the current output fields. Safe statement:
`0x23faf0` is not just a wrapper or copy helper; it performs installed-bundle
source-record composition math.

### 2. `0x23faf0` invokes three offset-and-scale adjustment pairs

After the first composition block, `0x23faf0` calls `0x264980` and `0x264460`
in three repeated pairs using fields from the right-hand record:

- `0x240002..0x24001a`: calls `0x264980` with scalar arguments from
  `right+0x38/+0x3c`
- `0x24001f..0x240031`: calls `0x264460` with scale-pair pointer `right+0x30`
- `0x240036..0x24004e`: calls `0x264980` with scalar arguments from
  `right+0x48/+0x4c`
- `0x240053..0x240065`: calls `0x264460` with scale-pair pointer `right+0x40`
- `0x24006a..0x240082`: calls `0x264980` with scalar arguments from
  `right+0x74/+0x78`
- `0x240087..0x240099`: calls `0x264460` with scale-pair pointer `right+0x7c`

It then writes adjusted fields back into the output record:

- `0x24009e..0x2400de`: writes output `+0x00..+0x2c`
- `0x2400e3..0x240102`: writes output `+0x30..+0x50`
- `0x240105..0x240109`: writes output `+0x54..+0x63`
- `0x240155..0x24016a`: writes vector ownership fields at `+0x68/+0x70/+0x78`
- `0x24017e..0x240192`: writes output `+0x80..+0xa0`

Finally, `0x23faf0` performs a second large SIMD composition block and writes
the secondary region:

- `0x2402d4..0x240488`: multiply / add / shuffle arithmetic over current output
  fields and right-record fields
- `0x240490..0x2404b2`: writes output `+0x30..+0x50`
- `0x2404b5..0x2404c9`: returns `dst`

Safe statement: `0x23faf0(dst, left, right)` initializes `dst` from `right`,
combines `left` with current output fields, applies three installed-bundle
offset / scale adjustment pairs, finalizes a secondary output region, and
returns `dst`.

### 3. `0x264980(dst, src, dx, dy)` is a bounded two-axis field-shift helper

`0x264980` first copies the same source-record-shaped layout from `src` to
`dst`.

Instruction anchors:

- `0x26499e..0x2649e8`: copies fields through `+0x60`
- `0x2649fb..0x264a5e`: copies the vector-managed region at `+0x68/+0x70/+0x78`
- `0x264a5e..0x264a82`: copies fields through `+0x80..+0xa0`

It then adjusts exactly six scalar fields:

```text
dst+0x08 = src+0x08 - dx
dst+0x14 = src+0x14 - dy
dst+0x88 = src+0x88 - dx
dst+0x94 = src+0x94 - dy
dst+0x54 = src+0x54 + dx
dst+0x58 = src+0x58 + dy
```

Instruction anchors:

- `0x264a89..0x264a97`: subtracts `dx` from `src+0x08`
- `0x264a9c..0x264aaa`: subtracts `dy` from `src+0x14`
- `0x264aaf..0x264abb`: subtracts `dx` from `src+0x88`
- `0x264ac3..0x264acf`: subtracts `dy` from `src+0x94`
- `0x264ad7..0x264adc`: adds `dx` to `src+0x54`
- `0x264ae1..0x264ae6`: adds `dy` to `src+0x58`

Safe statement: `0x264980` is no longer an unknown helper. It copies the record
shape and applies a proven two-axis field shift to six fields.

### 4. `0x264460(dst, src, scale_pair)` is a bounded positive two-axis scale helper

`0x264460` reads two floats from `scale_pair`.

If both values are exactly `1.0`, it takes a copy fast path:

- `0x26448a..0x2644a2`: compares both scale values against `1.0`
- `0x2644a8..0x264584`: copies the source-record-shaped layout

Otherwise, both scale values must be positive:

- `0x26458c..0x2645a0`: checks both scale values against zero
- `0x26488f..0x2648b9`: throws `Scale has to be a positive value.`

The non-copy path scales selected fields and writes the same output layout:

- `0x264687..0x2646d7`: scales selected fields in `+0x00..+0x20`
- `0x264788..0x2647c8`: scales selected fields in `+0x80..+0xa0`
- `0x2647cd..0x264835`: scales / writes `+0x54..+0x63` and copies the
  vector-managed region
- `0x2647f0..0x264872`: writes final output fields

Safe statement: `0x264460` is no longer an unknown helper. It is a positive
two-axis scale helper over the source-record layout, with an exact `(1.0, 1.0)`
copy fast path.

## Safe Conclusion

- Proven:
  `0x23faf0` is an installed-bundle source-record composition helper. It copies
  `right` into `dst`, performs SIMD composition math using `left` and current
  output fields, applies three proven helper pairs, writes adjusted output
  regions, and returns `dst`.
- Proven:
  `0x264980` copies a source-record-shaped layout and applies a two-axis shift
  to exactly six scalar fields.
- Proven:
  `0x264460` is a positive two-axis scale helper over the source-record layout,
  with an exact `(1.0, 1.0)` copy fast path.
- Still unproven:
  public calibration names for the source-record fields, LRI calibration-block
  origins for the source records, and the semantic meaning / origin of the map
  returned through the `0x268480` virtual slot path.

## Consequence For Blocker Work

Future work should not treat `0x23faf0`, `0x264980`, or `0x264460` as opaque
unknowns.

The remaining producer-side transform-record blocker is now narrower:

```text
known:
  source-record constructors -> 0x23faf0 composition -> 0x264980 shifts
  -> 0x264460 scales -> 0x25e0c0 matrix-chain row producer

still unknown:
  public calibration names, LRI block origins, and map-provider semantics
```
