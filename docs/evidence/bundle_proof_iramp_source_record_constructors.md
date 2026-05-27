# Bundle Proof: IRAMP Source-Record Constructors And Map Provider

## Scope

This note proves the installed-bundle topology and field movement for the
source-record constructors that feed the IRAMP `0x50` warpfield records.

It builds on:

- [bundle_proof_iramp_record_producer_scale_and_dispatch.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_record_producer_scale_and_dispatch.md)
- [bundle_proof_iramp_row_composition_matrix_chain.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_row_composition_matrix_chain.md)
- [bundle_proof_iramp_9db20_matrix_inverse.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_9db20_matrix_inverse.md)
- [bundle_proof_iramp_23faf0_composition_helper.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_23faf0_composition_helper.md)
- [bundle_proof_iramp_calib_object_accessors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_calib_object_accessors.md)
- [bundle_proof_iramp_state_448_tree_builder.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_tree_builder.md)

It does not prove public calibration names for the source-record fields.

It does not prove the semantic meaning or calibration origin of the map pointer
returned by the virtual call behind `0x268480`.

The companion `state+0x448` evidence now bounds that field as a keyed
tree/control object with a first visible byte-gated insertion path. This note
still does not prove public calibration names or full later field semantics for
the records stored there.

The companion composition-helper evidence bounds the installed-bundle bodies of
`0x23faf0`, `0x264460`, and `0x264980`. This note keeps only the constructor
topology.

The companion calibration-object accessor evidence bounds `state+0xe0`
resolution and the object accessors behind `0x264270`. This note keeps only the
constructor topology.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Source-record constructors and map provider:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3faed0 --count 320'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3fb1a0 --count 360'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x268480 --count 180'`
- Deeper helper boundaries:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x264270 --count 180'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x264450 --count 340'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x23faf0 --count 300'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x24009e --count 180'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x241610 --count 120' -o 'disassemble --start-address 0x241630 --count 160'`
- Constants:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format f --size 4 --count 8 0x5a8120' -o 'memory read --format f --size 4 --count 8 0x5a88b0'`

## Proven Facts

### 1. `0x3faed0` is a guarded same-category source-record constructor

The dispatcher calls `0x3faed0(dst, state, key, level_or_index)` from the
same-category branch and once from the cross-category branch.

`0x3faed0` first requires:

```text
*(int32 *)(state + 0x8) == 8
```

If that check fails, it throws:

```text
Online calibration is not finished.
```

Instruction anchors:

- `0x3faeef..0x3faef5`: checks `state+0x8`
- `0x3fb118..0x3fb142`: throws the online-calibration error

When the guard passes, it searches the tree/control object reached through
`state+0x448` for the incoming key. The comparison key is read from found-node
`+0x1c`.

Instruction anchors:

- `0x3faefb`: reads `state+0x448`
- `0x3faf10..0x3faf31`: tree walk by `node+0x1c`
- `0x3fb0c5..0x3fb100`: throws `map::at:  key not found` if no node is found

Once a node is found, `0x3faed0` copies node payload fields into a stack source
record from node offsets `+0x20..+0xa0`.

It then writes two explicit `(1.0, 1.0)` float pairs into that stack record:

- `0x3fafe5`: loads packed `0x3f8000003f800000`
- `0x3fb007`: calls `0x241610`, which writes pair input to record `+0x40/+0x44`
- `0x3fb021`: calls `0x241630`, which writes pair input to record `+0x48/+0x4c`

It also resolves an object through `state+0xe0` and the same key, builds another
source record from that object, and combines the node-derived record with the
object-derived record:

- `0x3fb026..0x3fb037`: calls `0x1be970` with `state+0xe0` and key
- `0x3fb054..0x3fb064`: calls `0x264450`, which tail-jumps to `0x264270`
- `0x3fb069..0x3fb076`: calls `0x23faf0(dst, node_record, object_record)`

Safe statement: `0x3faed0` is not a leaf calibration table copy. It combines a
keyed `state+0x448` record with a keyed `state+0xe0` object-derived record
through `0x23faf0`.

### 2. `0x3fb1a0` is the cross-category source-record constructor

`0x3fb1a0(dst, state, key, level_or_index)` has the same online-calibration
guard and the same `state+0x448` keyed tree/control lookup shape.

Instruction anchors:

- `0x3fb1ba..0x3fb1be`: checks `state+0x8`
- `0x3fb1c4..0x3fb1fc`: tree walk by `node+0x1c`
- `0x3fb412..0x3fb44d`: throws `map::at:  key not found` if no node is found
- `0x3fb465..0x3fb48f`: throws the online-calibration error

Unlike `0x3faed0`, the found-node record is used directly from `node+0x20`:

- `0x3fb202`: advances the found node pointer to `node+0x20`

