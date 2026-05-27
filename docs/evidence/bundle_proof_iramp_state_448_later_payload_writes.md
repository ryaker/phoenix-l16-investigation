# Bundle Proof: IRAMP `state+0x448` Later Payload Writes

## Scope

This note extends the `state+0x448` tree-builder boundary with later direct
payload writes that can be traced to a found `state+0x448` node payload.

It proves:

- the copy-helper field offsets for payload writes from `+0x30` through `+0x80`
- direct writes to found `state+0x448` payloads after keyed tree lookup
- which nearby helper calls are stack-only or separate-record writes and must
  not be promoted as `state+0x448` facts

It does not prove public calibration field names.

It does not prove the LRI calibration-block origin of the source objects or
stack records.

It does not prove runtime hit counts or four-zoom coverage. This is static
installed-bundle structure proof for the shared constructor paths.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Helper field offsets:
  `sed -n '558102,558220p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`
- First later constructor writes:
  `sed -n '966565,966660p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`
- Cross-key constant writes:
  `sed -n '967840,967935p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`
- Higher constructor path:
  `sed -n '971900,972545p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`
- Mirrored higher constructor path:
  `sed -n '975500,975875p' /Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`

## Proven Facts

### 1. The payload copy helpers have fixed destination offsets

The helper bodies are small direct field-copy routines:

- `0x2415d0(dst, src)` copies `src+0x00` to `dst+0x30` and `src+0x04` to
  `dst+0x34`.
- `0x2415f0(dst, src)` copies `src+0x00` to `dst+0x38` and `src+0x04` to
  `dst+0x3c`.
- `0x241610(dst, src)` copies `src+0x00` to `dst+0x40` and `src+0x04` to
  `dst+0x44`.
- `0x241630(dst, src)` copies `src+0x00` to `dst+0x48` and `src+0x04` to
  `dst+0x4c`.
- `0x2416b0(dst, src)` copies `src+0x00..+0x20` to
  `dst+0x50..+0x70`.
- `0x241670(dst, src)` copies `src+0x00` to `dst+0x74` and `src+0x04` to
  `dst+0x78`.
- `0x241650(dst, src)` copies `src+0x00` to `dst+0x7c` and `src+0x04` to
  `dst+0x80`.

Safe statement: when the first argument is proven to be a `state+0x448` payload
pointer, these helpers prove exact destination offsets. When the first argument
is stack or a separate record, they do not prove `state+0x448` writes.

### 2. The longer constructor directly fills payload `+0x30..+0x3c`

After the first insertion loop, the constructor computes two stack outputs from
an object-derived input:

- `0x3f3503..0x3f350b`: calls `0xf3350(object)` and advances to
  `f3350_result+0x8`.
- `0x3f3514..0x3f352c`: calls `0x260e40` with output at `-0x520`,
  input at `f3350_result+0x8`, `edx=1`, and auxiliary output stack slots
  `-0x5d8` / `-0x5d0`.

The same function then performs keyed `state+0x448` lookups before writing:

- `0x3f3531..0x3f358e`: walks the tree loaded from the saved
  `state+0x448` control pointer, comparing the current key with `node+0x1c`.
- `0x3f358e`: converts the matching node to payload pointer `node+0x20`.
- `0x3f3592..0x3f3599`: calls `0x2415d0(payload, -0x5d0)`, writing payload
  `+0x30/+0x34`.
- `0x3f359e..0x3f35ea`: repeats the same `state+0x448` keyed lookup.
- `0x3f35ea`: converts the matching node to payload pointer `node+0x20`.
- `0x3f35ee..0x3f35f5`: calls `0x2415f0(payload, -0x5d8)`, writing payload
  `+0x38/+0x3c`.

Safe statement: payload fields `+0x30..+0x3c` are direct later
`state+0x448` payload writes sourced from stack outputs of the nearby
`0x260e40` call. The semantic names of those stack outputs are not proven here.

### 3. Multiple paths directly set payload `+0x40..+0x4c` to `(0.5, 0.5)`

The immediate constant is `0x3f0000003f000000`, two packed IEEE-754
`0.5f` values.

Direct traced writes:

- `0x3f4cab..0x3f4cfb`: looks up a key in `state+0x448`; `0x3f4cfb` sets
  `r15 = node+0x20`.
- `0x3f4cff..0x3f4d1a`: calls `0x241630` with `r15` and the packed
  `0.5f` pair stack slot, writing payload `+0x48/+0x4c`.
- `0x3f4d1f..0x3f4d30`: calls `0x241610` with `r15` and the packed
  `0.5f` pair stack slot, writing payload `+0x40/+0x44`.
- `0x3f95db..0x3f9635`: looks up key `r15d` in `state+0x448`, converts the
  found node to payload, then calls `0x241610` with the packed `0.5f` pair.
- `0x3f963a..0x3f9698`: repeats the lookup and calls
  `0x241630` with the packed `0.5f` pair.
