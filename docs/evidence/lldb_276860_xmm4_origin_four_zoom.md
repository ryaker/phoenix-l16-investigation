# LLDB 0x276860 XMM4 Origin Proof, Four-Zoom

Status: accepted narrow early-terminate runtime evidence.

## Question

[lldb_276860_xmm3_term_step_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm3_term_step_four_zoom.md)
validates one non-degenerate `%xmm3` pre-add term per focal tier from
`%xmm4_low`, `u16[object+0x56]`, and `f32[object+0x58]`. This probe follows
the previously unresolved local producer by asking whether the preceding
SIMD/scalar window at `0x27786f..0x277903` reconstructs the captured
`%xmm4_low` values exactly.

This is packet evidence only. The process is intentionally killed after the
stepped packet is captured, so the `.hdr` outputs from this harness are
zero-byte non-evidence files.

## Harness

Probe files:

- `tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_probe.py`
- `tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_28mm.lldb`
- `tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_35mm.lldb`
- `tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_70mm.lldb`
- `tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_150mm.lldb`
- `tools/lldb_probes/codex_276860_xmm4_origin/run_four_zoom.sh`
- `tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py`

Run:

```bash
bash tools/lldb_probes/codex_276860_xmm4_origin/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py
```

Raw rerunnable output lives under `runs/codex_276860_xmm4_origin/`.

## Static Window

Static disassembly from `tools/libcp_disasm_intel.txt`:

```text
27786f: movaps xmm2, xmm8
277873: mov rdi, qword ptr [rbp - 0x208]
27787a: subps xmm2, xmmword ptr [rdi + rdx]
27787e: mov rdi, qword ptr [rbp - 0x1c8]
277885: mulps xmm2, xmmword ptr [rdi + 0x60]
277889: andps xmm2, xmm10
27788d: blendps xmm2, xmm11, 0x8
277894: movaps xmm3, xmm2
277897: shufpd xmm3, xmm3, 0x1
27789c: addps xmm3, xmm2
27789f: movaps xmm2, xmm3
2778a2: shufps xmm2, xmm2, 0xb1
2778a6: addps xmm2, xmm3
2778a9: xorps xmm2, xmm12
2778ad: shufps xmm2, xmm2, 0x0
2778b1: minss xmm2, xmm13
2778b6: maxss xmm2, xmm14
2778bb: cvttps2dq xmm3, xmm2
2778bf: movaps xmm4, xmm2
2778c2: psrad xmm4, 0x1f
2778c7: paddd xmm4, xmm3
2778cb: cvtdq2ps xmm3, xmm4
2778ce: subss xmm2, xmm3
2778d2: movaps xmm3, xmm2
2778d5: mulss xmm3, xmm15
2778da: addss xmm3, dword ptr [rip + 0x36354e]  ; 0x5dae30
2778e2: mulss xmm3, xmm2
2778e6: addss xmm3, dword ptr [rip + 0x363546]  ; 0x5dae34
2778ee: mulss xmm3, xmm2
2778f2: addss xmm3, dword ptr [rip + 0x36353e]  ; 0x5dae38
2778fa: pslld xmm4, 0x17
2778ff: paddd xmm4, xmm3
277903: movzx edx, word ptr [rdi + 0x56]
```

## Capture Model

The probe uses the same target-index-5 gate as the scalar-origin and `%xmm3`
term proofs:

- `0x26bbd0`: capture target index `5` and target object.
- `0x26be50`: capture the caller context for that object.
- `0x29a1a0`: verify the target context reaches the source-local producer
  boundary, then install the table breakpoint.
- `0x27786b`: after skipping the first four target table hits, capture the
  table setup, `xmm8`, `xmm10..xmm15`, `[rbp-0x208] + rdx`, `object+0x60`,
  and polynomial constants at `0x5dae30..0x5dae38`.
- Single-step the selected thread through `0x277903`, capturing the
  post-instruction states listed in the validator.

The validator requires the same thread, same `rbp`, same `r9`, same tracked
object, no LLDB errors, and no step cap.

## Validated Formula

For each admitted packet, the verifier reconstructs:

```text
v0 = f32x4(xmm8) - f32x4([[rbp-0x208] + rdx])
v1 = v0 * f32x4([object+0x60])
v2 = bit_and(v1, xmm10)
v2[3] = xmm11[3]
sum = horizontal_sum(v2) using the observed shufpd/shufps sequence
signed = xor_sign_bits(sum, xmm12)
scalar = clamp_signed_low_lane(signed, xmm13.low, xmm14.low)
n = cvtt_i32(scalar) + signmask_i32(scalar)
frac = scalar - f32(n)
poly = (((frac * xmm15.low + C1) * frac + C2) * frac + C3)
xmm4_low_bits = (n << 23) + bits(poly)
```

