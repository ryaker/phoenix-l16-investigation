# Bundle Proof: IRAMP Record Producer Scale And Dispatch

## Scope

This note proves only the installed-bundle producer-side facts that are visible
around the `0x50` records later consumed by IRAMP's second pair-grid transform.

It builds on:

- [bundle_proof_initresamp_post_wrapper_records.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_initresamp_post_wrapper_records.md)
- [bundle_proof_iramp_live_signature_and_warp_records.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_live_signature_and_warp_records.md)
- [bundle_proof_iramp_pair_grid_transform_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_pair_grid_transform_formula.md)

It does not prove public calibration names for the row fields.

It does not prove the semantic meaning of the map stored at `record+0x40`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Record composer:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e500 --count 100'`
- Row-composition helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e0c0 --count 220'`
- Reciprocal helpers:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e560 --count 50'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x25e590 --count 50'`
- Shared constant read:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format f --size 4 --count 1 0x5a8128'`
- Record dispatcher:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3f7040 --count 130'`
- Same-category producer branch:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3f70d0 --count 180'`
- Cross-category producer branch:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3f72f0 --count 220'`
- Source-record helpers:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3faed0 --count 260'`
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3fb1a0 --count 260'`
- Map-provider helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x268480 --count 130'`

## Proven Facts

### 1. `0x3f7040` dispatches by two `0xf6c60`-derived categories

At `0x3f7061..0x3f706d`, `0x3f7040` calls `0xf6c60` with the current key and
keeps the returned category.

At `0x3f7071..0x3f7088`, it obtains a second key through the object at
`state+0xe0`, calls `0xf6c60` for that key, and compares the two categories.

If the categories match, `0x3f708e..0x3f709e` calls `0x3f70d0`.

If the categories differ, `0x3f70a5..0x3f70b5` calls `0x3f72f0`.

Both calls preserve the same output record pointer, state pointer, current key,
scale-pair pointer, and flag argument.

### 2. The same-category branch builds two source records, then composes one output record

The same-category branch at `0x3f70d0` first verifies a depth-completion
condition. If the last set bit found from `state+0x10/+0x18` does not equal the
last element implied by `(state+0xc8 - state+0xc0) / 8 - 1`, it throws:

```text
Depth is not finished.
```

When that guard passes:

- `0x3f715e..0x3f7179` builds one source record with `0x3faed0` using the key
  obtained through `state+0xe0`.
- `0x3f717e..0x3f718e` builds one source record with `0x3faed0` using the
  current key.
- `0x3f7193..0x3f719d` calls `0x268480` on `state+0xb0`.
- `0x3f71a2..0x3f71b6` calls `0x25e500(output, source_a, source_b, map_ptr)`.
- `0x3f721c..0x3f7222` calls `0x25e590(output, scale_pair_ptr)`.

This proves a concrete producer path for the final `0x50` record, but it does
not name the calibration semantics of the source records.

### 3. The cross-category branch also composes through `0x25e500`

The cross-category branch at `0x3f72f0` requires `*(int32 *)(state+0x8) == 8`.
If not, it throws:

```text
Online calibration is not finished.
```

When that guard passes:

- `0x3f731a..0x3f732a` builds an intermediate source record with `0x3fb1a0`.
- `0x3f732f..0x3f733c` calls `0x264460` with that source record and the
  scale-pair pointer.
- `0x3f7456..0x3f7471` builds another source record with `0x3faed0` using the
  key obtained through `state+0xe0`.
- `0x3f7476..0x3f7480` calls `0x268480` on `state+0xb0`.
- `0x3f7485..0x3f7499` calls `0x25e500(output, source_a, source_b, map_ptr)`.
- `0x3f74d3..0x3f74d9` calls `0x25e590(output, scale_pair_ptr)`.

This proves that both dispatcher branches converge on the same final record
composer and reciprocal scale writer.

### 4. `0x25e500` initializes the `0x50` output record, composes rows, then stores the map pointer

At `0x25e50d..0x25e549`, `0x25e500` initializes the output record:

```text
record+0x00..0x3f = 4x4 identity-like float matrix
record+0x40       = 0
record+0x48       = 1.0
record+0x4c       = 1.0
```

At `0x25e54d`, it calls `0x25e0c0`.

At `0x25e552`, after `0x25e0c0` returns, it stores the incoming fourth argument
into `record+0x40`.

Therefore `0x25e500` proves the producer-side source of `record+0x40`: it is
the map pointer passed to `0x25e500` by the caller.

### 5. `0x25e0c0` writes only the row area of the `0x50` output record

`0x25e0c0` reads fields from its two source-record arguments, converts many of
them through double-precision temporaries, calls helper bodies including
`0x25ec70` and `0x9db20`, and then writes the output row area.

The visible output writes are:

