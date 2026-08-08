# LLDB Evidence: Index-5 Lookup Vector Public-Origin Check, Four Zoom

## Scope

This note refines the remaining public-origin gap for the tracked index-5
`StereoLayer<false>+0xe0` lookup vector used by the proven
`0x299c70 -> 0x267010` source-index path.

It builds on:

- [lldb_index5_267010_mapping_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_267010_mapping_four_zoom.md)
- [lldb_index5_source_lookup_origin_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_lookup_origin_watch_four_zoom.md)
- [lldb_index5_source_object_field_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_object_field_origin_four_zoom.md)
- [lldb_29a140_source_local_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_29a140_source_local_producer_four_zoom.md)

It proves a narrow internal generator/copy boundary and a negative direct-public
origin result:

- `0x26c480` calls `0x28fa60` / `0x28f5a0` to build a stack float vector, then
  copies that vector into `StereoLayer<false>+0xe0` through `0xf02d0`;
- the retained target object fields at the copy point are index `5`, mode `8`,
  dimensions `2080 x 1560`, and `this+0x298/+0x29c = [200.0, 640000.0]`;
- helper `0x28f860` generates the vector as a float32 reciprocal near/far ramp
  from `640000.0` down to `200.0`;
- the copied source span and final `this+0xe0` destination bytes are identical;
- the final vector reaches the later `0x267010` call unchanged as
  `rdx == this+0xe0`;
- the full vector is not an exact byte sequence in any checked LRI block
  payload, and is not an exact fixed32 sequence in the public calibration
  payloads.

This admits the internal lookup-vector meaning as a generated near/far
reciprocal table. Follow-up
[lldb_lookup_endpoint_count_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_lookup_endpoint_count_origin_four_zoom.md)
closes the endpoint/count producer mechanics as static binary endpoint
constants plus internal `0x28f5a0` source-record count math. Public
LRI/protobuf field names, source-record public names, lookup-vector physical
meaning, and the physical name of the source-index descriptor that indexes the
table remain open.

## Artifacts

- Runtime probe:
  [lookup_vector_public_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_probe.py)
- Runtime verifier:
  [verify_lookup_vector_public_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py)
- Static extractor:
  [static_lookup_vector_generator.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/static_lookup_vector_generator.lldb)
- Runtime LLDB scripts:
  [lookup_vector_public_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_28mm.lldb),
  [lookup_vector_public_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_35mm.lldb),
  [lookup_vector_public_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_70mm.lldb),
  [lookup_vector_public_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_150mm.lldb)
- Runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/run_four_zoom.sh)
- Raw outputs:
  `runs/codex_index5_lookup_vector_public_origin/`

The admitted runtime JSON reports and static log have no matches for
`Traceback`, `error:`, `warning:`, `lost connection`, `EXC`, `SIGABRT`, or
`SIGSEGV`.

## Static Boundary

Static extraction in
`runs/codex_index5_lookup_vector_public_origin/static_lookup_vector_generator.log`
shows the generator/copy path:

```text
0x26c497  movss 0x298(%rbx), %xmm0
0x26c49f  movss 0x29c(%rbx), %xmm1
0x26c4ba  callq 0x28fa60
0x26c4bf  leaq 0xe0(%rbx), %rdi
0x26c4cf  movq -0x40(%rbp), %rsi
0x26c4d3  movq -0x38(%rbp), %rdx
0x26c4d7  callq 0xf02d0
```

`0x28fa60` is a thunk to `0x28f5a0`. That body computes a count, rounds it by
the mode/step input, and calls `0x28f860` to build the vector. `0x28f860`
contains explicit validation strings for near/far ordering and positivity, then
builds the vector using reciprocal spacing:

```text
step = (1.0 / near - 1.0 / far) / (count - 1)
lookup[i] = 1.0 / (1.0 / far + i * step)
lookup[count - 1] = near
```

The static formula is mirrored in the verifier with float32 arithmetic. For the
tracked object, the retained runtime endpoints are:

```text
near = this+0x298 = 200.0
far  = this+0x29c = 640000.0
```

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

At the `0xf043e` post-copy breakpoint, every tier has the same stack prefix:

```text
0xf043e <- 0x26c4dc <- 0x26bdf8 <- 0x26895a <- 0x2687ab <- 0x3fcb86
```

