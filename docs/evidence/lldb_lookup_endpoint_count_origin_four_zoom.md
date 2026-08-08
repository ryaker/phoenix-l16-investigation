# LLDB Evidence: Index-5 Lookup Endpoint / Count Origin, Four Zoom

## Scope

This note extends the generated-table proof in
[lldb_index5_lookup_vector_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_lookup_vector_public_origin_four_zoom.md).

That earlier proof established that the tracked `StereoLayer<false>` index-5
`this+0xe0` table is generated internally as a float32 reciprocal near/far
ramp and is not an exact public LRI table or public calibration fixed32
sequence. This follow-up traces the remaining endpoint and count inputs:

- `this+0x298/+0x29c` are set by `0x26ba90` from scalar arguments propagated
  from a static binary float table selected at `0x3ff407..0x3ff41a`;
- the selected canonical four-zoom endpoint pair is `[200.0, 640000.0]`;
- the index-5 lookup count is produced by `0x28f5a0` from the copied
  `this+0x258` source-record vector, `this+0x18`, the first source-record
  scalar, the endpoint reciprocal span, clamp `0x1000`, and mode rounding by
  `this+0xc = 8`;
- the verified count is `752` for `28mm` / `35mm` and `1472` for
  `70mm` / `150mm`.

This closes the endpoint/count producer mechanics for the tracked generated
lookup vector. It does not assign a public LRI/protobuf name to the physical
quantity represented by the table, the source-index image, or the 0xa8 source
records in `this+0x258`.

## Artifacts

- Runtime probe:
  [endpoint_count_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_probe.py)
- Runtime verifier:
  [verify_endpoint_count_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/verify_endpoint_count_origin.py)
- Static extractor:
  [static_endpoint_count_origin.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/static_endpoint_count_origin.lldb)
- Runtime LLDB scripts:
  [endpoint_count_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_28mm.lldb),
  [endpoint_count_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_35mm.lldb),
  [endpoint_count_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_70mm.lldb),
  [endpoint_count_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_150mm.lldb)
- Runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_lookup_endpoint_count_origin/run_four_zoom.sh)
- Raw outputs:
  `runs/codex_lookup_endpoint_count_origin/`

The admitted runtime JSON reports and static log have no matches for
`Traceback`, `error:`, `warning:`, `lost connection`, `EXC`, `SIGABRT`, or
`SIGSEGV`. All four runs emitted files identified by the OS `file` command as
`Radiance HDR image data`.

## Static Endpoint Origin

The target object is initialized through the call chain observed at runtime:

```text
0x3ff43c -> 0x2681b0 -> 0x26ba90
```

Static extraction in
`runs/codex_lookup_endpoint_count_origin/static_endpoint_count_origin.log`
shows the endpoint scalars are selected from two static float tables:

```text
0x3ff407  leaq 0x20a01a(%rip), %rcx
0x3ff40e  movss (%rcx,%rax,4), %xmm0
0x3ff413  leaq 0x20a016(%rip), %rcx
0x3ff41a  movss (%rcx,%rax,4), %xmm1

0x00609428: 200
0x0060942c: 70
0x00609430: 640000
0x00609434: 40000
```

`0x2681b0` preserves those scalar arguments and forwards them to `0x26ba90`:

```text
0x268258  movss -0xb4(%rbp), %xmm0
0x268260  movss -0xb0(%rbp), %xmm1
0x268268  callq 0x26ba90
```

`0x26ba90` copies the three incoming vectors and stores the endpoint scalars
into the target object:

```text
0x26bae0..0x26baeb  copy rsi source vector to this+0x240
0x26bafc..0x26bb05  copy rdx source-record vector to this+0x258
0x26bb16..0x26bb1d  copy rcx scale vector to this+0x270
0x26bb27            store xmm0 to this+0x298
0x26bb34            store xmm1 to this+0x29c
```

For the tracked canonical index-5 object, runtime after the endpoint store
always observes:

```text
this+0x298 = 200.0
this+0x29c = 640000.0
```

## Static Count Formula

Static extraction shows `0x26c480` reads the endpoint/count inputs and calls
the count/vector generator:

```text
0x26c497  movss 0x298(%rbx), %xmm0
0x26c49f  movss 0x29c(%rbx), %xmm1
0x26c4a7  leaq 0x258(%rbx), %rsi
0x26c4ae  movss 0x18(%rbx), %xmm2
0x26c4b3  movl 0xc(%rbx), %edx
0x26c4ba  callq 0x28fa60
```

`0x28fa60` reaches `0x28f5a0`. The verifier mirrors the installed float32
operations:

```text
record_point(record):
  a = record+0x24
  b = record+0x28
  c = record+0x2c
  x = record+0x38*a + record+0x44*b + record+0x50*c
  y = record+0x34*a + record+0x40*b + record+0x4c*c
  z = record+0x30*a + record+0x3c*b + record+0x48*c

max_distance = max(distance(record_point[0], record_point[i]))
scaled = max_distance * this+0x18 * first_record+0x00 * (1/near - 1/far)
count = min(int(scaled), 0x1000)
count = round_up_to_multiple(count, this+0xc)
```

The generated count is then passed to `0x28f860`, which allocates the float32
lookup vector and fills the reciprocal ramp. The already admitted downstream
copy remains:

```text
0x26c4bf  leaq 0xe0(%rbx), %rdi
0x26c4cf  movq -0x40(%rbp), %rsi
0x26c4d3  movq -0x38(%rbp), %rdx
0x26c4d7  callq 0xf02d0
```

## Runtime Result

The target object has index `5`, mode `8`, dimensions `2080 x 1560`,
`this+0x18 = 2.0`, and an 840-byte `this+0x258` source-record vector
containing five `0xa8` records.

| Focal tier | Endpoint pair | Source records | `max_distance` | First scalar | Rounded count | Lookup SHA-256 prefix |
|---|---:|---:|---:|---:|---:|---|
| `28mm` | `[200, 640000]` | 5 | `43.855167` | `1702.676636` | 752 | `e52206cbe601e978` |
| `35mm` | `[200, 640000]` | 5 | `43.855167` | `1702.676636` | 752 | `e52206cbe601e978` |
| `70mm` | `[200, 640000]` | 5 | `35.540379` | `4140.005859` | 1472 | `85202a045de94c33` |
| `150mm` | `[200, 640000]` | 5 | `35.406025` | `4141.635254` | 1472 | `85202a045de94c33` |

The target lookup-copy stack prefix is identical across all four tiers:

```text
0xf043e <- 0x26c4dc <- 0x26bdf8 <- 0x26895a <- 0x2687ab <- 0x3fcb86
```

At the post-copy breakpoint, `r14 == target_object + 0xe0` in every tier, and
the copied lookup vector length matches the verifier-computed rounded count.

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet:

```text
static endpoint table at 0x609428 / 0x609430
  -> selected pair [200.0, 640000.0]
  -> 0x3ff43c -> 0x2681b0 -> 0x26ba90
  -> StereoLayer<false> index-5 this+0x298/+0x29c
  -> 0x26c480 reads this+0x258, this+0x18, this+0xc, endpoints
  -> 0x28f5a0 computes count from five 0xa8 source records
  -> 0x28f860 generates reciprocal near/far vector
  -> 0xf02d0 copies stack vector into this+0xe0
```

This admits endpoint/count origin for the generated lookup table as installed
binary constants plus internal source-record geometry/count math. It rejects
the narrower unresolved wording that endpoint and count producers are still
unknown. By itself it does not prove a public LRI/protobuf origin or public
semantic name for the source records, the source-index descriptor, or the
physical quantity encoded by the lookup table. Follow-up
[bundle_static_runtime_index5_triangulator_depth_bound_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_triangulator_depth_bound_custody.md)
admits the internal reciprocal ray-depth hypothesis-grid role while leaving
public units and public calibration/LRI/protobuf names open.

## Validation

Commands run:

```text
python3 -m py_compile tools/lldb_probes/codex_lookup_endpoint_count_origin/endpoint_count_origin_probe.py tools/lldb_probes/codex_lookup_endpoint_count_origin/verify_endpoint_count_origin.py
bash tools/lldb_probes/codex_lookup_endpoint_count_origin/run_four_zoom.sh
arch -x86_64 lldb -b -s tools/lldb_probes/codex_lookup_endpoint_count_origin/static_endpoint_count_origin.lldb > runs/codex_lookup_endpoint_count_origin/static_endpoint_count_origin.log
python3 tools/lldb_probes/codex_lookup_endpoint_count_origin/verify_endpoint_count_origin.py
file runs/codex_lookup_endpoint_count_origin/endpoint_count_origin_{28mm,35mm,70mm,150mm}.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' runs/codex_lookup_endpoint_count_origin
```

Verifier output:

The verifier also requires each admitted paired output file to start with the
Radiance HDR magic bytes.

```text
28mm: OK records=5 max_distance=43.855167 first_scalar=1702.676636 scalar_0x18=2.000000 rounded_count=752
35mm: OK records=5 max_distance=43.855167 first_scalar=1702.676636 scalar_0x18=2.000000 rounded_count=752
70mm: OK records=5 max_distance=35.540379 first_scalar=4140.005859 scalar_0x18=2.000000 rounded_count=1472
150mm: OK records=5 max_distance=35.406025 first_scalar=4141.635254 scalar_0x18=2.000000 rounded_count=1472
```