- `0x25e441..0x25e450`: output `+0x00`, `+0x04`, `+0x08`, `+0x0c`
- `0x25e455..0x25e465`: output `+0x10`, `+0x14`, `+0x18`, `+0x1c`
- `0x25e46a..0x25e47b`: output `+0x20`, `+0x24`, `+0x28`, `+0x2c`
- `0x25e480..0x25e492`: output `+0x30`, `+0x34`, `+0x38`, `+0x3c`

No visible write in this body writes output `+0x40`, `+0x48`, or `+0x4c`.

Therefore, in this composer path:

- `record+0x00..0x3c` are produced by `0x25e0c0`
- `record+0x40` is written by `0x25e500` after `0x25e0c0`
- `record+0x48/+0x4c` are written later by `0x25e590`

### 6. `0x25e560` and `0x25e590` are reciprocal helpers over the same `1.0` constant

The shared constant used by both helpers is `0x5a8128`, and the installed bundle
reads it as:

```text
0x005a8128: 1
```

`0x25e560(dst_pair, record)` computes:

```text
dst_pair[0] = 1.0 / *(float *)(record + 0x48)
dst_pair[1] = 1.0 / *(float *)(record + 0x4c)
```

Instruction anchors:

- `0x25e564`: load `1.0`
- `0x25e56f`: divide by `record+0x48`
- `0x25e574`: divide by `record+0x4c`
- `0x25e579..0x25e57d`: write the two-float output

`0x25e590(record, src_pair)` computes:

```text
*(float *)(record + 0x48) = 1.0 / src_pair[0]
*(float *)(record + 0x4c) = 1.0 / src_pair[1]
```

Instruction anchors:

- `0x25e594`: load `1.0`
- `0x25e59f`: divide by `src_pair[0]`
- `0x25e5a3`: divide by `src_pair[1]`
- `0x25e5a8..0x25e5ad`: write `record+0x48/+0x4c`

### 7. The post-wrapper `initResAmp` insertion path normalizes `record+0x48/+0x4c` to `(1.0, 1.0)`

The already-proven post-wrapper `initResAmp` path calls `0x3f7040` with:

```text
rcx = &PipelineCache+0x1e8
```

Both `0x3f7040` branches call `0x25e590(output, rcx)` before returning, so
their output scale fields become:

```text
record+0x48 = 1.0 / PipelineCache+0x1e8
record+0x4c = 1.0 / PipelineCache+0x1ec
```

Immediately after the `0x3f7040` call, the post-wrapper `initResAmp` body:

1. calls `0x25e560` on the stack record
2. divides the resulting pair by `PipelineCache+0x1e8/+0x1ec`
3. calls `0x25e590` again on the same stack record
4. copies the `0x50` record into `PipelineCache+0x258`

Algebraically, in this specific insertion path:

```text
after 0x3f7040:
  sx = 1.0 / ratio_x
  sy = 1.0 / ratio_y

after 0x25e560:
  tmp_x = ratio_x
  tmp_y = ratio_y

after division by PipelineCache ratios:
  tmp_x = 1.0
  tmp_y = 1.0

after the final 0x25e590:
  record+0x48 = 1.0
  record+0x4c = 1.0
```

This proves the final stored `PipelineCache+0x258` record scale fields for the
post-wrapper `initResAmp` insertion path. It does not prove that every other
possible caller of `0x3f7040` stores normalized scale fields.

## Safe Conclusion

- Proven:
  both `0x3f7040` dispatcher branches converge on `0x25e500` and `0x25e590`.
- Proven:
  `0x25e500` uses `0x25e0c0` to write the four vec4 row fields, then stores the
  caller-supplied map pointer at `record+0x40`.
- Proven:
  `0x25e560` and `0x25e590` are reciprocal helpers over constant `1.0`.
- Proven:
  in the post-wrapper `initResAmp` path that inserts records into
  `PipelineCache+0x258`, the final stored `record+0x48/+0x4c` values are
  normalized to `(1.0, 1.0)`.
- Still unproven:
  public calibration names and semantic meaning for `record+0x00..0x3c` and the
  map stored at `record+0x40`.

## Consequence For Blocker Work

The producer-side pair-grid blocker is narrower again.

Future work should not ask whether the live `PipelineCache+0x258` records come
from `0x3f7040`, whether both category branches converge on `0x25e500`, whether
`record+0x40` is caller-supplied map state, or whether `+0x48/+0x4c` remain
non-unit after the post-wrapper insertion path. Those fields are proven
normalized to `(1.0, 1.0)` in that path.

Future work should decode:

- later field semantics and public calibration origin of the `state+0x448`
  source-record family
- the LRI calibration-block origin of the `state+0xe0` object banks
- the public semantic names for the source-record fields composed by `0x23faf0`
- the semantic meaning and calibration origin of the map pointer returned
  through `0x268480`
