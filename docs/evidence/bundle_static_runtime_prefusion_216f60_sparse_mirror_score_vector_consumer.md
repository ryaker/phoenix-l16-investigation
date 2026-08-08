# Evidence: Prefusion `0x216f60` Sparse-Mirror Score-Vector Consumer

## Scope

This note follows
`bundle_static_runtime_prefusion_219210_record_score_caller_output.md`.

The prior note proves that the watched Unit-1 `70mm` solved-record field reaches
helper `0x218940`, returns through callback `0x219210`, and that the callback
stores helper `xmm0` into its captured output vector at `[r14+0x18][r15]`.

This note asks the next local custody question: does the parent body consume
that captured vector?

Answer: yes, at same-runtime vector-address scope for one complete Unit-1
`70mm` render. A byte-pinned decode of parent body `0x216f60` shows it constructs the
`lt::SparseMirrorAngleOptimizer::optimize(...)::$_2` callback object, captures
the stack vector header `[rbp-0x3f0]` at callback field `+0x18`, dispatches the
callback through `0x5670`, then reads the same `[rbp-0x3f0]` vector after
dispatch at `0x217a68`. The post-dispatch code runs a `ucomiss` / `jae`
min-like scan over that vector, checks the selected index against the helper
side-output vector `[rbp-0x410]`, and materializes the selected 24-byte grid
record from `[rbp-0x430]` before calling `0xf33d0`. A new LLDB packet captures
one closure construction, 64 matching callback stores after `0x219381`, and one
matched parent consumer at `0x217a68`; all three stages carry the exact same
return-vector header and begin pointer.

This is one-render same-runtime callback-store to parent-consumer vector
custody. It is not record-specific score-value proof, all-record proof, public
acceptance/rejection semantics, image/source contribution, reducer closure, or
final acceptance/rejection proof.

## Artifacts

- Runtime packet:
  `runs/prefusion_216f60_score_vector_consumer/score_vector_consumer_unit1_70mm.json`
- LLDB probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_score_vector_consumer_probe.py`
- LLDB command file:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_216f60_score_vector_consumer_unit1_70mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_score_vector_consumer_unit1_70mm.sh`
- Prior evidence bundle:
  `docs/evidence/bundle_static_runtime_prefusion_219210_record_score_caller_output.md`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_sparse_mirror_score_vector_consumer.py`

## Static Parent Shape

The verifier SHA-pins installed `libcp.dylib` bytes
`0x216f60..0x2180e0`:

```text
sha256 = 42b320ff8f9c3c0f5c2eaccff82a52fa4a105b1c475b799b2362a3d86e8d1f7e
```

It also re-verifies that callback slot `+0x30` at vtable address point
`0x658138` is `0x219210`, with the same
`SparseMirrorAngleOptimizer::optimize(...)::$_2` typeinfo admitted by the prior
caller-output proof.

The parent allocates and initializes three local vectors:

```text
[rbp-0x3f0]  per-index callback return vector captured at callback +0x18
[rbp-0x410]  helper side-output vector captured at callback +0x38
[rbp-0x430]  24-byte per-index candidate/grid record vector captured at callback +0x10
```

Callback construction and dispatch:

```text
0x217926  rcx = 0x658138
0x21792d  [callback] = rcx
0x21793b  rcx = &[rbp-0x430]
0x217942  [callback+0x10] = rcx
0x217946  rcx = &[rbp-0x3f0]
0x21794d  [callback+0x18] = rcx
0x21796b  rcx = &[rbp-0x410]
0x217972  [callback+0x38] = rcx
0x217992  call 0x5670
```

Post-dispatch consumer:

```text
0x217a68  rax = [rbp-0x3f0]
0x217a6f  rdx = [rbp-0x3e8]
0x217a99  xmm0 = [candidate]
0x217a9d  ucomiss xmm0, [current_winner]
0x217aa0  jae keep_current_winner
0x217aa4  rcx = selected_byte_offset
0x217aae  rsi = [rbp-0x410]
0x217ab9  xmm0 = side_output[selected_byte_offset]
0x217ac6  threshold check
0x217ad2  center-side-output check
0x217ae8  optional center return-vector check
0x217aff  rax = [rbp-0x430]
0x217b0a  load selected 24-byte record fields
0x217bbe  call 0xf33d0
```

## Runtime Same-Vector Custody

The complete Unit-1 `70mm` packet records:

```text
closure                         0x7fd0b1806cb0
return-vector header            0x304c67f40
return-vector begin             0x7fd08580f600
return-vector count             1089
side-output count               1089
candidate-record count          1089
matching callback-store samples 64
matched parent consumer         0x217a68
```

At construction `0x21797a`, closure fields `+0x18`, `+0x38`, and `+0x10`
exactly equal the three expected stack-vector header addresses. Every sampled
post-store stop at `0x219387` has the same closure pointer, the same
return-vector begin pointer in `rax`, a unique in-range index, and a readable
float at `begin + 4*index`.

At parent consumer `0x217a68`, the return header, return begin pointer, side
header, and candidate-record header all still equal the construction packet.
The verifier mirrors the installed `ucomiss` / `jae` scan over all 1,089 return
values and obtains:

```text
winner index 505
winner bits  57309940
winner value 4.787150859832764
```

This proves same-runtime vector custody. It does not bind the earlier watched
`record+0x10` sample to one particular stored score index or value.

## Verification

Commands:

```bash
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_score_vector_consumer_probe.py
bash tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_score_vector_consumer_unit1_70mm.sh
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_sparse_mirror_score_vector_consumer.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_sparse_mirror_score_vector_consumer.py
```

Verifier output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
window=0x216f60..0x2180e0 sha256=42b320ff8f9c3c0f5c2eaccff82a52fa4a105b1c475b799b2362a3d86e8d1f7e
callback_construction=0x216f60 stores vtable 0x658138 and captures vector headers +0x18=&[rbp-0x3f0], +0x38=&[rbp-0x410], +0x10=&[rbp-0x430]
runtime_same_vector=closure=0x7fd0b1806cb0 return_header=0x304c67f40 return_begin=0x7fd08580f600 count=1089 stores=64 consumer=0x217a68
runtime_winner=index=505 value=4.787150860 hex=57309940
runtime_report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_216f60_score_vector_consumer/score_vector_consumer_unit1_70mm.json
scope=one Unit-1 70mm same-runtime callback-store to parent-consumer vector custody; no record-specific score, image effect, or final acceptance proven
```

## Safe Conclusion

The `0x219210` callback output vector now has a verified local consumer in its
parent `0x216f60` body. The parent captures `[rbp-0x3f0]` at callback field
`+0x18`, the callback stores helper returns through that field, and the parent
then receives the same runtime vector header and begin pointer after dispatch
before scanning, gating, and materializing one selected record for `0xf33d0`.

This narrows the solved-record local score path. It does not prove the watched
record's stored score value, all-record behavior, public acceptance/rejection
semantics, image/source contribution, reducer closure, or final
acceptance/rejection.
