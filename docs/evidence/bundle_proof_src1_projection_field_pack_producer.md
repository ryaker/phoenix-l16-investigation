# Bundle Proof: Visible `src1` Projection Field-Pack Producer

## Scope

This note bounds the installed-bundle producer path for the transform fields
consumed by the live visible-`src1` projection callable at `libcp+0x3e42e0`.

It builds on:

- [lldb_src1_worker_projection_record_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_worker_projection_record_four_zoom.md)
- [bundle_proof_src1_projection_callable_transform.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_projection_callable_transform.md)

It proves:

- the visible `src1` payload constructor calls `0x3f6170` to produce the
  field pack later consumed by `0x3e42e0`
- `0x3f6170` dispatches into same-category and cross-category producer paths
  at `0x3f6200` and `0x3f6940`
- both producer paths converge on `0x145580`, which tail-jumps to `0x144f50`
- `0x144f50` writes the output record fields that the constructor copies into
  payload fields `+0xf8/+0xfc`, `+0x100/+0x108/+0x110`, and `+0x118..+0x140`
- `0x144a70` fills the radius-table vector used by `0x3e42e0` and forces that
  vector to `0x1000` float entries

It does not prove:

- the public calibration names of the keyed records
- the LRI block/field origins of the records or optional object data
- the semantic meaning of the same-category versus cross-category classifier
- that any projection-record index is a physical camera id
- the semantic contents of visible `src1`
- the exact upstream merge/reduction mechanism behind `src1` / `src2`
- C6 routing or final merge acceptance / rejection logic

## Bundle + Commands

Binary:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

Commands:

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x3e27a0 --end-address 0x3e2a20'

arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x3f6170 --end-address 0x3f6900'

arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x3f6940 --end-address 0x3f7050'

arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x144a70 --end-address 0x145590'
```

## Constructor Copy Path

The visible `src1` payload constructor at `0x3e27a0` writes the fields later
read by `0x3e42e0`.

Instruction anchors:

- `0x3e28db`: loads constructor key from `payload+0x90` into `edx`
- `0x3e28e2..0x3e28ec`: initializes a two-float stack tuple to `(1.0, 1.0)`
- `0x3e28f6`: passes output record pointer `-0x138` as `rdi`
- `0x3e28fd`: passes the `(1.0, 1.0)` tuple as `rcx`
- `0x3e2904`: passes an auxiliary tuple pointer `-0xe8` as `r8`
- `0x3e290b`: calls `0x3f6170`
- `0x3e2910..0x3e2922`: copies output record `+0x00/+0x04` into
  `payload+0xf8/+0xfc`
- `0x3e2930..0x3e2990`: moves output record vector fields `+0x08/+0x10/+0x18`
  into `payload+0x100/+0x108/+0x110`
- `0x3e29a6..0x3e29b8`: copies output record `+0x20/+0x24` into
  `payload+0x118/+0x11c`
- `0x3e29bf..0x3e29e2`: copies output record `+0x28..+0x48` into
  `payload+0x120..+0x140`

This ties the already-decoded `0x3e42e0` fields to an installed-bundle
producer path:

| `0x3e42e0` state field | Producer output record field |
|---:|---:|
| `+0x0f8/+0x0fc` | `+0x00/+0x04` |
| `+0x100/+0x108/+0x110` | `+0x08/+0x10/+0x18` |
| `+0x118/+0x11c` | `+0x20/+0x24` |
| `+0x120..+0x140` | `+0x28..+0x48` |

The constructor does not public-name these fields.

## Dispatcher At `0x3f6170`

`0x3f6170` receives:

- `rdi`: output record pointer
- `rsi`: state/cache object
- `edx`: constructor key
- `rcx`: caller tuple pointer
- `r8`: auxiliary tuple pointer

Instruction anchors:

- `0x3f6191..0x3f6198`: calls `0xf6c60(key)` and saves the returned class/group
- `0x3f61a1..0x3f61b3`: reads `state+0xe0`, calls `0x1bea00`, then classifies
  that result through `0xf6c60`
- `0x3f61b8..0x3f61c1`: compares the two classifier results
- `0x3f61be..0x3f61ca`: same-category branch calls `0x3f6200`
- `0x3f61d1..0x3f61e1`: cross-category branch calls `0x3f6940`
- `0x3f61e6`: returns the original output record pointer

Safe conclusion: `0x3f6170` is a dispatcher for the projection field-pack
producer. The semantic name of its classifier is not proven here.

## Same-Category Producer At `0x3f6200`

`0x3f6200` resolves an object through `state+0xe0`, writes the auxiliary tuple,
copies two keyed record ranges from `state+0x420`, builds a row-pack, then calls
the common writer at `0x145580`.

Instruction anchors:

- `0x3f6224..0x3f6238`: resolves an object through `state+0xe0` and
  `0x1be970`
- `0x3f6246..0x3f6258`: calls `0xf3350(object)` and writes returned
  `+0x08/+0x0c` into the auxiliary tuple passed as `rcx`
- `0x3f6263..0x3f628a`: searches the `state+0x420` tree by key at node `+0x20`
- `0x3f62a4..0x3f63f4`: copies one record range from found node
  `+0xd0..+0x170` into stack locals, including an owned float vector from
  node `+0x138..+0x140`
- `0x3f6403..0x3f642a`: searches the same `state+0x420` tree again by key
- `0x3f6433..0x3f6566`: copies a second record range from found node
  `+0x28..+0xc8` into stack locals, including an owned float vector from
  node `+0x90..+0x98`
- `0x3f656d..0x3f674c`: performs SIMD scalar products into a row-pack at
  stack locals `-0x1c0`, `-0x1b0`, and `-0x1a0`
- `0x3f6754..0x3f6768`: initializes a local scale tuple to `(1.0, 1.0)` and a
  zero/default tuple
- `0x3f677e..0x3f67ab`: calls `0x145580(output, record_a, record_b, row_pack,
  object, scale_tuple, zero_tuple)`
- `0x3f6826..0x3f689e`: missing tree keys throw `map::at:  key not found`

Safe conclusion: the same-category path is a keyed-record producer over
`state+0x420` plus a resolved object. It is not an exposed multi-source pixel
reducer.

## Cross-Category Producer At `0x3f6940`

`0x3f6940` has a stronger online-calibration guard, uses `state+0x438` for the
auxiliary tuple, then converges on the same output writer.

Instruction anchors:

- `0x3f6959..0x3f695e`: requires `*(int32 *)(state + 0x8) == 8`
- `0x3f6fab..0x3f6fd5`: failed guard throws `Online calibration is not
  finished.`
- `0x3f6964..0x3f698c`: searches `state+0x438` by key at node `+0x1c`
- `0x3f6999..0x3f69be`: reads node `+0x20/+0x24`, multiplies by the caller
  tuple at `rcx`, converts to int, and writes the auxiliary tuple at `r8`
- `0x3f69c2..0x3f69d8`: resolves an object through `state+0xe0` and `0x1be970`
- `0x3f69ed..0x3f6a1d`: searches `state+0x420` by key at node `+0x20`
- `0x3f6a26..0x3f6b99`: copies the first keyed record range from node
  `+0xd0..+0x170`, including vector storage from `+0x138..+0x140`
- `0x3f6b9d..0x3f6bdd`: searches `state+0x420` again and calls `0x264460` to
  adjust a second source-record-shaped stack object using the caller tuple
- `0x3f6bf0..0x3f6dcf`: performs the same row-pack style of SIMD scalar products
  into stack locals `-0x1d0`, `-0x1c0`, and `-0x1b0`
- `0x3f6dd7..0x3f6e27`: calls `0x145580(output, record_a, adjusted_record_b,
  row_pack, object, scale_tuple, zero_tuple)`
- `0x3f6eab..0x3f6f46`: missing tree keys throw `map::at:  key not found`

Safe conclusion: the cross-category path also produces the same projection
field-pack shape. The names and LRI origins of `state+0x420` and `state+0x438`
records remain unproven here.

## Common Output Writer At `0x145580` / `0x144f50`

`0x145580` is a tail-jump stub:

- `0x145585`: jumps to `0x144f50`

The body at `0x144f50` writes the output record consumed by the constructor.

Instruction anchors:

- `0x144f7a..0x144fb0`: calls `0xf3350(object)`, reads returned
  `+0x18/+0x1c`, multiplies by the scale tuple, divides static `1.0` by those
  values, and writes output record `+0x00/+0x04`
- `0x144fb7..0x144fc0`: zero-initializes output vector fields at
  `+0x08/+0x10/+0x18`
- `0x144fc9..0x145008`: chooses optional object data through `0xf3360(object)`,
  preferring one optional branch and falling back to another
- `0x145008..0x145030`: scales the chosen optional pair, subtracts the caller's
  stack tuple, and writes output record `+0x20/+0x24`
- `0x145037..0x145143`: transforms / copies row-pack and source-record fields
  into stack locals through `0x9d7e0`
- `0x145143..0x14549c`: performs scalar/SIMD row composition and writes output
  record `+0x28..+0x48`
- `0x1454a3..0x1454a9`: calls `0x144a70(output, object)` before returning
- `0x1454c0..0x145515`: empty optional data throws `Cannot read data from empty
  Optional!`

Safe output-record map:

| Output record field | Later payload field | Proven writer |
|---:|---:|---|
| `+0x00/+0x04` | `+0xf8/+0xfc` | reciprocal pair from `0xf3350(object)+0x18/+0x1c` after scale |
| `+0x08/+0x10/+0x18` | `+0x100/+0x108/+0x110` | radius-table vector managed by `0x144a70` |
| `+0x20/+0x24` | `+0x118/+0x11c` | scaled optional object pair minus caller tuple |
| `+0x28..+0x48` | `+0x120..+0x140` | nine-float row-pack written by `0x144f50` |

The row-pack arithmetic is installed-bundle-proven as field movement and SIMD
composition, but this note does not assign public calibration names to those
rows.

## Radius-Table Writer At `0x144a70`

`0x144a70(output, object)` operates on output vector fields at
`output+0x08/+0x10/+0x18`.

Instruction anchors:

- `0x144a87`: computes `output+0x08`
- `0x144a8b..0x144aae`: reads current vector size and appends entries until the
  vector has `0x1000` floats when it is shorter
- `0x144ab8..0x144ade`: truncates the vector end pointer to `begin+0x4000` when
  it is longer than `0x1000` floats
- `0x144ae2..0x144aee`: calls `0x145590` to build a temporary object-derived
  float vector
- `0x144b00..0x144c4b`: subtracts that temporary vector from the output vector
  where their ranges overlap
- `0x144c4b..0x144c8f`: obtains an object-derived scalar either from optional
  data or through `0xf3330` / `0xf2720` / `0xe7730`
- `0x144c97`: writes `1.0` into radius-table entry `0`
- `0x144caf`: calls `0x146380` to prepare interpolation input
- `0x144d20..0x144ddd`: fills radius-table entries `1..4095`

Safe conclusion: the radius table consumed by `0x3e42e0` is not an unbounded
or arbitrary-length vector in this path. It is forced to `4096` float entries,
with entry `0` set to `1.0`, and entries `1..4095` produced through the
installed interpolation loop.

This aligns with the separately decoded `0x3e42e0` table-index clamp to
`0xfff`.

## Safe Conclusions

- Proven:
  the visible `src1` projection callable fields consumed by `0x3e42e0` are
  produced by `0x3f6170` and copied into the visible payload by `0x3e27a0`.
- Proven:
  `0x3f6170` dispatches same-category work to `0x3f6200` and cross-category
  work to `0x3f6940`, then both paths converge on `0x145580` / `0x144f50`.
- Proven:
  the same-category path copies keyed records from `state+0x420`; the
  cross-category path uses `state+0x438` for the auxiliary tuple and keyed
  records from `state+0x420` for the field-pack path.
- Proven:
  `0x144f50` writes the output fields later copied into the exact
  `0x3e42e0` state fields.
- Proven:
  `0x144a70` forces the radius table to `4096` floats and fills entries
  `1..4095`.
- Excluded:
  this producer path is not itself the exposed `src1` / `src2` N-to-1 reducer
  or final merge-quality decision body.
- Still unproven:
  public calibration names, LRI field origins, semantic `src1` contents, C6
  routing, and the exact upstream merge/reduction mechanism.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002` by bounding
the producer for the already-live `0x3e42e0` projection transform state.

It should be used as a field-origin boundary, not as merge/reducer closure.
