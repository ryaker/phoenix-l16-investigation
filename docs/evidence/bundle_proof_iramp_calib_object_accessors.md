# Bundle Proof: IRAMP Calibration Object Accessors

## Scope

This note proves installed-bundle accessors reached by the IRAMP source-record
constructor path. It narrows the remaining producer-origin blocker by proving
how `state+0xe0` object lookup and the object-derived record-bank helpers work.

It builds on:

- [bundle_proof_iramp_source_record_constructors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_source_record_constructors.md)
- [bundle_proof_iramp_23faf0_composition_helper.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_23faf0_composition_helper.md)

It does not prove the LRI calibration-block origin of these object fields.

It does not prove public semantic names for the source-record fields.

It does not map the numeric `CalibStage` values to the public words `factory`
and `current`; the installed bundle only proves the accepted numeric values and
the error string.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Disassembly commands:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x1be970 --count 420'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0xe6ba0 --count 240'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0xf2720 --count 80' -o 'disassemble --start-address 0xf3320 --count 40' -o 'disassemble --start-address 0xf3340 --count 40'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0xf3350 --count 220'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0xe7220 --count 180'`

## Proven Facts

### 1. `0x1be970` resolves a shared image-like object or throws

`0x1be970(out, lookup_context, key)` reads lookup state from
`lookup_context`, delegates the actual search to `0xe6ba0`, and requires the
resulting shared-ptr-like output to contain a non-null raw pointer.

Instruction anchors:

- `0x1be980`: reads `*(lookup_context)` as the search container pointer
- `0x1be983`: reads `lookup_context+0x10` as one integer search key
- `0x1be989`: passes the caller-supplied integer key as the other search key
- `0x1be98b`: calls `0xe6ba0`
- `0x1be990..0x1be9a1`: returns `out` if `*(out)` is non-null
- `0x1be9b1`: failure path uses the literal `invalid image pointer!`

Safe statement: the `state+0xe0` path used by the source-record constructors is
not arbitrary memory. It is a lookup-context path that must resolve to a
non-null shared image-like object or throw.

### 2. `0xe6ba0` searches a vector of shared object pairs by two object fields

`0xe6ba0(out, container, key_a, key_b)` walks entries from
`container+0x10` to `container+0x18` in `0x10`-byte steps. Each entry is a
shared-ptr-like pair. The candidate raw pointer is read from entry `+0`.

For each candidate, it compares:

- `0xf3320(candidate)` against `key_a`
- `0xf2720(candidate)` against `key_b`

Instruction anchors:

- `0xe6bb7..0xe6bbf`: loads vector begin/end from `container+0x10/+0x18`
- `0xe6bd0..0xe6bd8`: calls `0xf3320(candidate)` and compares to `key_a`
- `0xe6bdd..0xe6be8`: calls `0xf2720(candidate)` and compares to `key_b`
- `0xe6bf3..0xe6bfa`: writes a null shared-ptr-like output if no match exists
- `0xe6c0c..0xe6c24`: copies the matching shared-ptr-like pair to `out` and
  increments the shared count when present

The object-field accessors are direct:

- `0xf2720`: returns `*(int32 *)(object+0x60)`
- `0xf3320`: returns `*(int32 *)(object+0x64)`

Safe statement: `0x1be970` resolves objects by two integer fields stored at
object offsets `+0x64` and `+0x60`. Their public names are not proven here.

### 3. `0xf34e0` selects one of two `CalibStage` record banks

`0xf34e0(object, stage)` returns one of two in-object record banks:

```text
stage == 1 -> object + 0x12c
stage != 1 -> object + 0x180
```

Instruction anchors:

- `0xf34e4`: prepares return pointer `object+0x12c`
- `0xf34eb`: prepares alternate pointer `object+0x180`
- `0xf34f2..0xf34f5`: selects `object+0x12c` only when `stage == 1`

