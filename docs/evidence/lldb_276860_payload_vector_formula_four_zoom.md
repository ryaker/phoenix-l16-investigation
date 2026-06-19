# LLDB 0x276860 Payload Vector Formula, Four-Zoom

Status: accepted narrow runtime/static evidence.

## Question

`lldb_source_record_payload_watch_four_zoom.md` proves sampled source-record
payload bytes at `record+0x08` are mutated by the `libcp+0x277a10` SIMD store
inside the `0x276860` mode-8 `StereoLayer<false>::runPass` body. This probe asks
whether the sampled SIMD increment feeding that store can be reconstructed from
the live vector operands at the same watchpoint stops, and whether a narrow
internal custody boundary can be proven for the stable object fields feeding the
sampled destination and `%xmm1` operand.

## Harness

Probe files:

- `tools/lldb_probes/codex_276860_payload_vector_formula/vector_formula_probe.py`
- `tools/lldb_probes/codex_276860_payload_vector_formula/vector_formula_28mm.lldb`
- `tools/lldb_probes/codex_276860_payload_vector_formula/vector_formula_35mm.lldb`
- `tools/lldb_probes/codex_276860_payload_vector_formula/vector_formula_70mm.lldb`
- `tools/lldb_probes/codex_276860_payload_vector_formula/vector_formula_150mm.lldb`
- `tools/lldb_probes/codex_276860_payload_vector_formula/run_four_zoom.sh`
- `tools/lldb_probes/codex_276860_payload_vector_formula/validate_vector_formula.py`

Run:

```bash
bash tools/lldb_probes/codex_276860_payload_vector_formula/run_four_zoom.sh
python3 tools/lldb_probes/codex_276860_payload_vector_formula/validate_vector_formula.py
file runs/codex_276860_payload_vector_formula/vector_formula_*.hdr
rg -n "Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV" runs/codex_276860_payload_vector_formula/vector_formula_*.json
```

The final `rg` command produced no matches for the admitted packets.

## Static Window

Static disassembly from `tools/libcp_disasm_intel.txt`:

```text
2779b0: lea eax, [rbx + rdx]
2779b3: cdqe
2779b5: movdqu xmm0, xmmword ptr [rsi + 2*rax]
2779ba: movdqu xmm6, xmmword ptr [rdi + 2*rdx]
2779bf: movdqa xmm7, xmm6
2779c3: pslldq xmm7, 0x2
2779c8: movdqa xmm5, xmm0
2779cc: psrld xmm5, 0x10
2779d1: pblendw xmm5, xmm7, 0xfe
2779d7: paddusw xmm0, xmm1
2779db: pminuw xmm0, xmm5
2779e0: paddusw xmm6, xmm1
2779e4: pminuw xmm6, xmm0
2779e9: pminuw xmm6, xmm3
2779ee: movdqu xmm0, xmmword ptr [r10 + 2*rdx]
2779f4: paddusw xmm0, xmm6
2779f8: psubusw xmm0, xmm2
2779fc: movdqu xmmword ptr [rcx + 2*rdx], xmm0
277a01: pminuw xmm4, xmm0
277a06: movdqu xmm5, xmmword ptr [r9 + 2*rdx]
277a0c: paddusw xmm5, xmm0
277a10: movdqu xmmword ptr [r9 + 2*rdx], xmm5
277a16: add rdx, 0x8
```

## Validated Formula

The validator treats all vectors as eight unsigned 16-bit lanes in memory order.
For each sampled stop at `libcp+0x277a16`, it reads the live memory operands and
the live `%xmm0..%xmm7` registers.

```text
src0  = u16x8([rsi + 2*rax])
src6  = u16x8([rdi + 2*rdx])
accum = u16x8([r10 + 2*rdx])
bias1 = u16x8(xmm1)
bias2 = u16x8(xmm2)
cap   = u16x8(xmm3)

blend = [src0[1], src6[0], src6[1], src6[2],
         src6[3], src6[4], src6[5], src6[6]]

v0        = min_u16(sat_add_u16(src0, bias1), blend)
v6        = min_u16(min_u16(sat_add_u16(src6, bias1), v0), cap)
increment = sat_sub_u16(sat_add_u16(accum, v6), bias2)

[rcx + 2*rdx] = increment
[r9 + 2*rdx]  = sat_add_u16(previous_payload, increment)
```

Important scope guard: the hardware watchpoint covers 8 bytes while the SIMD
stores cover 16 bytes. The validator therefore proves full 16-byte increment
formula and full 16-byte side-store/payload-store register agreement, but it
only validates prior-payload accumulation on the watched lanes whose previous
bytes are actually observed by the watchpoint.

## Validated Operand / Destination Custody

The accepted rerun also captures an `origin_context` packet for every sampled
watchpoint stop. The validator now requires all of these relationships:

