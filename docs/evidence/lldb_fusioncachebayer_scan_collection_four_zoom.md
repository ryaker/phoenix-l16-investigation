# LLDB Evidence: `FusionCacheBayer` `0x402d20` Scan Collection Across Four Zooms

## Scope

This proof extends the `FusionCacheBayer+0x18` constructor-origin evidence by
capturing the scanned upstream records inside `0x402d20`.

It proves the tested scan-loop predicate under the canonical bridge HDR quartet:

1. `0x402d20` iterates `0x10`-byte records.
2. Each record item pointer supplies key field `+0x60` through `0xf2720`.
3. The key is normalized through `0xf6c60` and compared to the constructor's
   target-normalized bucket.
4. Only normalized-bucket matches call `0xf2750`.
5. The `0xf2750` two-int field at item `+0x58/+0x5c` must have a sign bit set
   after OR for the record to be eligible.
6. The first eligible key replaces sentinel `16`; if no eligible record is
   found, sentinel `16` remains and `FusionCacheBayer+0x18` is written as `0`.
7. Static follow-up proves `0xf6c60` maps camera IDs `0..4`, `5..9`, and
   `10..15` to group ordinals `0`, `1`, and `2`.
8. Static follow-up proves `0x137d70` is a camera-ID range check / identity
   helper for IDs `0..15`, and `0xf2770` stores its result into item `+0x60`
   from input field `+0x30`.
9. Static follow-up proves item fields `+0x58/+0x5c` are assigned inside
   constructor path `0xf2770`, including switch-derived defaults, optional
   input override, and later adjustment logic.

This is structural scan-loop evidence. It does not name the public meaning of
fields `+0x58/+0x5c`, the LRI origin of the input fields feeding `0xf2770`,
or optional `FusionCacheBayer+0x20`.

## Artifacts

- Runtime helper:
  [scan_collection_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_probe.py)
- Runtime scripts:
  [scan_collection_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_28mm.lldb),
  [scan_collection_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_35mm.lldb),
  [scan_collection_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_70mm.lldb),
  [scan_collection_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_150mm.lldb)
- Runtime JSON reports:
  `runs/fusioncachebayer_scan_collection/scan_collection_28mm.json`,
  `runs/fusioncachebayer_scan_collection/scan_collection_35mm.json`,
  `runs/fusioncachebayer_scan_collection/scan_collection_70mm.json`,
  `runs/fusioncachebayer_scan_collection/scan_collection_150mm.json`
- Runtime HDR outputs:
  `runs/fusioncachebayer_scan_collection/scan_collection_28mm.hdr`,
  `runs/fusioncachebayer_scan_collection/scan_collection_35mm.hdr`,
  `runs/fusioncachebayer_scan_collection/scan_collection_70mm.hdr`