The constants captured from the installed binary are:

```text
C1 = 0.2260671556
C2 = 0.6958335638
C3 = 0.9999251962
xmm15.low = 0.078025 approximately
```

The verifier checks exact register bytes after every captured stage through the
vector arithmetic and checks the final `%xmm4` low lane bits at `0x277903`. It
also scans the four canonical LRI payload streams for the exact `object+0x60`
16-byte vector and for each nonzero 4-byte scalar word in that vector.

## Accepted Results

| Tier | JSON | Clamped scalar | Sign-adjusted int | Fraction | `xmm4_low` |
|---|---|---:|---:|---:|---:|
| `28mm` | `runs/codex_276860_xmm4_origin/xmm4_origin_28mm.json` | `-0.000000` | `-1` | `1.000000` | `0.999925256` |
| `35mm` | `runs/codex_276860_xmm4_origin/xmm4_origin_35mm.json` | `-0.060112` | `-1` | `0.939888` | `0.959209323` |
| `70mm` | `runs/codex_276860_xmm4_origin/xmm4_origin_70mm.json` | `-0.270505` | `-1` | `0.729495` | `0.829063177` |
| `150mm` | `runs/codex_276860_xmm4_origin/xmm4_origin_150mm.json` | `-0.090168` | `-1` | `0.909832` | `0.939458907` |

Validator output:

```text
xmm4_origin_28mm.json: OK table=240 clamped=-0.000000 floor=-1 fraction=1.000000 xmm4_low=0.999925256 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_35mm.json: OK table=199 clamped=-0.060112 floor=-1 fraction=0.939888 xmm4_low=0.959209323 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_70mm.json: OK table=225 clamped=-0.270505 floor=-1 fraction=0.729495 xmm4_low=0.829063177 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_150mm.json: OK table=215 clamped=-0.090168 floor=-1 fraction=0.909832 xmm4_low=0.939458907 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
```

The table values above are packet observations, not stable constants. The
validated `%xmm4_low` values match the prior `%xmm3` term proof's captured
`%xmm4_low` values.

The captured `object+0x60` scale vector is the same in all four admitted
packets:

```text
8a25a43d 4f38f63c 4f38f63c 00000000
= [0.080149725, 0.030056147, 0.030056147, 0.0]
```

The validator finds zero exact full-vector LRI payload hits and zero exact
nonzero scalar-word LRI payload hits for that vector. This is only an exact
byte/scalar absence check; it does not exclude a computed, transformed,
rounded, or differently encoded public origin.

Follow-up
[lldb_276860_operand_source_context_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_operand_source_context_four_zoom.md)
binds the sampled subtraction operands to immediate target-object fields:
`%xmm8` comes through target `+0x200` after a local guide-byte conversion from
target `+0x288`, `[rbp-0x208]` is target `+0x1e8`, and `[rbp-0x210]` is target
`+0x198`. That follow-up is internal custody only, not public naming.

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  one stepped target-index-5 packet per focal tier reconstructs `%xmm4_low`
  exactly from the preceding local `0x27786f..0x277903` arithmetic.
- The captured `%xmm4` producer reads a 4-float vector through `[rbp-0x208] +
  rdx`, subtracts it from `%xmm8`, scales by `object+0x60`, applies the
  observed masks/blend/sign/clamp sequence, then assembles the low-lane result
  through a polynomial plus exponent-bit step.
- The sampled `object+0x60` scale vector has zero exact full-vector and zero
  exact nonzero scalar-word hits in the canonical LRI payload streams.
- This closes the narrow internal formation boundary for the `%xmm4` operand
  used by the sampled `%xmm3` pre-add term.

## Not Proven

- Public meaning, public LRI/protobuf origin, or physical name for `%xmm8`,
  `[rbp-0x208] + rdx`, `object+0x60`, or the resulting `%xmm4`.
- Public meaning or public LRI/protobuf origin of `object+0x56`,
  `object+0x58`, the table at `rbp-0x210`, or the source-record payload costs.
- Full-map payload distribution, all source records, all lane positions, or
  stability beyond the single stepped packet per focal tier.
- Whether these sampled operands are final costs, intermediate costs, or one
  term in a later score.
- Final source contribution, anti-ghosting behavior, or acceptance/rejection.
