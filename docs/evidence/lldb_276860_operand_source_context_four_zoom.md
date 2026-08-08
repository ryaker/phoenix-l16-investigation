# LLDB 0x276860 Operand Source Context, Four-Zoom

Status: accepted narrow early-terminate runtime evidence.

## Question

[lldb_276860_xmm4_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm4_origin_four_zoom.md)
proved sampled `%xmm4_low` formation from:

```text
xmm8 - [[rbp-0x208] + rdx]
```

scaled by the target worker object's `+0x60` vector. This follow-up asks where
the two vector operands in that subtraction come from in the same sampled
`0x276860` target-index-5 packet.

This is packet evidence only. The process is intentionally killed after the
selected packet is captured, so the `.hdr` files from this harness are
zero-byte non-evidence files.

## Harness

Probe files:

- `tools/lldb_probes/codex_276860_operand_source_context/operand_source_probe.py`
- `tools/lldb_probes/codex_276860_operand_source_context/operand_source_28mm.lldb`
- `tools/lldb_probes/codex_276860_operand_source_context/operand_source_35mm.lldb`
- `tools/lldb_probes/codex_276860_operand_source_context/operand_source_70mm.lldb`
- `tools/lldb_probes/codex_276860_operand_source_context/operand_source_150mm.lldb`
- `tools/lldb_probes/codex_276860_operand_source_context/run_four_zoom.sh`
- `tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py`

Run:

```bash
bash tools/lldb_probes/codex_276860_operand_source_context/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
```

Raw rerunnable output lives under
`runs/codex_276860_operand_source_context/`.

## Static Window

Static disassembly from `tools/libcp_disasm_intel.txt`:

```text
276a95: mov qword ptr [rbp - 0x208], rax   ; rax from [target+0x1e8]
276afd: mov qword ptr [rbp - 0x210], rax   ; rax from [target+0x198]
276b56: mov qword ptr [rbp - 0x200], rax   ; rax from [target+0x168]
276bad: mov qword ptr [rbp - 0x1c8], rbx   ; target object

26ca94: mov qword ptr [r13 + 0x198], r12
26cbcd: mov qword ptr [r13 + 0x1e8], r15
26cc01: mov qword ptr [r13 + 0x200], rax

2774a2: mov rax, qword ptr [r14 + 0x288]
2774b5: mov rax, qword ptr [rax + 0x20]
2774b9: pmovzxbd xmm0, dword ptr [rax + 4*rcx]
2774bf: cvtdq2ps xmm0, xmm0
2774c9: mov rax, qword ptr [rbp - 0x250]   ; target+0x200 base
2774d0: movaps xmmword ptr [rax + rcx], xmm0

2775d5: movaps xmm8, xmmword ptr [rcx]
27786b: movzx ecx, word ptr [rdi + 2*rcx]
277873: mov rdi, qword ptr [rbp - 0x208]
27787a: subps xmm2, xmmword ptr [rdi + rdx]
```

## Capture Model

The probe uses the same target-index-5 gate as the prior `0x276860` packet
proofs:

- `0x26bbd0`: capture target index `5` and target object.
- after the target object is known, arm write-watchpoints on target fields
  `+0x198`, `+0x1e8`, `+0x200`, and `+0x288`;
- dynamically capture same-object candidate producer stores at `0x26c5e7`,
  `0x26c633`, `0x26ca94`, `0x26cbcd`, and `0x26cc01`;
- `0x26be50`: capture the caller context for that target object.
- `0x29a1a0`: verify the target context reaches the source-local producer
  boundary, then install the operand breakpoints.
- `0x2774bf`: capture the guide bytes immediately after `pmovzxbd`.
- `0x2774d0`: capture the vector written into the target object's `+0x200`
  vector table.
- `0x2775d5`: capture the later `%xmm8` load address and bytes.
- `0x27786b`: after skipping the first four target table hits, capture the
  selected table/subtraction context, correlate it with the latest same-thread
  `%xmm8` load, then kill the process.

The validator requires:

- the table packet's target object equals `[rbp-0x1c8]`;
- `[rbp-0x208] == target+0x1e8`;
- `[rbp-0x210] == target+0x198 == table_base`;
- `%xmm8` at `0x27786b` equals bytes read at the preceding `0x2775d5` load
  address;
- that load address matches a prior `0x2774d0` store into the target `+0x200`
  vector table;
- the `0x2774d0` stored vector equals the `0x2774bf` guide bytes after
  unsigned-byte-to-float conversion.
- final target fields `+0x198`, `+0x1e8`, `+0x200`, and `+0x288` have
  same-object producer custody by either a field write-watchpoint or a matched
  same-object producer breakpoint.