The nearby writer at `0xf33d0` proves those offsets are the two accepted
`CalibStage` banks. It accepts only stage values `0` and `1`; any other value
throws the installed-bundle error:

```text
wrong CalibStage, must be factory or current
```

Instruction anchors:

- `0xf33d9..0xf33e2`: accepts `stage == 1` and `stage == 0`; other values branch
  to the error path
- `0xf33e8..0xf3438`: writes the stage-0 bank at
  `object+0x180/+0x1a4/+0x1c8`
- `0xf3440..0xf3490`: writes the stage-1 bank at
  `object+0x12c/+0x150/+0x174`
- `0xf34ac`: error string literal

Safe statement: the source-record builder `0x264270` reads source-record fields
from one of two CalibStage banks in the resolved object. The installed bundle
does not, in this proof, map numeric stage `0` or `1` to which public word is
`factory` versus `current`.

### 4. `0xf3350` and `0xf3360` are direct object / owner accessors

`0xf3350(object)` returns `object+0x10c`.

Instruction anchor:

- `0xf3354`: `leaq 0x10c(%rdi), %rax`

In the `0x264270` source-record builder, fields read from this returned pointer
include returned `+0x18/+0x1c`, which are object offsets `+0x124/+0x128`.

`0xf3360(object)` reads an owner pointer from `object+0xa0`. If the owner is
non-null, it calls `0xe7220(owner, *(int32 *)(object+0x60))`. If the owner is
null, it throws:

```text
CapturedImage does not have an owner!
```

Instruction anchors:

- `0xf336c`: reads `object+0xa0`
- `0xf3378`: reads `object+0x60` as the lookup key passed to the owner
- `0xf337b`: calls `0xe7220`
- `0xf3396`: owner-missing error string literal

`0xe7220(owner, key)` searches a tree rooted at `owner+0x2a8` by comparing
`key` against node `+0x20`. On an exact match it returns node `+0x30`; otherwise
it returns a static fallback address.

Instruction anchors:

- `0xe7224..0xe7230`: reads the tree root and establishes `owner+0x2a8`
- `0xe7240..0xe7259`: tree walk comparing `key` with node `+0x20`
- `0xe727c`: exact-match return is `node+0x30`

Safe statement: `0xf3360` is not an unexplained table read. It is an
owner-backed keyed tree lookup using the object's `+0x60` integer field.

## Safe Conclusion

- Proven:
  `state+0xe0` resolution through `0x1be970` / `0xe6ba0` searches shared
  image-like objects by two integer object fields at `+0x64` and `+0x60`, and
  `0x1be970` throws `invalid image pointer!` if the lookup output is null.
- Proven:
  `0xf34e0` selects between two in-object `CalibStage` banks at `object+0x12c`
  and `object+0x180`; the writer at `0xf33d0` accepts only stage values `0` and
  `1` and uses the installed string `wrong CalibStage, must be factory or
  current` for other values.
- Proven:
  `0xf3350` returns `object+0x10c`.
- Proven:
  `0xf3360` delegates through `object+0xa0` to an owner tree lookup at
  `owner+0x2a8`, keyed by `object+0x60`, or throws `CapturedImage does not have
  an owner!`.
- Still unproven:
  LRI calibration-block origins, public names for `object+0x60/+0x64`, numeric
  `CalibStage` value-to-name mapping, public names for the `0xf34e0` bank
  fields, and the semantic meaning / origin of the `0x268480` map provider.

## Consequence For Blocker Work

Future work should not treat `state+0xe0`, `0xf34e0`, `0xf3350`, or `0xf3360`
as opaque.

The remaining producer-side blocker is now narrower:

```text
known:
  state+0xe0 -> 0x1be970 -> 0xe6ba0 shared object lookup
  object -> 0xf34e0 CalibStage bank selection
  object -> 0xf3350 direct field block
  object -> 0xf3360 owner-backed keyed lookup

still unknown:
  LRI block origins, public field names, numeric stage-name mapping,
  and 0x268480 map-provider semantics
```
