# LLDB Evidence: `0x1f0ce0` K Source Trace, Four Zoom

## Scope

This note refines the Lane B `0x1f0ce0 -> 0xf33d0` producer-edge proof.

**Public-name follow-up (2026-06-19):** embedded `libcp.dylib` protobuf
descriptors now prove that the anonymous public `field_6` used below is
`GeometricCalibration.CalibrationFocusBundle.focus_hall_code`, while runtime
`object+0x54` comes from `LightHeader.modules[].lens_position`. The captured
helper is therefore focus-dependent `intrinsics.k_mat` interpolation or
extrapolation over calibrated focus Hall codes at the live lens position. See
[bundle_static_runtime_index5_public_proto_schema_names.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_public_proto_schema_names.md).
The original probe did not establish those names by itself; its remaining
scope limits still apply.

The narrow question is where the B/C K matrices stop being exact public LRI
fixed32 records. Prior evidence proved that B4/C5 pose records are exact public
copies while B4/C5 K records are zoom-variant non-exact packets at the final
`0xf33d0` producer edge. This probe adds runtime breakpoints inside
`0x1f0ce0` to distinguish the public input K vector, the optional helper output,
the `0xf3350` scale window, and the final two selector-bank calls.

Bottom line: in the captured four-zoom packets, the first usable K vector after
`0x1f0b00` is an exact public LRI K record under the 32,832-byte intrinsics
payload `field_13[camera=N]` for the same camera ID. The helper entry at
`0x1f96e0` receives the same camera's two public K records and two public
`field_6` fixed32 scalar values from that payload. The scalar argument is the
runtime `object+0x54` value returned by `0xf3300`. The helper output copied
through `rbp-0x188 -> rbp-0xb8` equals the verifier-reconstructed float32
linear interpolation/extrapolation of K fields `0`, `2`, `4`, and `5` over
those public `field_6` scalars at `object+0x54`. The `0xf3350` scale fields are
`(1.0, 1.0)` in these runs, so that later window does not explain the B/C K
differences.

This proves the component-scoped K helper formula for the two-record branch
exercised by the captured packets. The companion embedded-schema proof now
names `field_6` as `focus_hall_code` and `object+0x54` as `lens_position`; it
does not name selector `0` / `1` or the other non-K B/C packet fields.

## Artifacts

- Runtime verifier:
  [verify_k_source_trace.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_1f0ce0_k_source_trace/verify_k_source_trace.py)
- Runtime probe:
  [k_source_trace_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_probe.py)
- Four-zoom harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_1f0ce0_k_source_trace/run_four_zoom.sh)
- LLDB scripts:
  `tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_28mm.lldb`,
  `tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_35mm.lldb`,
  `tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_70mm.lldb`,
  `tools/lldb_probes/codex_1f0ce0_k_source_trace/k_source_trace_150mm.lldb`
- Raw runtime reports:
  `runs/codex_1f0ce0_k_source_trace/k_source_trace_28mm.json`,
  `runs/codex_1f0ce0_k_source_trace/k_source_trace_35mm.json`,
  `runs/codex_1f0ce0_k_source_trace/k_source_trace_70mm.json`,
  `runs/codex_1f0ce0_k_source_trace/k_source_trace_150mm.json`
- Preceding producer-edge evidence:
  [lldb_f33d0_1f0ce0_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_f33d0_1f0ce0_producer_four_zoom.md)

## Probe Sites

The harness samples seven sites inside the `0x1f0ce0` producer path:

| Site | Meaning checked by verifier |
|---|---|
| `0x1f0d36` | after `0x1f0b00`; captures vector headers and the first K vector payload |
| `0x1f96e0` | helper entry; captures output/source arguments, `edx`, public K record vector, and public scalar vector |
| `0x1f0ee5` | after the optional helper K copy; captures helper output at `rbp-0x188` and K stack at `rbp-0xb8` |
| `0x1f0fed` | before `0xf3350` scale-field use |
| `0x1f1047` | after `0xf3350` scale-field use |
| `0x1f1328` | final `0xf33d0` selector-`0` call |
| `0x1f134b` | final `0xf33d0` selector-`1` call |

The verifier also reuses the existing static producer-edge byte verifier to
guard the direct calls, selector setup, K / pose / three-int stack-local
arguments, and post-`0xf3350` K-field scale window. It additionally byte-guards
`0xf3300` as the `object+0x54` accessor plus the installed `0x1f96e0`
two-record interpolation windows.

## Verification

Command:

```bash
python3 tools/lldb_probes/codex_1f0ce0_k_source_trace/verify_k_source_trace.py
```

Verifier output:

For packets that report complete render exit, the verifier also requires the
paired output file to start with the Radiance HDR magic bytes.

```text
static_1f0ce0_calls_and_selector_setup=OK
static_1f96e0_two_record_interp=OK
28mm: OK probe_window_complete render_complete=yes keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 public_input=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 formula=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 helper_changed=B1,B2,B3,B4,B5 final_public=A1,A2,A3,A4,A5
35mm: OK probe_window_complete render_complete=yes keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 public_input=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 formula=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 helper_changed=B1,B2,B3,B4,B5 final_public=A1,A2,A3,A4,A5
70mm: OK probe_window_complete render_complete=yes keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 public_input=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 formula=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 helper_changed=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 final_public=none
150mm: OK probe_window_complete render_complete=yes keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 public_input=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 formula=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 helper_changed=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 final_public=none
cross_tier=B4_public_input_stable_formula_variants4,C5_public_input_stable_formula_variants2,A1-A5_wide_formula_preserves_public_K
```

## Verified Facts

For each focal tier, the verifier requires ten hits at each of the seven probe
sites:

| Zoom | Captured keys |
|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |

For every captured key, the first usable K vector after `0x1f0b00` matches a
public fixed32 sequence under:

```text
32832.field_13[camera=N].field_3[0].field_2[0].field_2[0].field_1[0]
```

Some A-bank fixed-camera records also have a second exact public path under
`field_2[1]`; the verifier requires at least the same-camera `field_13`
public path and does not use duplicate paths as separate facts.

For every captured key, the helper entry at `0x1f96e0` is checked against the
same public camera entry:

- `rdi = rbp-0x188`, the helper output copied later to the K stack.
- `rsi = rbp-0x140`, the helper source record.
- `edx = object+0x54`.
- `rsi+0x00` is a two-record vector of public K matrices from
  `32832.field_13[camera=N].field_3.field_2[*].field_2.field_1`.
- `rsi+0x30` is a two-int scalar vector matching public fixed32
  `32832.field_13[camera=N].field_3.field_2[*].field_6`.

The admitted two-record formula is:

```text
sort the two records by scalar field_6
for K fields 0, 2, 4, and 5:
  slope = (K1[field] - K0[field]) / (scalar1 - scalar0)
  intercept = K0[field] - scalar0 * slope
  output[field] = object+0x54 * slope + intercept
copy the remaining K fields from the first public K record
```

The verifier performs that calculation with float32 rounding at the helper's
arithmetic steps, then compares the resulting raw float32 K packet to the
helper output and to both final `0xf33d0` selector-call K arguments.

Representative scalar bindings:

| Zoom | Key | `object+0x54` | public `field_6` values |
|---|---:|---:|---|
| `28mm` | `A1` | `10640` | `8707,9654` |
| `28mm` | `B4` | `1592` | `1766,1675` |
| `35mm` | `B4` | `1566` | `1766,1675` |
| `70mm` | `B4` | `1544` | `1766,1675` |
| `70mm` | `C5` | `1056` | `2082,1566` |
| `150mm` | `B4` | `1562` | `1766,1675` |
| `150mm` | `C5` | `1062` | `2082,1566` |

The helper boundary is component-scoped:

| Zoom | Public K input | Helper changes K for | Final exact-public K |
|---|---|---|---|
| `28mm` | all captured keys | `B1,B2,B3,B4,B5` | `A1,A2,A3,A4,A5` |
| `35mm` | all captured keys | `B1,B2,B3,B4,B5` | `A1,A2,A3,A4,A5` |
| `70mm` | all captured keys | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | none |
| `150mm` | all captured keys | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | none |

For each key, the verifier checks:

- helper output `rbp-0x188` converts to the exact K stack packet at
  `rbp-0xb8`;
- the pre-`0xf3350` K stack equals the helper output;
- `object+0x124` and `object+0x128` are `1.0`, and the post-`0xf3350` K stack
  equals the pre-`0xf3350` K stack;
- selector `0` and selector `1` both receive `rsi = rbp-0xb8`,
  `rdx = rbp-0x278`, and `rcx = rbp-0x288`;
- the K stack at both final selector-call sites equals the post-scale K stack.

Cross-tier formula checks add:

- B4 public input K is stable across all four focal tiers, while B4
  formula/helper/final K has four variants driven by per-tier `object+0x54`.
- C5 public input K is stable across the tele tiers, while C5 helper/final K
  has two variants driven by per-tier `object+0x54`.
- A1-A5 formula/helper/final K preserves the public wide input K across `28mm`
  and `35mm`, because the paired public K records are identical even when
  `object+0x54` is outside the public scalar interval.

## Consequence

The B/C K public-meaning gap is no longer between the public LRI calibration
payload and the entry to `0x1f0ce0`: the runtime input K vector is a public
same-camera intrinsics record. It is also no longer an undecoded K-helper
numeric gap for the exercised branch: the helper output is the public
two-record K formula evaluated over public `field_6` values at runtime
`object+0x54`.

The remaining public-meaning gap is coverage beyond this focus-dependent K
formula. Companion schema proof names `field_6` as `focus_hall_code` and
`object+0x54` as `lens_position`; a superseding writer-census/two-body-watch
proof now names selector `0=factory` and selector `1=current`. Complete
bank-field semantics and the other B/C source-record fields feeding the wider
pair-grid / index-5 path remain open.

## Non-Claims

- This runtime probe alone did not name `field_6` or `object+0x54`; the
  companion embedded-schema proof now does.
- This does not prove branches of `0x1f96e0` other than the captured two-record
  K helper branch.
- This does not assign public protobuf field names to the transformed B/C K
  outputs beyond the component-scoped K fields and raw public carrier paths
  proven here.
- This does not name selector `0` or selector `1` as public `factory` /
  `current` semantics.
- This does not close full `state+0xe0` contents or `state+0x448` payload
  semantics.
- This does not close tele C6.
- This does not prove public origin or physical meaning for the index-5
  `0x299c70 -> 0x267010` source/lookup descriptors.
- This does not upgrade the Lane B blocker to closed.

## Safe Statement

For the captured four-zoom `0x1f0ce0` packets, public same-camera
`intrinsics.k_mat` records enter the producer from the LRI geometry payload;
the helper receives two per-focus K records plus their calibrated
`focus_hall_code` scalars, and live `lens_position` selects the scalar point.
The captured branch linearly interpolates/extrapolates K fields `0`, `2`, `4`,
and `5` with float32 arithmetic; A-bank wide K packets remain unchanged because
their paired public K records are identical; B/C K packets become zoom-specific
through the helper output before `0xf3350`; the tested `0xf3350` scale window is
identity; and both final `0xf33d0` selector calls receive the same result.