The `150mm` JSON report is valid for pre-crash scan-loop facts, but the
instrumented render stopped after those facts with the already known
instrumentation-sensitive `libcp+0x2e945d` crash. The `150mm` run is therefore
not an output-completion proof, and its zero-byte HDR path must not be cited as
render evidence.

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_28mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_35mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/fusioncachebayer_scan_collection/scan_collection_150mm.lldb
```

## Static Anchor

The scan loop is inside `0x402d20`:

- `0x402dc4..0x402dc7`: loads begin/end pointers for the `0x10`-stride record
  vector.
- `0x402dcb`: initializes `r15d = 0x10`.
- `0x402de0..0x402de3`: reads record item pointer and retained pointer.
- `0x402df4..0x402e10`: obtains key field `+0x60` through `0xf2720` and
  normalizes it through `0xf6c60`.
- `0x402e10..0x402e16`: compares the current normalized key with the
  constructor target-normalized bucket.
- `0x402e18..0x402e25`: only for matching normalized keys, reads the two-int
  field returned by `0xf2750` and ORs the two ints.
- `0x402e25`: skips unless the OR result has a sign bit set.
- `0x402e27..0x402e35`: if `r15d` is still sentinel `16`, stores the candidate
  key into `r15d`.
- `0x402e6a..0x402e78`: writes `FusionCacheBayer+0x18 = (r15d != 16)`.

## Static Follow-Up: Camera-ID Validation And Grouping

The key and group helpers used by `0x402d20` are now statically bounded:

- `0x137d70` returns its input unchanged for `0 <= id < 16`.
- `0x137d70` throws the installed-bundle string
  `Invalid camera id requested!` for out-of-range IDs.
- `0xf6c60` returns group ordinal `0` for IDs `0..4`, group ordinal `1` for
  IDs `5..9`, and group ordinal `2` for IDs `10..15`.
- `0xf6c60` throws the installed-bundle string `unknown camera group type!`
  for out-of-range IDs.
- Using the already-established camera-id mapping, those ranges are
  `A1..A5`, `B1..B5`, and `C1..C6`.

Constructor path `0xf2770` is the direct static producer for the scanned item
fields relevant here:

- `0xf27a1..0xf27ad` reads input `+0x30`, calls `0x137d70`, and stores the
  validated camera ID to item `+0x60`.
- `0xf27b0..0xf27b4` copies input byte `+0x60` to item `+0x30`.
- `0xf2d1b..0xf2d4c` assigns default item fields `+0x58/+0x5c` from a
  resolved local value: value `1` gives `(0,0)`, values `2` and `4` give
  `(1,0)`, and values `3` and `5` give `(-1,-1)`.
- `0xf2d4c..0xf2d71` can override `+0x58/+0x5c` from an optional input
  record at input `+0x28`, reading its `+0x18` qword as two int32 fields.
- `0xf2d75..0xf2def` can adjust the two fields based on item `+0x100`,
  item `+0x4c`, and the current `+0x58/+0x5c` values.

This proves the item key is a validated camera-ID-range integer on this
constructor path. It does not prove the public LRI field origin of input
`+0x30`, input byte `+0x60`, optional input record `+0x28`, or the public
semantic name for the two-int `+0x58/+0x5c` pair.

## Runtime Summary

| Seed | Records | Normalized-bucket keys | First eligible key | Final `r15d` | Written flag |
|---|---:|---|---:|---:|---:|
| `28mm` / `L16_02130` | `10` | `0,4,1,2,3` | `1` | `1` | `1` |
| `35mm` / `L16_03041` | `10` | `0,4,1,2,3` | `1` | `1` | `1` |
| `70mm` / `L16_03434` | `11` | `6,8,9,5,7` | none | `16` | `0` |
| `150mm` / `L16_02285` | `11` | `6,8,9,5,7` | none | `16` | `0` |

## Wide-Tier Record Facts

The accepted wide records are identical in shape at `28mm` and `35mm`.

| Record index | Key `+0x60` | `object+0x30` | Field `+0x58,+0x5c` | Normalized match | Sign bit | Accepted |
|---:|---:|---:|---|---|---|---|
| `0` | `0` | `1` | `(1, 0)` | yes | no | no |
| `1` | `4` | `1` | `(0, 1)` | yes | no | no |
| `2` | `6` | `1` | `(1, 1)` | no | not tested | no |
| `3` | `8` | `1` | `(1, 1)` | no | not tested | no |
| `4` | `9` | `1` | `(0, 0)` | no | not tested | no |
| `5` | `1` | `1` | `(-1, -1)` | yes | yes | yes |
| `6` | `2` | `1` | `(1, 0)` | yes | no | no |
| `7` | `3` | `1` | `(1, 0)` | yes | no | no |
| `8` | `5` | `1` | `(0, 0)` | no | not tested | no |
| `9` | `7` | `1` | `(1, 1)` | no | not tested | no |

## Tele-Tier Record Facts

The tele records are identical in shape at `70mm` and `150mm` for this tested
predicate.

| Record index | Key `+0x60` | `object+0x30` | Field `+0x58,+0x5c` | Normalized match | Sign bit | Accepted |
|---:|---:|---:|---|---|---|---|
| `0` | `6` | `1` | `(1, 1)` | yes | no | no |
| `1` | `8` | `1` | `(1, 1)` | yes | no | no |
| `2` | `9` | `1` | `(0, 0)` | yes | no | no |
| `3` | `14` | `1` | `(1, 1)` | no | not tested | no |
| `4` | `5` | `1` | `(0, 0)` | yes | no | no |
| `5` | `7` | `1` | `(1, 1)` | yes | no | no |
| `6` | `11` | `1` | `(1, 1)` | no | not tested | no |
| `7` | `10` | `1` | `(0, 0)` | no | not tested | no |
| `8` | `12` | `1` | `(0, 0)` | no | not tested | no |
| `9` | `13` | `1` | `(1, 1)` | no | not tested | no |
| `10` | `15` | `0` | `(-1, -1)` | no | not tested | no |

Later evidence in [lldb_capturedimage_f2770_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_capturedimage_f2770_origin_four_zoom.md)
and [lldb_c6_active_byte_mutation_watch_tele.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_c6_active_byte_mutation_watch_tele.md)
proves this `object+0x30 = 0` value is post-constructor state: tele key `15`
is constructed with item `+0x30 = 1` and later cleared at `libcp+0x3c90a5`.

## Proven Facts

- The wide-tier canonical seeds scan `10` records and preserve the same key
  order and predicate shape under this probe.
- The tele-tier canonical seeds scan `11` records and preserve the same key
  order and predicate shape under this probe.
- At `28mm` and `35mm`, only key `1` both matches the target-normalized bucket
  and has a sign-bit OR result from fields `+0x58/+0x5c`; it becomes final
  `r15d = 1`, and byte `+0x18` is written as `1`.
- At `70mm` and `150mm`, no key in the target-normalized bucket has sign-bit
  fields; final `r15d` remains sentinel `16`, and byte `+0x18` is written as
  `0`.
- Tele key `15` has fields `(-1, -1)` and post-constructor-mutated
  `object+0x30 = 0`, but it does not match the target-normalized bucket in this
  `0x402d20` predicate, so
  `0x402d20` does not call `0xf2750` on it in the observed branch.
- Static proof identifies the normalization bucket as the `0xf6c60` camera-ID
  group ordinal: IDs `0..4`, `5..9`, and `10..15` map to ordinals `0`, `1`,
  and `2`.
- Static proof identifies item `+0x60`, for objects constructed by `0xf2770`,
  as the range-checked camera ID produced by `0x137d70` from input `+0x30`.
- Static proof identifies `+0x58/+0x5c` as constructor-assigned two-int
  fields inside `0xf2770`, with switch defaults, an optional input override,
  and later adjustment logic. Public field semantics and LRI origin remain
  unproven.

## Safe Conclusion

The constructor selector behind visible-`src2` branch `0x406a10` is now bounded
one level deeper:

- Wide tier: the scan loop finds key `1` as the first target-normalized record
  whose `+0x58/+0x5c` pair has a sign bit set.
- Tele tier: the scan loop finds no target-normalized record whose
  `+0x58/+0x5c` pair has a sign bit set, so sentinel `16` remains.

This still does not prove the public meaning of the accepted key `1` beyond its
established camera-id mapping, the public meaning of sentinel `16`, the public
meaning / LRI origin of fields `+0x58/+0x5c`, the LRI origin of the input field
that becomes item `+0x60`, or optional `FusionCacheBayer+0x20`.

## Remaining Unknowns

- Public semantic meaning and LRI origin of item fields `+0x58/+0x5c`.
- Public LRI origin of the input field that becomes item key field `+0x60`.
- Why tele key `15` carries `(-1, -1)` while not matching this predicate's
  normalized bucket. The later `object+0x30 = 0` state is now explained as a
  post-constructor mutation at `libcp+0x3c90a5`, but terminality remains open.
- Public semantic name of optional `FusionCacheBayer+0x20`.
- Whether this constructor selector contributes only to source-descriptor
  adaptation or also to later merge-quality / acceptance policy.
