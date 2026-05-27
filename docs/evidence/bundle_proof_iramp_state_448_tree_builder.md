# Bundle Proof: IRAMP `state+0x448` Tree Builder Boundary

## Scope

This note proves the installed-bundle boundary for the `state+0x448` container
that later feeds the IRAMP source-record constructors.

It proves:

- how `state+0x448` is initialized as a tree/control-object pointer
- how the first visible insertion loop resolves objects through `state+0xe0`
- how `object+0x30` gates insertion into this tree
- how `0x38dad0` inserts/finds keyed tree nodes
- how `0x241590` and `0x2415b0` copy the first visible payload fields

It does not prove public calibration field names.

It does not prove the LRI calibration-block origin of the resolved objects.

It does not prove the semantic name of `object+0x30`. In older scratch prose it
was described with anchor/stereo-reference language, but this note only admits
the byte-gated insertion behavior proven by installed disassembly.

It does not fully close every later write to the `state+0x448` payload records.
A companion note, `bundle_proof_iramp_state_448_later_payload_writes.md`,
bounds later direct writes through payload `+0x80` and excludes nearby
stack-only / separate-record helper calls. This note remains the container and
first-insertion boundary, not a complete semantic decode.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Constructor and first insertion loop:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3f2dcf --count 280'`
- Tree insert/find helper:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x38dad0 --count 170'`
- First payload copy helpers:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x241590 --count 80' -o 'disassemble --start-address 0x2415b0 --count 80'`
- Downstream consumers for shape confirmation:
  `arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3faed0 --count 90' -o 'disassemble --start-address 0x3fb1a0 --count 95'`

## Proven Facts

### 1. `state+0x448` is initialized as a tree/control-object pointer

The constructor allocates `0x30` bytes and sets up a small control object before
storing it into the state object:

- `0x3f2ee3..0x3f2ee8`: allocates `0x30` bytes.
- `0x3f2ef0`: zeroes `allocated+0x8..+0x17`.
- `0x3f2efe`: computes `allocated+0x18`.
- `0x3f2f05`: computes `allocated+0x20`.
- `0x3f2f09`: zeroes `allocated+0x20..+0x2f`.
- `0x3f2f0d`: writes `allocated+0x20` at `allocated+0x18`.
- `0x3f2f11`: writes `allocated+0x18` into `state+0x448`.
- `0x3f2f18`: writes the original allocation pointer into `state+0x450`.
- `0x3f2f1f`: writes zero into `state+0x458`.

Downstream constructors confirm that `state+0x448` is treated as a tree/control
object pointer:

- `0x3faefb`: `0x3faed0` reads `state+0x448`.
- `0x3faf10`: `0x3faed0` reads `control+0x8` as the first tree node pointer.
- `0x3fb1c4`: `0x3fb1a0` reads `state+0x448`.
- `0x3fb1cb`: `0x3fb1a0` reads `control+0x8` as the first tree node pointer.

Safe statement: `state+0x448` is not arbitrary memory. It is initialized in the
constructor as a pointer to a tree/control object that later source-record
constructors walk by integer key.

### 2. The first visible population loop enumerates keys from `state+0xe0`

After setup, the constructor calls the already-bounded object-list helper:

- `0x3f3061..0x3f306f`: calls `0x1bdb60(out, state+0xe0)`.
- `0x3f3082..0x3f3090`: treats the result as a vector of `int32` keys.
- `0x3f30a0`: reads one `int32` key from the vector.
- `0x3f30a4..0x3f30ae`: calls `0x1be970(out, state+0xe0, key)`.

Companion evidence already bounds `0x1be970` / `0xe6ba0` as a shared
object-lookup path over `state+0xe0`-derived containers.

Safe statement: the first visible `state+0x448` population loop is keyed by a
vector produced from `state+0xe0`, and each loop iteration resolves a
shared-ptr-like object through `0x1be970`.

### 3. `object+0x30` gates insertion into `state+0x448`

Each resolved object is tested before insertion:

- `0x3f30b3`: loads the resolved object pointer.
- `0x3f30ba`: compares byte `object+0x30` with zero.
- `0x3f30be`: if the byte is zero, jumps to cleanup/advance at `0x3f312d`.

Only the nonzero path inserts or updates a `state+0x448` tree node:

