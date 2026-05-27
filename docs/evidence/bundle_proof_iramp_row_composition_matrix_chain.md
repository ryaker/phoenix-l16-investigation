# Bundle Proof: IRAMP Row Composition Matrix Chain

## Scope

This note proves the installed-bundle row-composition structure inside
`0x25e0c0`, the helper reached from the final IRAMP `0x50` record composer.

It builds on:

- [bundle_proof_iramp_record_producer_scale_and_dispatch.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_record_producer_scale_and_dispatch.md)

It does not prove public calibration names for the source-record fields.

Later evidence proves `0x9db20` is a 4x4 double matrix inverse wrapper.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Row-composition body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e0c0 --count 220'`
- 4x4 double matrix multiply helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25ec70 --count 260'`
- Adjacent 3x3/4x4 helper context:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x9d970 --count 260'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x9db20 --count 260'`
- `0x9db20` inverse proof:
  [bundle_proof_iramp_9db20_matrix_inverse.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_9db20_matrix_inverse.md)

## Proven Facts

### 1. `0x25ec70` is a 4x4 double matrix multiply helper

`0x25ec70(dst, lhs, rhs)` treats `lhs`, `rhs`, and `dst` as four rows of four
doubles, with row stride `0x20`.

At `0x25ec74..0x25ec99`, it preloads the four `rhs` rows:

- `rhs+0x00/+0x10`
- `rhs+0x20/+0x30`
- `rhs+0x40/+0x50`
- `rhs+0x60/+0x70`

At `0x25ec9e..0x25ed59`, it loops over `lhs` rows in `0x20`-byte steps until
`rax == 0x80`.

For each row, it computes:

```text
dst[row] =
  lhs[row][0] * rhs[0] +
  lhs[row][1] * rhs[1] +
  lhs[row][2] * rhs[2] +
  lhs[row][3] * rhs[3]
```

The first two columns are written at `dst+row+0x00`; the second two columns are
written at `dst+row+0x10`.

Therefore `0x25ec70` is safely usable as:

```text
dst = lhs * rhs
```

where all three matrices are 4x4 double matrices.

### 2. `0x25e0c0` builds two 4x4 double matrices from the first source record

For input `source_a = rsi`, `0x25e0c0` builds one 4x4 matrix from fields
`source_a+0x00..0x20`, with a final row `[0, 0, 0, 1]`.

It also builds one 4x4 matrix from fields `source_a+0x30..0x50` and
`source_a+0x24..0x2c`, with a final row `[0, 0, 0, 1]`.

The exact observed layout is:

```text
source_a_primary =
  [ +0x00, +0x04, +0x08, 0 ]
  [ +0x0c, +0x10, +0x14, 0 ]
  [ +0x18, +0x1c, +0x20, 0 ]
  [ 0,     0,     0,     1 ]

source_a_secondary =
  [ +0x30, +0x34, +0x38, +0x24 ]
  [ +0x3c, +0x40, +0x44, +0x28 ]
  [ +0x48, +0x4c, +0x50, +0x2c ]
  [ 0,     0,     0,     1     ]
```

The field names above are offsets only, not semantic names.

### 3. `0x25e0c0` builds the same two 4x4 double matrices from the second source record

For input `source_b = rdx`, `0x25e0c0` builds the same two matrix layouts from:

```text
source_b+0x00..0x20
source_b+0x24..0x2c
source_b+0x30..0x50
```

Again, these are offset identities only.

### 4. `0x25e0c0` multiplies the two matrices for each source record

The first two `0x25ec70` calls are:

```text
source_b_product = source_b_primary * source_b_secondary
source_a_product = source_a_primary * source_a_secondary
```

Instruction anchors:

- `0x25e313..0x25e32b`: computes `source_b_product`
- `0x25e330..0x25e348`: computes `source_a_product`

This proves that the row-composition producer is not arbitrary field copying.
It constructs two homogeneous-style 4x4 matrices per source record and performs
matrix multiplication in double precision.

### 5. `0x25e0c0` inverts the first source product, then multiplies again

At `0x25e34d..0x25e35a`, `0x25e0c0` calls:

```text
helper_result = inverse(source_a_product)
```

At `0x25e35f..0x25e36c`, it then calls:

```text
row_double_matrix = source_b_product * helper_result
```

The exact inverse operation is proven in
[bundle_proof_iramp_9db20_matrix_inverse.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_9db20_matrix_inverse.md).

### 6. `0x25e0c0` converts the final double matrix to float row fields

After the final `0x25ec70` call, `0x25e0c0` reads sixteen doubles from the final
matrix and converts them to single-precision floats.

The output writes are:

- `0x25e441..0x25e450`: output `+0x00`, `+0x04`, `+0x08`, `+0x0c`
- `0x25e455..0x25e465`: output `+0x10`, `+0x14`, `+0x18`, `+0x1c`
- `0x25e46a..0x25e47b`: output `+0x20`, `+0x24`, `+0x28`, `+0x2c`
- `0x25e480..0x25e492`: output `+0x30`, `+0x34`, `+0x38`, `+0x3c`

Therefore the row fields consumed later by IRAMP are the single-precision copy
of this final double-matrix result.

## Safe Conclusion

- Proven:
  `0x25ec70` is a 4x4 double matrix multiply helper.
- Proven:
  `0x25e0c0` constructs two homogeneous-style 4x4 matrices from each source
  record, multiplies each source's matrix pair, inverts the first source
  product through `0x9db20`, multiplies the second source product by that
  inverse, and writes the final 4x4 result into output `+0x00..+0x3c` as
  floats.
- Still unproven:
  the semantic names / calibration origin of those source-record fields.

## Consequence For Blocker Work

The producer-side row blocker is narrower again.

Future work should not ask whether `0x25ec70` is scalar glue or whether
`0x25e0c0` merely copies row fields. The installed bundle proves a structured
4x4 matrix chain.

Future work should decode:

- later field semantics and public calibration origin of the `state+0x448`
  source-record family
- the LRI calibration-block origin of the `state+0xe0` object banks
- the public semantic names for the source-record fields composed by `0x23faf0`
- the semantic meaning and calibration origin of the map pointer returned
  through `0x268480`