It resolves an object through `state+0xe0`, builds an object-derived source
record through `0x264450`, and combines that with the node record through
`0x23faf0`:

- `0x3fb206..0x3fb211`: calls `0x1be970`
- `0x3fb228..0x3fb238`: calls `0x264450`
- `0x3fb23d..0x3fb246`: calls `0x23faf0(dst, node_record, object_record)`

It then applies additional installed-bundle adjustment helpers before writing
the final fields back to `dst`:

- `0x3fb280..0x3fb2a2`: calls `0x264460` with a stack pair initialized to
  two `2.0` floats
- `0x3fb2a7..0x3fb2c0`: calls `0x264980` with both scalar arguments loaded
  from `0x5a8120`, which reads as `-0.5`
- `0x3fb2c5..0x3fb3c0`: copies the adjusted record fields back into `dst`

Safe statement: `0x3fb1a0` is a cross-category constructor that shares the same
keyed sources as `0x3faed0`, then applies extra fixed adjustment helpers.

### 3. `0x264450` is a thin wrapper over `0x264270`

`0x264450` immediately tail-jumps to `0x264270`.

`0x264270(dst, object, level_or_index)` builds a source-record-shaped output
from object helper calls:

- `0x264288..0x264293`: calls `0xf34e0(object, level_or_index)`, then copies
  source `+0x00..+0x20` to output `+0x00..+0x20`
- `0x2642a7..0x2642c1`: calls `0xf34e0` again, then copies source
  `+0x48/+0x4c/+0x50` to output `+0x24/+0x28/+0x2c`
- `0x2642c4..0x2642e1`: calls `0xf34e0` again, then copies source
  `+0x24..+0x44` to output `+0x30..+0x50`
- `0x2642e5..0x2642ec`: writes a constant vector into output `+0x54..+0x63`
- `0x264303..0x264336`: calls `0xf3360(object)` and copies optional vector
  storage into output `+0x68..+0x78`
- `0x26433b..0x2643b0`: calls `0xf3350(object)`, uses floats at returned
  `+0x18/+0x1c` to scale optional-data fields into output `+0x80..+0xa0`,
  and writes output `+0xa0 = 1.0`

If the optional data from `0xf3360` is absent, `0x264270` throws:

```text
Cannot read data from empty Optional!
```

This proves the object-derived source-record field movement. Companion evidence
now bounds `0xf34e0` as a two-bank `CalibStage` selector, `0xf3350` as an
`object+0x10c` accessor, and `0xf3360` as an owner-backed keyed lookup. The
public field names and LRI origins remain unproven.

### 4. `0x268480` returns the map pointer through a virtual slot

In both `0x3f7040` branches, callers pass `state+0xb0` to `0x268480`.

`0x268480(rdi)` performs:

```text
tmp = *(rdi + 0x18)
object = *(tmp - 0x8)
return object->vtable[0x90]()
```

Instruction anchors:

- `0x268484`: reads `rdi+0x18`
- `0x268488`: reads the object pointer from `tmp-0x8`
- `0x26848c..0x26848f`: loads the vtable and calls slot `+0x90`
- `0x268495`: returns that virtual-call result

Safe statement: the map pointer stored in final IRAMP records is the return
value of this virtual call. Its public semantic meaning remains unproven.

## Safe Conclusion

- Proven:
  `0x3faed0` constructs source records from a keyed node record reached through
  `state+0x448` plus a keyed `state+0xe0` object-derived record, then combines
  them through `0x23faf0`.
- Proven:
  `0x3fb1a0` is the cross-category constructor using the same source families,
  plus fixed helper adjustments through `0x264460` and `0x264980`.
- Proven:
  `0x264450` reaches `0x264270`, which builds object-derived source records
  from helper-returned fields and optional vector storage; companion evidence
  bounds those helper accessors to `CalibStage` banks, `object+0x10c`, and an
  owner-backed keyed lookup.
- Proven:
  `0x268480` returns the map pointer by virtual slot `+0x90` on the object
  reached through `state+0xb0`.
- Still unproven:
  public calibration names, LRI calibration-block origins, and the semantic
  meaning / origin of the map returned through the `0x268480` virtual slot path.

## Consequence For Blocker Work

Future work should not ask whether the producer source records come from
unknown arbitrary memory. Their immediate installed-bundle sources are now
bounded:

```text
same-category:
  source_record = compose_0x23faf0(state+0x448[key], state+0xe0[key])

cross-category:
  source_record = adjusted(compose_0x23faf0(state+0x448[key], state+0xe0[key]))

map_pointer:
  state+0xb0 -> virtual slot +0x90
```

Future work should decode:

- later field semantics and public calibration origin of `state+0x448`
- the LRI calibration-block origin of `state+0xe0` and its resolved object banks
- the public semantic names for the source-record fields composed by `0x23faf0`
- the semantic meaning and origin of the `0x268480` virtual map provider