- the static/runtime layout of `+0x198`, `+0x1e8`, and `+0x200` matches the
  `0x26c8e0` formulas checked by the verifier.

## Accepted Results

Validator output:

```text
operand_source_28mm.json: OK xmm8=[168.0, 56.0, 48.0, 1.0] source_vec=[168.0, 56.0, 48.0, 1.0] guide_u8x4=a8383001 table=240 origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} producers=guide_store_0x288_reuse_26c633
operand_source_35mm.json: OK xmm8=[43.0, 118.0, 109.0, 1.0] source_vec=[43.0, 119.0, 108.0, 1.0] guide_u8x4=2b766d01 table=199 origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} producers=guide_store_0x288_reuse_26c633
operand_source_70mm.json: OK xmm8=[95.0, 90.0, 88.0, 1.0] source_vec=[98.0, 90.0, 89.0, 1.0] guide_u8x4=5f5a5801 table=230 origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} producers=guide_store_0x288_reuse_26c633
operand_source_150mm.json: OK xmm8=[177.0, 86.0, 44.0, 1.0] source_vec=[177.0, 84.0, 43.0, 1.0] guide_u8x4=b1562c01 table=202 origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} producers=guide_store_0x288_reuse_26c633
```

The table values and vectors above are packet observations, not stable
constants.

The watchpoint-backed field-origin rows are identical across all four focal
tiers:

| Target field | Runtime producer evidence |
|---|---|
| `+0x198` | write-watchpoint stop after `0x26ca94`, reported at `0x26ca9b`; final field value equals the later table base used at `0x27786b` |
| `+0x1e8` | write-watchpoint stop after `0x26cbcd`, reported at `0x26cbd4`; final field value equals `[rbp-0x208]` and the subtraction-vector base |
| `+0x200` | write-watchpoint stop after `0x26cc01`, reported at `0x26cc08`; final field value equals the `0x2774d0` store base and later `%xmm8` load family |
| `+0x288` | matched same-object producer breakpoint at `0x26c633`; the same store is also observed by the `+0x288` write-watchpoint at `0x26c63a` |

The same validator checks the static/runtime buffer layout of the sampled
packet:

| Layout item | Four-zoom value |
|---|---:|
| Guide descriptor dimensions | `2080 x 1560` |
| Expanded width used by `0x26c8e0` | `2082` |
| `+0x198` table capacity | `16656` `uint16` entries |
| `+0x200 - +0x1e8` | `33312` bytes |
| Sampled subtraction vector offset from `+0x200` | `16` bytes |

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  one target-index-5 packet per focal tier correlates the `%xmm8` operand to a
  preceding same-thread load from the target object's `+0x200` vector table.
- The captured `+0x200` vector-table value is written by the local
  `0x2774b9..0x2774d0` path from four guide bytes read through the target
  object's `+0x288` pointer and converted by unsigned-byte-to-float SIMD
  operations.
- The captured subtraction vector is read through `[rbp-0x208] + rdx`, where
  `[rbp-0x208]` equals target object field `+0x1e8`.
- The paired `uint16` table base at `0x27786b` is `[rbp-0x210]`, which equals
  target object field `+0x198`.
- The final target qwords consumed by that packet have same-object internal
  producer custody: `+0x198` through the `0x26ca94` store, `+0x1e8` through
  the `0x26cbcd` store, `+0x200` through the `0x26cc01` store, and `+0x288`
  through the `0x26c633` store.
- The sampled `+0x198` field is the base of a `16656`-entry `uint16` table for
  this target packet, and the sampled `+0x200` field is an interior pointer
  `33312` bytes into the `+0x1e8` vector buffer; the sampled subtraction vector
  is `16` bytes past that interior pointer.
- This closes a narrow internal operand-custody boundary for the sampled
  `%xmm4` subtraction inputs.

## Not Proven

- Public meaning, public LRI/protobuf origin, or physical name for the
  same-object producer path and target object fields `+0x1e8`, `+0x198`,
  `+0x200`, or `+0x288`.
- Public meaning of the guide bytes, subtraction vectors, table values, or
  target object `+0x60` scale vector.
- Full-map payload distribution, all source records, all lane positions, or
  stability beyond the selected packet per focal tier.
- Whether the sampled operands are final costs, intermediate costs, or one term
  in a later score.
- Final source contribution, anti-ghosting behavior, or acceptance/rejection.

## Validation

Commands run:

```text
python3 -m py_compile tools/lldb_probes/codex_276860_operand_source_context/operand_source_probe.py tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
bash tools/lldb_probes/codex_276860_operand_source_context/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' runs/codex_276860_operand_source_context || true
```

The error scan produced no matches.
