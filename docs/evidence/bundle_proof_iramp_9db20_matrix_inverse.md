# Bundle Proof: IRAMP `0x9db20` Matrix Inverse

## Scope

This note proves the exact installed-bundle operation performed by `0x9db20`
inside the IRAMP row-composition chain.

It builds on:

- [bundle_proof_iramp_row_composition_matrix_chain.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_row_composition_matrix_chain.md)

It does not prove public calibration names for the source-record fields.

It does not prove the semantic meaning or calibration origin of the map stored
at `record+0x40`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Wrapper and inverse body:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'image lookup -a 0x9db20' -o 'image lookup -a 0x9db80' -o 'disassemble --start-address 0x9db20 --count 140' -o 'disassemble --start-address 0x9db80 --count 420'`
- Tail confirmation:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x9e000 --count 420'`

## Proven Facts

### 1. `0x9db20` copies one 4x4 double matrix, then calls `0x9db80`

`0x9db20(dst, src)` copies `0x80` bytes from `src` to `dst`:

- `0x9db29..0x9db45`: copies source `+0x40..+0x7f`
- `0x9db49..0x9db64`: copies source `+0x00..+0x3f`

That is exactly sixteen doubles, or one 4x4 double matrix.

It then calls:

```text
0x9db80(stack_cookie_scratch, dst)
```

Instruction anchors:

- `0x9db67`: first argument is a stack scratch address
- `0x9db6b`: second argument is `dst`
- `0x9db6e`: call to `0x9db80`
- `0x9db73`: returns `dst`

Therefore `0x9db20` is a copy-then-transform wrapper over one copied 4x4
double matrix.

### 2. `0x9db80` is an in-place 4x4 double matrix inverse body

`0x9db80` reads the copied matrix from `rsi`, computes a full cofactor /
adjugate-style inverse, and overwrites the same `rsi` matrix.

The body computes many paired products and differences from all four rows of the
input matrix. The decisive anchors are the determinant reciprocal and the final
sixteen writes.

At `0x9de43..0x9de53`, the body computes one reciprocal scalar:

```text
inv_det = 1.0 / determinant
```

Instruction anchors:

- `0x9de43`: final determinant term is accumulated
- `0x9de47`: loads `1.0`
- `0x9de4f`: divides by the determinant
- `0x9de53`: saves the reciprocal determinant

At `0x9e1ce..0x9e230`, the body multiplies sixteen cofactor / adjugate terms by
that reciprocal determinant and writes the full output matrix:

- `0x9e1d6..0x9e1e2`: writes output `+0x00/+0x08`
- `0x9e1e6..0x9e1ef`: writes output `+0x10/+0x18`
- `0x9e1f4..0x9e1fd`: writes output `+0x20/+0x28`
- `0x9e202..0x9e206`: writes output `+0x30/+0x38`
- `0x9e20b..0x9e214`: writes output `+0x40/+0x48`
- `0x9e219..0x9e21d`: writes output `+0x50/+0x58`
- `0x9e222..0x9e230`: writes output `+0x60/+0x68/+0x70/+0x78`

The result is:

```text
matrix = inverse(matrix)
```

for the 4x4 double matrix at `rsi`.

### 3. `0x9db20` therefore returns an inverted copy

Combining the wrapper and body:

```text
0x9db20(dst, src):
  dst = src
  dst = inverse(dst)
  return dst
```

This is stronger than the previous safe statement that `0x9db20` was an unknown
matrix helper.

## Safe Conclusion

- Proven:
  `0x9db20` copies one 4x4 double matrix and inverts the copy through `0x9db80`.
- Proven:
  `0x9db80` is an in-place 4x4 double matrix inverse body using cofactor /
  adjugate terms scaled by a reciprocal determinant.
- Still unproven:
  the public calibration names or origin of the source-record matrices being
  inverted.

## Consequence For Blocker Work

The row-composition formula inside `0x25e0c0` can now be written as:

```text
source_a_product = source_a_primary * source_a_secondary
source_b_product = source_b_primary * source_b_secondary
row_double_matrix = source_b_product * inverse(source_a_product)
```

Future work should not ask what `0x9db20` does. It is now bundle-proven as a
4x4 double matrix inverse wrapper.

Future work should decode:

- later field semantics and public calibration origin of the `state+0x448`
  source-record family
- the LRI calibration-block origin of the `state+0xe0` object banks
- the public semantic names for the source-record fields composed by `0x23faf0`
- the semantic meaning and calibration origin of the map pointer returned
  through `0x268480`
