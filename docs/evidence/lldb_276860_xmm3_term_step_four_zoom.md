# LLDB 0x276860 XMM3 Term Step Proof, Four-Zoom

Status: accepted narrow early-terminate runtime evidence.

## Question

`lldb_276860_scalar_operand_origin_four_zoom.md` proves the immediate sampled
`%xmm2` / `%xmm3` scalar setup before the `0x2779b0..0x277a10` SIMD recurrence,
but it only records live post-add `edx` for `%xmm3`. This probe asks whether a
non-degenerate sampled `edx` term can be reconstructed from the immediately
preceding local arithmetic:

```text
edx_preadd = cvttss2si(float(u16[object+0x56]) * f32[object+0x58] * xmm4_low)
edx_postadd = edx_preadd + table_value
```

This is packet evidence only. The process is intentionally killed after the
stepped packet is captured, so the `.hdr` outputs from this harness are
zero-byte non-evidence files.

## Harness

Probe files:

- `tools/lldb_probes/codex_276860_xmm3_term_step/xmm3_term_step_probe.py`
- `tools/lldb_probes/codex_276860_xmm3_term_step/xmm3_term_step_28mm.lldb`
- `tools/lldb_probes/codex_276860_xmm3_term_step/xmm3_term_step_35mm.lldb`
- `tools/lldb_probes/codex_276860_xmm3_term_step/xmm3_term_step_70mm.lldb`
- `tools/lldb_probes/codex_276860_xmm3_term_step/xmm3_term_step_150mm.lldb`
- `tools/lldb_probes/codex_276860_xmm3_term_step/run_four_zoom.sh`
- `tools/lldb_probes/codex_276860_xmm3_term_step/validate_xmm3_term_step.py`

Run:

```bash
bash tools/lldb_probes/codex_276860_xmm3_term_step/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_xmm3_term_step/validate_xmm3_term_step.py
```

Raw rerunnable output lives under `runs/codex_276860_xmm3_term_step/`.

## Capture Model

The probe uses the same target-index-5 gate as the scalar-origin proof, then
skips the first four target table hits and stops at the fifth `0x27786b` table
hit. This targets the first non-degenerate packet observed in the scalar-origin
run, where `edx - ecx` is nonzero on all four focal tiers.

After stopping at `0x27786b`, the probe single-steps the selected thread and
captures:

- `0x27786b`: table-load setup before `movzx ecx, word ptr [rdi + 2*rcx]`.
- `0x277903`: completed `%xmm4` low lane immediately before `movzx edx, word ptr [rdi+0x56]`.
- `0x277917`: `%xmm2` low lane after multiplying `u16[object+0x56]`,
  `f32[object+0x58]`, and captured `%xmm4`.
- `0x27791b`: integer `edx` after `cvttss2si edx, xmm2` and before `add edx, ecx`.
- `0x27791d`: post-add `edx` before `movd xmm3, edx`.
- `0x277945`: broadcast-ready `%xmm2` / `%xmm3` after both `pshufb` instructions.

The validator requires one stepped nonzero pre-add packet per focal tier, same
thread, same `rbp`, same `r9`, same tracked object, no LLDB errors, and no step
cap.

## Validated Formula

For each admitted packet:

```text
table     = u16[[rbp-0x210] + 2*idx]
xmm4_low  = low f32 lane of xmm4 at 0x277903
scale     = f32(u16[object+0x56]) * f32[object+0x58]
product   = f32(scale * xmm4_low)
preadd    = trunc_i32(product)
postadd   = (preadd + table) mod 2^32
xmm2      = broadcast_u16(table)
xmm3      = broadcast_u16(postadd)
```

The validator performs the float operations with explicit single-precision
rounding at the checked multiplication boundary and requires the captured
`product`, `preadd`, `postadd`, `%xmm2`, and `%xmm3` values to match.

## Accepted Results

| Tier | JSON | Table | `xmm4_low` | Product | Pre-add | Post-add |
|---|---|---:|---:|---:|---:|---:|
| `28mm` | `runs/codex_276860_xmm3_term_step/xmm3_term_step_28mm.json` | `240` | `0.999925256` | `499.962616` | `499` | `739` |
| `35mm` | `runs/codex_276860_xmm3_term_step/xmm3_term_step_35mm.json` | `199` | `0.959209323` | `479.604675` | `479` | `678` |
| `70mm` | `runs/codex_276860_xmm3_term_step/xmm3_term_step_70mm.json` | `229` | `0.829063177` | `414.531586` | `414` | `643` |
| `150mm` | `runs/codex_276860_xmm3_term_step/xmm3_term_step_150mm.json` | `185` | `0.939458907` | `469.729462` | `469` | `654` |

Validator output:

```text
xmm3_term_step_28mm.json: OK stepped_sites=5 trace_steps=53
xmm3_term_step_35mm.json: OK stepped_sites=5 trace_steps=53
xmm3_term_step_70mm.json: OK stepped_sites=5 trace_steps=53
xmm3_term_step_150mm.json: OK stepped_sites=5 trace_steps=53
```

The numeric rows above are sampled packet observations, not stable constants.

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  one non-degenerate target-index-5 packet per focal tier validates the local
  `%xmm3` pre-add integer term from captured `%xmm4_low`,
  `u16[object+0x56]`, and `f32[object+0x58]`.
- The sampled post-add scalar feeding `movd xmm3, edx` equals the validated
  pre-add integer plus the paired table value from `rbp-0x210`.
- The sampled broadcast-ready `%xmm3` bytes at `0x277945` match the validated
  post-add scalar's low unsigned-16 value.
- The sampled broadcast-ready `%xmm2` bytes at `0x277945` still match the
  paired table value's low unsigned-16 value.

## Not Proven

- Public meaning or public LRI/protobuf origin of the captured `%xmm4` value.
  The later
  [lldb_276860_xmm4_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm4_origin_four_zoom.md)
  proof closes sampled internal `%xmm4` formation only.
- Public meaning or public LRI/protobuf origin of `object+0x56`,
  `object+0x58`, the table at `rbp-0x210`, or the table index.
- Full-map payload distribution, all records, all lane positions, or stability
  beyond the single stepped non-degenerate packet per focal tier.
- Whether these sampled scalar operands are final costs, intermediate costs, or
  one term in a later score.
- Final source contribution, anti-ghosting behavior, or acceptance/rejection.