- `rbp-0x1c8` equals the tracked target object captured at the index setter.
- `object+0x108` equals the output source-local record base observed after
  `0x299fd0`.
- `object+0x138` equals the output source-local offset table observed after
  `0x299fd0`.
- `object+0x130` equals the output source-local descriptor stride.
- The sampled payload destination satisfies
  `r9 == object+0x108 + sampled_record_offset + 8`, and the watched address
  equals `r9 + 2*rdx`.
- `r10` equals the temporary accumulator pointer saved at `rbp-0x2e0`.
- `rbp-0x200` equals `object+0x168`, and `rbp-0x210` equals `object+0x198`.
- `%xmm1` is the eight-lane unsigned-16 broadcast of `object+0x56`.

Two other inspected stack copies, `rbp-0x1d0` and `rbp-0x188`, matched their
static object-field origins in early samples but not all later watchpoint
samples, consistent with those locals being overwritten before some stops. They
are therefore not admitted as stable operand-origin facts.

## Accepted Results

| Tier | JSON | Process | Watch hits | Samples |
|---|---|---|---:|---:|
| `28mm` | `runs/codex_276860_payload_vector_formula/vector_formula_28mm.json` | exited `0` | `wp1=12`, `wp2=4` | `16` |
| `35mm` | `runs/codex_276860_payload_vector_formula/vector_formula_35mm.json` | exited `0` | `wp1=12`, `wp2=8` | `20` |
| `70mm` | `runs/codex_276860_payload_vector_formula/vector_formula_70mm.json` | exited `0` | `wp1=12`, `wp2=3` | `15` |
| `150mm` | `runs/codex_276860_payload_vector_formula/vector_formula_150mm.json` | exited `0` | `wp1=12`, `wp2=4` | `16` |

Validator output:

```text
vector_formula_28mm.json: OK samples=16 watch_hits={'1': 12, '2': 4} vector_formula=0x2779b0..0x277a10
vector_formula_35mm.json: OK samples=20 watch_hits={'1': 12, '2': 8} vector_formula=0x2779b0..0x277a10
vector_formula_70mm.json: OK samples=15 watch_hits={'1': 12, '2': 3} vector_formula=0x2779b0..0x277a10
vector_formula_150mm.json: OK samples=16 watch_hits={'1': 12, '2': 4} vector_formula=0x2779b0..0x277a10
```

All four output files are Radiance HDR files.

The watch-hit and sample totals above are accepted-packet counts from this run,
not stable algorithm constants.

## Rejected Development Runs

During probe development, one `70mm` attempt hit the known instrumentation
`EXC_BAD_ACCESS` race at `libcp+0x2e945d`, and capped batch attempts produced
non-exited `70mm` packets. Those packets are not admitted. The accepted `70mm`
packet above is a clean single-tier rerun with process exit `0`, no driver cap,
and a Radiance HDR output.

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  sampled stops at `libcp+0x277a16` validate the static SIMD increment formula
  for the live vectors feeding `libcp+0x277a10`.
- The computed `increment` exactly matches live `%xmm0` and the full 16-byte
  side-store at `[rcx + 2*rdx]`.
- The full 16-byte payload store at `[r9 + 2*rdx]` exactly matches live `%xmm5`.
- For watched lanes with known previous bytes, the payload update is unsigned
  saturating addition of the previous watched payload lanes plus `increment`.
- The sampled payload destination is internally tied to the tracked object's
  record base at `object+0x108` plus the sampled `0x299fd0` record offset.
- The sampled `%xmm1` operand is the unsigned-16 broadcast of `object+0x56`.
- The sampled accumulator source pointer in `r10` is the temporary pointer saved
  at `rbp-0x2e0`.

## Not Proven

- Public meaning or public LRI/protobuf origin for `src0`, `src6`, `accum`,
  `bias1`, `bias2`, `cap`, or the payload records.
- Public meaning for object fields `+0x56`, `+0x108`, `+0x130`, `+0x138`,
  `+0x168`, `+0x198`, or the `rbp-0x2e0` temporary pointer.
- Immediate sampled scalar setup for `%xmm2` / `%xmm3` is handled by the
  follow-up `lldb_276860_scalar_operand_origin_four_zoom.md` packet proof. That
  follow-up plus `lldb_276860_xmm3_term_step_four_zoom.md` and
  `lldb_276860_xmm4_origin_four_zoom.md` still does not prove public operand
  meaning/origin or full-map distribution.
- Full-map payload distribution or all records/lane positions.
- Prior-payload arithmetic for unwatched lanes in the same 16-byte SIMD store.
- Whether the sampled payload values are final costs, intermediate accumulated
  costs, or one term in a later score.
- Final source contribution, anti-ghosting behavior, or acceptance/rejection.