- `0x3f30c0..0x3f30c7`: loads the `state+0x448` control pointer.
- `0x3f30ca`: calls `0xf2720(object)`.
- `0x3f30cf`: stores the returned integer as the tree key.
- `0x3f30d5..0x3f30df`: calls `0x38dad0(control, &key)`.
- `0x3f30e4..0x3f30ee`: copies the first stack record into the returned
  payload through `0x241590`.
- `0x3f30f3..0x3f3119`: repeats the same key lookup path.
- `0x3f311e..0x3f3128`: copies three more dwords into the payload through
  `0x2415b0`.

Companion evidence already bounds `0xf2720(object)` to the direct
`*(int32 *)(object+0x60)` accessor. This note therefore admits only:

```text
if *(uint8 *)(object + 0x30) != 0:
    key = *(int32 *)(object + 0x60)
    payload = insert_or_find(state_448_tree, key)
    copy first stack record fields into payload
    copy three additional dwords into payload
else:
    skip this insertion/update path
```

Safe statement: `object+0x30 == 0` excludes that resolved object from this
first visible `state+0x448` insertion/update path. The semantic name of that
byte is not proven here.

### 4. `0x38dad0` is the keyed insert/find helper for this tree shape

`0x38dad0(control, &key)` uses the integer at `*key` and tree-node keys at
`node+0x1c`:

- `0x38dae4`: reads `control+0x8` as the current root node.
- `0x38daed`: reads the requested key from `*rsi`.
- `0x38db03..0x38db28`: walks left/right by comparing requested key with
  `node+0x1c`.
- `0x38db63..0x38db73`: allocates a new `0xa8`-byte node and writes the key at
  `node+0x1c` when no matching node exists.
- `0x38db76..0x38db7a`: initializes the node payload through `0x241540`.
- `0x38db89`: links the new node into the tree.
- `0x38dbab`: increments `control+0x10`.
- `0x38dbaf..0x38dbb3`: returns `node+0x20`.

Safe statement: `0x38dad0` returns the payload pointer for a node keyed by a
32-bit integer. On first insertion it creates a `0xa8`-byte node whose payload
starts at `node+0x20`.

### 5. `0x241590` and `0x2415b0` copy the first visible payload fields

`0x241590(dst_payload, src)` copies:

- `src+0x00..+0x0f` to `dst+0x00..+0x0f`
- `src+0x10..+0x1f` to `dst+0x10..+0x1f`
- `src+0x20` to `dst+0x20`

Instruction anchors:

- `0x241594..0x241597`
- `0x24159a..0x2415a5`

`0x2415b0(dst_payload, src)` copies:

- `src+0x00` to `dst+0x24`
- `src+0x04` to `dst+0x28`
- `src+0x08` to `dst+0x2c`

Instruction anchors:

- `0x2415b4..0x2415c2`

Safe statement: the first visible insertion loop initializes at least payload
fields `+0x00..+0x2c` for each nonzero-`object+0x30` entry. It does not, by
itself, prove the public names of those fields or every later field in the
payload record.

## Safe Conclusion

- Proven:
  `state+0x448` is initialized as a pointer to a tree/control object whose
  root-node pointer lives at `control+0x8`.
- Proven:
  the first visible population loop enumerates `int32` keys from `state+0xe0`,
  resolves each object through `0x1be970`, and inserts/updates only objects
  with nonzero byte `object+0x30`.
- Proven:
  inserted/updated nodes are keyed by the integer returned by `0xf2720`, which
  companion evidence bounds to `*(int32 *)(object+0x60)`.
- Proven:
  `0x38dad0` is the keyed tree insert/find helper and returns `node+0x20`.
- Proven:
  `0x241590` and `0x2415b0` copy the first visible payload fields
  `+0x00..+0x2c`.
- Still unproven:
  public calibration names, LRI calibration-block origins, the semantic name of
  `object+0x30`, and the full semantic meaning of the `state+0x448` payload
  fields.

## Consequence For Blocker Work

Future work should not ask whether `state+0x448` is arbitrary or uninitialized.
Its control-object shape and first insertion gate are now bounded.

Future work should decode:

- the public calibration meaning of the copied payload fields
- the LRI block(s) that supply the `state+0xe0` objects used here
- the semantic meaning of `object+0x30`
- whether payload fields beyond the companion note's direct writes through
  `+0x80` are live