| Focal tier | Count | Bytes | SHA-256 prefix | Formula | Source span equals `this+0xe0` | Later `0x267010` |
|---|---:|---:|---|---|---|---|
| `28mm` | 752 | 3008 | `e52206cbe601e978` | reciprocal `640000 -> 200` | yes | unchanged |
| `35mm` | 752 | 3008 | `e52206cbe601e978` | reciprocal `640000 -> 200` | yes | unchanged |
| `70mm` | 1472 | 5888 | `85202a045de94c33` | reciprocal `640000 -> 200` | yes | unchanged |
| `150mm` | 1472 | 5888 | `85202a045de94c33` | reciprocal `640000 -> 200` | yes | unchanged |

Representative endpoints:

| Focal tier | First four float32 values | Last four float32 values |
|---|---|---|
| `28mm` / `35mm` | `640000.0`, `121681.015625`, `67231.78125`, `46447.62109375` | `200.802231`, `200.534225`, `200.266922`, `200.0` |
| `70mm` / `150mm` | `640000.0`, `201593.15625`, `119639.09375`, `85059.6328125` | `200.411209`, `200.274826`, `200.138626`, `200.0` |

## Public-Origin Check

The verifier scans the real LRI block payloads for each canonical focal tier
and recursively walks the public calibration payloads with sizes `32832`,
`262968`, and `35266`.

Accepted negative checks:

| Focal tier | Full vector in any LRI block payload | Full vector as calibration fixed32 sequence | Scalar fixed32 hits in calibration payloads |
|---|---:|---:|---:|
| `28mm` | 0 | 0 | `0 / 2708704` |
| `35mm` | 0 | 0 | `0 / 2708704` |
| `70mm` | 0 | 0 | `0 / 5302144` |
| `150mm` | 0 | 0 | `0 / 5302144` |

This rejects treating `StereoLayer<false>+0xe0` as a direct public LRI table or
direct public calibration fixed32 sequence under the checked payload classes.
The admitted positive origin is internal generation from the tracked object's
near/far fields plus the internally computed count.

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet:

```text
StereoLayer<false> index 5
  +0x298/+0x29c = [200.0, 640000.0]
  -> 0x28f5a0 / 0x28f860 generated reciprocal near/far float32 vector
  -> stack vector at caller rbp-0x40
  -> 0xf02d0 copy
  -> StereoLayer<false>+0xe0
  -> later 0x267010 rdx == this+0xe0
```

This closes the internal generated-table mechanics for the lookup vector used
by the sampled source-index-to-float expansion. Follow-up endpoint/count proof
closes the static endpoint constants and internal count producer. By itself it
does not close public source-record names, source-index descriptor semantics,
lookup-vector physical meaning, or final effect. Follow-up
[bundle_static_runtime_index5_triangulator_depth_bound_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_triangulator_depth_bound_custody.md)
admits the lookup's internal reciprocal ray-depth hypothesis-grid role, not
public units or public calibration/LRI/protobuf names.

## Validation

Commands run:

```text
python3 -m py_compile tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_probe.py tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py
bash tools/lldb_probes/codex_index5_lookup_vector_public_origin/run_four_zoom.sh
arch -x86_64 lldb -b -s tools/lldb_probes/codex_index5_lookup_vector_public_origin/static_lookup_vector_generator.lldb > runs/codex_index5_lookup_vector_public_origin/static_lookup_vector_generator.log
python3 tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py
file runs/codex_index5_lookup_vector_public_origin/lookup_vector_public_{28mm,35mm,70mm,150mm}.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' runs/codex_index5_lookup_vector_public_origin
```

Verifier output:

The verifier also requires each admitted paired output file to start with the
Radiance HDR magic bytes.

```text
28mm: OK count=752 sha=e52206cbe601e978 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 121681.016, 67231.781, 46447.621] last4=[200.802231, 200.534225, 200.266922, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/2708704
35mm: OK count=752 sha=e52206cbe601e978 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 121681.016, 67231.781, 46447.621] last4=[200.802231, 200.534225, 200.266922, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/2708704
70mm: OK count=1472 sha=85202a045de94c33 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 201593.156, 119639.094, 85059.633] last4=[200.411209, 200.274826, 200.138626, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/5302144
150mm: OK count=1472 sha=85202a045de94c33 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 201593.156, 119639.094, 85059.633] last4=[200.411209, 200.274826, 200.138626, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/5302144
```
