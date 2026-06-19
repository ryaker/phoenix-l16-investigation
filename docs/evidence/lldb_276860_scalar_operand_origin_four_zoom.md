# LLDB 0x276860 Scalar Operand Origin, Four-Zoom

Status: accepted narrow early-terminate runtime evidence.

## Question

`lldb_276860_payload_vector_formula_four_zoom.md` proves the sampled
`0x2779b0..0x277a10` unsigned-16 SIMD recurrence and leaves the immediate
`%xmm2` / `%xmm3` scalar setup as an open local input boundary. This probe asks
whether the sampled setup immediately before that SIMD loop can be paired and
validated under the same target-index-5 `0x276860` path across the canonical
four focal tiers.

This is packet evidence only. The process is intentionally killed after the
sample cap is reached, so the `.hdr` outputs from this harness are zero-byte
non-evidence files.

## Harness

Probe files:

- `tools/lldb_probes/codex_276860_scalar_operand_origin/scalar_origin_probe.py`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/scalar_origin_28mm.lldb`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/scalar_origin_35mm.lldb`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/scalar_origin_70mm.lldb`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/scalar_origin_150mm.lldb`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/run_four_zoom.sh`
- `tools/lldb_probes/codex_276860_scalar_operand_origin/validate_scalar_origin.py`

Run:

```bash
bash tools/lldb_probes/codex_276860_scalar_operand_origin/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_scalar_operand_origin/validate_scalar_origin.py
```

Raw rerunnable output lives under
`runs/codex_276860_scalar_operand_origin/`.

## Static Window

Static disassembly from `tools/libcp_disasm_intel.txt`:

```text
277864: mov rdi, qword ptr [rbp - 0x210]
27786b: movzx ecx, word ptr [rdi + 2*rcx]
27786f: movaps xmm2, xmm8
277873: mov rdi, qword ptr [rbp - 0x208]
27787a: subps xmm2, xmmword ptr [rdi + rdx]
27787e: mov rdi, qword ptr [rbp - 0x1c8]
277885: mulps xmm2, xmmword ptr [rdi + 0x60]
...
277903: movzx edx, word ptr [rdi + 0x56]
27790a: cvtsi2ss xmm2, edx
27790e: mulss xmm2, dword ptr [rdi + 0x58]
277913: mulss xmm2, xmm4
277917: cvttss2si edx, xmm2
27791b: add edx, ecx
27791d: movd xmm2, ecx
...
27792f: movd xmm3, edx
277939: pshufb xmm2, xmm9
27793f: pshufb xmm3, xmm9
277945: mov rcx, qword ptr [rbp - 0x150]
```

## Capture Model

The probe gates through the same target-index path used by the vector formula
custody proof:

- `0x26bbd0`: capture target index `5` and target object.
- `0x26be50`: capture the caller context for that object.
- `0x29a1a0`: verify the target context reaches the source-local producer
  boundary, then install the scalar setup breakpoints.
- `0x27786b`: capture the table-load setup immediately before the `movzx`.
- `0x27791d`: capture the scalar values immediately before `movd xmm2, ecx`.
- `0x277945`: capture final `%xmm2` / `%xmm3` bytes immediately after both
  `pshufb` instructions and before the SIMD recurrence setup continues.

The validator accepts only paired `0x27786b -> 0x27791d -> 0x277945` samples
with the same thread, same `rbp`, same `r9`, same tracked object, no LLDB
errors, and no drive step cap.

## Accepted Results

| Tier | JSON | Process | Paired samples |
|---|---|---|---:|
| `28mm` | `runs/codex_276860_scalar_operand_origin/scalar_origin_28mm.json` | killed after capture | `8` |
| `35mm` | `runs/codex_276860_scalar_operand_origin/scalar_origin_35mm.json` | killed after capture | `8` |
| `70mm` | `runs/codex_276860_scalar_operand_origin/scalar_origin_70mm.json` | killed after capture | `8` |
| `150mm` | `runs/codex_276860_scalar_operand_origin/scalar_origin_150mm.json` | killed after capture | `8` |

Validator output:

```text
scalar_origin_28mm.json: OK paired_samples=8 terminated_after_capture=True
scalar_origin_35mm.json: OK paired_samples=8 terminated_after_capture=True
scalar_origin_70mm.json: OK paired_samples=8 terminated_after_capture=True
scalar_origin_150mm.json: OK paired_samples=8 terminated_after_capture=True
```

## Validated Relationships

For every admitted paired packet:

- The `0x27786b` packet proves `rdi == qword [rbp-0x210]` and records the
  `uint16` table value at `rdi + 2*rcx`.
- The paired `0x27791d` packet proves the later `ecx` feeding `movd xmm2, ecx`
  equals that captured `uint16` table value.
- The paired `0x27791d` packet records the live `edx` feeding
  `movd xmm3, edx` after the local static `add edx, ecx` instruction.
- The paired `0x277945` packet proves the prepared `%xmm2` bytes decode as
  eight identical unsigned-16 lanes equal to the paired `ecx & 0xffff`.
- The paired `0x277945` packet proves the prepared `%xmm3` bytes decode as
  eight identical unsigned-16 lanes equal to the paired `edx & 0xffff`.
- The paired target stack context proves `qword [rbp-0x1c8]` equals the tracked
  target object.
- The paired `r9` value resolves through the tracked object's
  `object+0x108` record base and `object+0x138` offset table.

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  sampled target-index-5 packets bound the immediate `%xmm2` setup before the
  admitted `0x2779b0..0x277a10` SIMD recurrence to a `uint16` lookup from the
  table pointer stored at `rbp-0x210`.
- Across the same sampled packets, the immediate `%xmm3` setup before that SIMD
  recurrence is bounded to the live post-add `edx` scalar captured immediately
  before `movd xmm3, edx`.
- The sampled broadcast-ready `%xmm2` and `%xmm3` register contents at
  `0x277945` match those paired immediate scalar values.
- The sampled packets remain tied to the same tracked object and source-local
  record table context admitted by the preceding vector formula custody proof.

## Not Proven

- Public meaning or public LRI/protobuf origin for the table at `rbp-0x210`,
  the `ecx` lookup index, or the `edx` post-add scalar.
- The follow-up `lldb_276860_xmm3_term_step_four_zoom.md` validates one
  non-degenerate sampled `%xmm3` pre-add term per focal tier from captured
  `%xmm4`. The later
  [lldb_276860_xmm4_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm4_origin_four_zoom.md)
  proof closes sampled internal `%xmm4` formation, but not public meaning or
  public LRI/protobuf origin.
- Full-map payload distribution, all records, all lane positions, or stability
  beyond the sampled target-index-5 packets.
- Whether these sampled scalar operands are final costs, intermediate costs, or
  one term in a later score.
- Final source contribution, anti-ghosting behavior, or acceptance/rejection.
