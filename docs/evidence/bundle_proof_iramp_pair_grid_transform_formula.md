# Bundle Proof: IRAMP Pair-Grid Transform Consumer Formula

## Scope

This note proves only the consumer-side formula visible in the installed
`libcp.dylib` for the second IRAMP pair-grid transform at
`0x366b80..0x366d59`.

It builds on:

- [bundle_proof_pair_grid_roi_transform.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_pair_grid_roi_transform.md)
- [bundle_proof_iramp_live_signature_and_warp_records.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_live_signature_and_warp_records.md)

It does not prove the producer-side semantic names for each record field.

It does not prove how `0x3f7040` / `0x3f70d0` / `0x3f72f0` derive all fields in
the `0x50`-byte records.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Consumer disassembly:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x366b80 --count 130'`
- Constant reads:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format f --size 4 --count 1 0x5a8128' -o 'memory read --format f --size 4 --count 1 0x5a886c' -o 'memory read --format f --size 4 --count 1 0x5d4c20'`

## Proven Facts

### 1. The selected record exposes four vec4 rows, one map pointer, and two scale floats

For each source-vector index, `0x3661b0` selects a matching `0x50`-byte record
from the live `PipelineCache+0x258` vector.

The consumer at `0x366b92..0x366bc7` uses these fields:

- `record+0x00`: vec4 used as the first scaled-coordinate row
- `record+0x10`: vec4 used as the second scaled-coordinate row
- `record+0x20`: vec4 used as the sampled-map row
- `record+0x30`: vec4 added as a constant row / bias row
- `record+0x40`: pointer to an image-like float map
- `record+0x48`: x scale
- `record+0x4c`: y scale

The field labels above describe only the visible consumer role. They are not
public class or calibration names.

### 2. The loop rejects first-grid pairs outside the source dimensions

At `0x366c70..0x366c90`, each first-grid pair is read from the first grid:

- `x = *(int32 *)(pair + 0)`
- `y = *(int32 *)(pair + 4)`

The pair is rejected if:

- `x >= source_dim_0` from `source+0x30`
- `y >= source_dim_1` from `source+0x34`
- either coordinate is negative, via `or` then sign-bit test

Rejected pairs write sentinel `0x8000000080000000` at `0x366da0..0x366daa`.

### 3. The accepted pair is scaled and used to sample the record's float map

At `0x366c96..0x366cd3`, accepted pairs are converted to float and scaled:

```text
u = float(x) * *(float *)(record + 0x48)
v = float(y) * *(float *)(record + 0x4c)
```

The map object is loaded from `record+0x40`.

The sample index uses:

- `int(u)` as x index
- `int(v)` as y index
- map stride from `map+0x18`
- map data pointer from `map+0x20`

The sampled scalar is:

```text
m = map[int(v) * stride + int(u)]
```

### 4. The transform forms one homogeneous-like vec4

At `0x366cd8..0x366d0a`, the code forms a vec4:

```text
H = (m * u) * R0 + (m * v) * R1 + m * R2 + R3
```

where:

```text
R0 = vec4(record + 0x00)
R1 = vec4(record + 0x10)
R2 = vec4(record + 0x20)
R3 = vec4(record + 0x30)
```

Instruction anchors:

- `0x366cd8..0x366cdc`: multiply `u` and `v` by `m`
- `0x366ce0..0x366ceb`: broadcast `m*u` and multiply by `R0`
- `0x366cee..0x366cf9`: broadcast `m*v` and multiply by `R1`
- `0x366cfc..0x366d00`: broadcast `m` and multiply by `R2`
- `0x366d03`: add `R3`
- `0x366d07..0x366d0a`: add the `R0` and `R1` terms

### 5. The output pair is a rounded divide by component 2

At `0x366d0d..0x366d59`, the code divides component 0 and component 1 by
component 2:

```text
px = H[0] / H[2]
py = H[1] / H[2]
```

Instruction anchors:

- `0x366d14`: `shufpd $0x1` moves `H[2]` into the scalar divide lane
- `0x366d19..0x366d1c`: computes `1.0 / H[2]`
- `0x366d20`: computes `H[1] / H[2]`
- `0x366d32`: computes `H[0] / H[2]`

The constants read from the installed bundle are:

- `0x5a8128`: `1.0`
- `0x5a886c`: `0.5`
- `0x5d4c20`: `-8.0`

The bounds checks are:

```text
-8.0 <= py < source_dim_1 + 7
-8.0 <= px < source_dim_0 + 7
```

If either check fails, the sentinel is written.

If both checks pass, the stored pair is:

```text
out_x = int_trunc(px + 0.5)
out_y = int_trunc(py + 0.5)
```

The writes occur at:

- `0x366d54`: `out_x`
- `0x366d59`: `out_y`

## Safe Conclusion

- Proven:
  the consumer-side second-grid transform is a sampled-map-modulated vec4
  projection followed by divide-by-component-2, bounded acceptance, rounding,
  and int32 pair write.
- Proven:
  the accepted output range is checked against `[-8, source_dim + 7)` before
  rounding.
- Still unproven:
  the producer-side row and map calibration semantics for the `0x50`-byte
  record fields. Later evidence narrows the producer-side dispatcher,
  row/map writer split, row-composition matrix chain, and final scale-field
  normalization.

## Consequence For Blocker Work

The pair-grid blocker is narrower again.

Future work should not ask what the second-grid consumer formula is. The
consumer formula is now bundle-proven.

Future work should decode the producer-side calibration semantics behind:

- `record+0x00`
- `record+0x10`
- `record+0x20`
- `record+0x30`
- `record+0x40`

The relevant producer path remains the `initResAmp` per-key record construction
through `0x3f7040`, with the currently proven producer split documented in
[bundle_proof_iramp_record_producer_scale_and_dispatch.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_record_producer_scale_and_dispatch.md).