- `0x3f9900..0x3f997b`: looks up the current vector key in `state+0x448`,
  sets `r13 = node+0x20`, then calls `0x241610` with the packed `0.5f` pair.
- `0x3f9980..0x3f999b`: calls `0x241630` with `r13` and the packed
  `0.5f` pair.
- `0x3fced7..0x3fcf41`: looks up another key in `state+0x448`, sets
  `r13 = node+0x20`, then calls `0x241610` with the packed `0.5f` pair.
- `0x3fcf46..0x3fcf57`: calls `0x241630` with `r13` and the packed
  `0.5f` pair.

Safe statement: these paths directly initialize or normalize found
`state+0x448` payload fields `+0x40..+0x4c` to two `0.5f` pairs. This note
does not assign public calibration names to those pairs.

### 4. Two traced paths directly fill payload `+0x50..+0x80`

In the higher constructor path, `r13` is first proven as a found
`state+0x448` payload:

- `0x3f9900..0x3f995c`: reads `state+0x448`, walks by `node+0x1c`, and sets
  `r13 = node+0x20`.
- No later instruction in the traced span reassigns `r13` before the copy
  helper calls at `0x3f9fba`, `0x3f9fc9`, and `0x3f9fd8`.
- `0x3f9fba`: calls `0x2416b0(r13, -0x760)`, writing payload `+0x50..+0x70`.
- `0x3f9fc9`: calls `0x241670(r13, -0x670)`, writing payload `+0x74/+0x78`.
- `0x3f9fd8`: calls `0x241650(r13, -0x678)`, writing payload `+0x7c/+0x80`.

A mirrored path has the same direct-payload shape:

- `0x3fced7..0x3fcf22`: reads `state+0x448`, walks by `node+0x1c`, and sets
  `r13 = node+0x20`.
- No later instruction in the traced span reassigns `r13` before the copy
  helper calls at `0x3fd54d`, `0x3fd55c`, and `0x3fd56b`.
- `0x3fd54d`: calls `0x2416b0(r13, -0x640)`, writing payload `+0x50..+0x70`.
- `0x3fd55c`: calls `0x241670(r13, -0x550)`, writing payload `+0x74/+0x78`.
- `0x3fd56b`: calls `0x241650(r13, -0x558)`, writing payload `+0x7c/+0x80`.

Safe statement: these two traced paths directly write later
`state+0x448` payload fields through `+0x80`. The source stack records are
computed locally before the helper calls; their public calibration semantics
and LRI origins remain unproven.

### 5. Nearby helper calls that are not `state+0x448` payload writes

The same neighborhoods contain helpers with the same small copy bodies. These
are excluded unless their destination is proven as a found `state+0x448`
payload.

Excluded by destination:

- `0x3f3379..0x3f3480`: copies `0x23faf0` output into a separate
  `state+0x418/+0x420` record, not into `state+0x448`.
- `0x3f35fa..0x3f38e4`: continues working with the separate
  `state+0x418/+0x420` structure, not direct `state+0x448` payload writes.
- `0x3f4e2e` and `0x3f4e4c`: normalize a stack record at `-0x380`, then use
  that stack record in `0x23faf0`; they are not direct `state+0x448` writes.
- `0x3f9ad3` and `0x3f9aed`: normalize a stack record at `-0x500`, then use
  that stack record in `0x23faf0`; they are not direct `state+0x448` writes.
- `0x3fd052` and `0x3fd070`: normalize a stack record at `-0x3e0`, then use
  that stack record in `0x23faf0`; they are not direct `state+0x448` writes.

Safe statement: the copy helpers are only evidence for `state+0x448` when the
destination provenance is a found tree-node payload. Helper identity alone is
not enough.

## Safe Conclusion

- Proven:
  after the first `+0x00..+0x2c` payload copies, later direct writes fill
  `state+0x448` payload fields `+0x30..+0x80` in traced constructor paths.
- Proven:
  payload `+0x40..+0x4c` receives two `(0.5f, 0.5f)` pairs in multiple traced
  paths after keyed `state+0x448` lookup.
- Proven:
  payload `+0x50..+0x80` is populated through `0x2416b0`, `0x241670`, and
  `0x241650` in two traced paths where the destination register remains the
  found `state+0x448` payload pointer.
- Proven:
  nearby stack-only and separate-record helper calls must remain excluded from
  `state+0x448` truth.
- Still unproven:
  public calibration field names, LRI calibration-block origins, the semantic
  name of `object+0x30`, the `state+0xe0` object-bank semantics, and any
  additional payload fields not covered by the direct writes through `+0x80`.

## Consequence For Blocker Work

Future work should not ask whether later `state+0x448` payload fields are
written only through the first insertion loop. The direct write surface is now
bounded through `+0x80`.

Future work should decode:

- public calibration meanings for payload fields `+0x00..+0x80`
- the LRI block(s) and object banks that supply the source records
- the semantic meaning of `object+0x30`
- whether any payload fields beyond the direct writes through `+0x80` are live
