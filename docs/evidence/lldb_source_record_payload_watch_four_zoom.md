# LLDB Source-Record Payload Watch, Four-Zoom

Status: accepted narrow runtime/static evidence.

## Question

The existing `0x299c70 -> 0x29a670` worker proof shows the source descriptor is
computed from per-pixel records:

```text
record = record_base + u32(offset_table + 4 * (x + y * stride))
base   = u16(record + 0x00)
count  = u16(record + 0x02)
step   = u16(record + 0x04)
costs  = u16[count] at record + 0x08
output = base + step * first_min_index(costs)
```

`0x299fd0` creates the source-local record layout with zeroed sampled payload
bytes. This probe asks which later instruction first mutates sampled payload
bytes at `record+0x08`.

## Harness

Probe files:

- `tools/lldb_probes/codex_source_record_payload_watch/payload_watch_probe.py`
- `tools/lldb_probes/codex_source_record_payload_watch/payload_watch_28mm.lldb`
- `tools/lldb_probes/codex_source_record_payload_watch/payload_watch_35mm.lldb`
- `tools/lldb_probes/codex_source_record_payload_watch/payload_watch_70mm.lldb`
- `tools/lldb_probes/codex_source_record_payload_watch/payload_watch_150mm.lldb`
- `tools/lldb_probes/codex_source_record_payload_watch/run_four_zoom.sh`
- `tools/lldb_probes/codex_source_record_payload_watch/validate_payload_watch.py`

Run:

```bash
bash tools/lldb_probes/codex_source_record_payload_watch/run_four_zoom.sh
python3 tools/lldb_probes/codex_source_record_payload_watch/validate_payload_watch.py
file runs/codex_source_record_payload_watch/payload_watch_*.hdr
rg -n "Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV" runs/codex_source_record_payload_watch/payload_watch_*.json
```

The final `rg` command produced no matches for the admitted run.

## Runtime Method

For the tracked `StereoLayer<false>` index `5` source object:

1. Break at `0x26bbd0` to capture the index-5 object.
2. Break at `0x26be50` to capture the caller frame for `0x29a140`.
3. Break at `0x29a1a0`, immediately after `0x299fd0` has returned.
4. Read the source-local record base and offset table from the output local.
5. Arm hardware write-watchpoints on the first 8 payload bytes at
   `record+0x08` for the first two records.
6. Record watchpoint stop PCs, stacks, registers, watched bytes, and whether
   the watched address matches the `r9 + 2*rdx` store or the nearby
   `rcx + 2*rdx` store.

The watchpoints were armed only after the sampled payload bytes were observed
as zero.

## Accepted Results

| Tier | LRI | Target counts | Watch hits | Watchpoint records |
|---|---|---:|---:|---|
| `28mm` | `2018-07-23/L16_02130.lri` | `caller_pre_29a140=1`, `maker_after_299fd0=1`, `later_299c70_entry=1` | `wp1=12`, `wp2=4` | record `0` offset `0`, header `[205,9,1,16]`; record `1` offset `56`, header `[205,9,1,16]` |
| `35mm` | `2018-12-26/L16_03041.lri` | `caller_pre_29a140=1`, `maker_after_299fd0=1`, `later_299c70_entry=1` | `wp1=12`, `wp2=8` | record `0` offset `0`, header `[27,3,1,8]`; record `1` offset `32`, header `[27,3,1,8]` |
| `70mm` | `2019-05-18/L16_03434.lri` | `caller_pre_29a140=1`, `maker_after_299fd0=1`, `later_299c70_entry=1` | `wp1=12`, `wp2=8` | record `0` offset `0`, header `[0,1,1,8]`; record `1` offset `32`, header `[0,1,1,8]` |
| `150mm` | `2018-07-29/L16_02285.lri` | `caller_pre_29a140=1`, `maker_after_299fd0=1`, `later_299c70_entry=1` | `wp1=12`, `wp2=4` | record `0` offset `0`, header `[2,8,1,8]`; record `1` offset `32`, header `[2,8,1,8]` |

All armed watchpoints had `bytes_before_hex = 0000000000000000`.
All generated outputs are Radiance HDR files.

Validator output:

```text
payload_watch_28mm.json: OK samples=16 watch_hits={'1': 12, '2': 4} pc=0x277a16 store=0x277a10
payload_watch_35mm.json: OK samples=20 watch_hits={'1': 12, '2': 8} pc=0x277a16 store=0x277a10
payload_watch_70mm.json: OK samples=20 watch_hits={'1': 12, '2': 8} pc=0x277a16 store=0x277a10
payload_watch_150mm.json: OK samples=16 watch_hits={'1': 12, '2': 4} pc=0x277a16 store=0x277a10
```

## Static Context

Static disassembly from `tools/libcp_disasm_intel.txt`:

```text
2779fc: movdqu xmmword ptr [rcx + 2*rdx], xmm0
277a01: pminuw xmm4, xmm0
277a06: movdqu xmm5, xmmword ptr [r9 + 2*rdx]
277a0c: paddusw xmm5, xmm0
277a10: movdqu xmmword ptr [r9 + 2*rdx], xmm5
277a16: add rdx, 0x8
277a1a: cmp rdx, r12
277a1d: jl 0x2779b0
```

Hardware watchpoints report the stopped PC after the watched write. Every
sample stopped at `libcp+0x277a16`. The validator requires every sampled
watched address to fall inside the 16-byte destination range
`r9 + 2*rdx .. r9 + 2*rdx + 15` and outside the nearby
`rcx + 2*rdx .. rcx + 2*rdx + 15` range.

Therefore the sampled payload mutation is attributed to:

```text
libcp+0x277a10: movdqu xmmword ptr [r9 + 2*rdx], xmm5
```

## Proven

- Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` no-auto-LRIS runs,
  sampled source-record payload bytes at `record+0x08` for the first two
  records are zero immediately after `0x299fd0`.
- Those sampled payload bytes are later mutated during the render.
- The sampled mutation stops are all at `libcp+0x277a16`, immediately after the
  `libcp+0x277a10` SIMD store.
- Register disambiguation proves the watched addresses match the `r9 + 2*rdx`
  destination of the `0x277a10` store and do not match the neighboring
  `rcx + 2*rdx` store.

## Not Proven

- The arithmetic or public meaning that produces `%xmm5`.
- Full-map payload distribution beyond the two watched records per focal tier.
- Public LRI/protobuf field origin for the source-local records or payloads.
- Whether these sampled costs are final costs, intermediate accumulated costs,
  or one contributor to a later score.
- Final merge contribution, anti-ghosting behavior, or acceptance/rejection.
