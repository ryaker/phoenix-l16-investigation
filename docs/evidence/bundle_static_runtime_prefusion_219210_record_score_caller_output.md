# Evidence: Prefusion `0x219210` Record-Score Caller Output Path

## Scope

This note follows
`bundle_static_runtime_prefusion_218940_solved_record_score_window.md`.

The prior note proves that one watched Unit-1 `70mm` solved-record
`record+0x10` value reaches helper `0x218940`'s local positive z-gated
record/transform score body. This note asks the next local custody question:
what does the caller do with the `0x218940` helper result?

Answer: byte-pinned static code and vtable/typeinfo checks identify `0x219210`
as slot `+0x30` of the `std::__function` callback for
`lt::SparseMirrorAngleOptimizer::optimize(...)::$_2`. That caller invokes
`0x218940` at `0x219375`, returns at `0x21937a`, and immediately stores `xmm0`
into the caller output vector at `[r14+0x18][r15]` via `0x219381`. Runtime stack
samples from the same watched solved record prove the 37 `0x2189c4` stops are
inside that `0x219210 -> 0x218940` callsite.

This is caller output-vector custody only. It does not prove the stored numeric
value, all-record behavior, downstream consumer identity, image/source
contribution, reducer closure, or final acceptance/rejection.

## Artifacts

- Runtime packet reused:
  `runs/prefusion_20ca00_record_z_watch/record_z_watch_unit1_70mm.json`
- Prior evidence bundle:
  `docs/evidence/bundle_static_runtime_prefusion_218940_solved_record_score_window.md`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_219210_record_score_caller_output.py`

## Static Caller Shape

The verifier SHA-pins installed `libcp.dylib` bytes
`0x219210..0x219409`:

```text
sha256 = a988329eb834dbd9c64c0499f93e83fa24813d18c020827ccdfb9dc54c6c7540
```

It also verifies the callback identity:

```text
address point 0x658138
slot +0x30    0x219210
typeinfo      std::__function::__func<
                lt::SparseMirrorAngleOptimizer::optimize(...)::$_2,
                allocator<...>,
                void (int,int,int)>
```

The key caller instructions are:

```text
0x219358  rdx = [r14+0x30]
0x21935c  rax = [r14+0x38]
0x219360  rcx = r15 * 4
0x219368  rcx += [rax]
0x21936b  rdi = [rbp-0x228]
0x219372  rsi = r13
0x219375  call 0x218940
0x21937a  rax = [r14+0x18]
0x21937e  rax = [rax]
0x219381  [rax + r15*4] = xmm0
```

So `0x218940` has two local outputs under this caller: the helper itself writes
one score-like float through `rcx`, and the caller stores the returned `xmm0`
into a separate per-index vector rooted at `r14+0x18`.

## Runtime Stack Custody

The reused Unit-1 `70mm` watch packet captures 37 stops at `0x2189c4` for the
watched solved-record z. Every one has:

```text
stack[0] = 0x2189c4 inside helper 0x218940
stack[1] = 0x21937a inside caller 0x219210
rax      = watched z address
rdx      = selected gate_index 3906
```

The helper samples span 37 unique caller indices, with `r15` ranging from `16`
through `324` in the captured windows. The verifier also checks that
`rcx - 4*r15` is stable (`0x7fb347b28a00`) across those 37 samples, matching
the static per-index `rcx` slot formation before the `0x218940` call.

## Verification

Commands:

```bash
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_219210_record_score_caller_output.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_219210_record_score_caller_output.py
```

Verifier output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
window=0x219210..0x219409 sha256=a988329eb834dbd9c64c0499f93e83fa24813d18c020827ccdfb9dc54c6c7540
callback_type=SparseMirrorAngleOptimizer::optimize::$_2 std::__function void(int,int,int) address_point=0x658138 slot+0x30=0x219210
report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_20ca00_record_z_watch/record_z_watch_unit1_70mm.json
runtime_stack=gate_index=3906 z=3499.366699219 z_compare_samples=37 caller_return=0x21937a r15_range=16..324 rcx_base=0x7fb347b28a00
caller_output=0x219375 call 0x218940 -> 0x219381 store xmm0 into [r14+0x18][r15]
scope=caller output-vector path only; no stored value, image effect, or final acceptance proven
```

## Safe Conclusion

For the watched Unit-1 `70mm` solved-record field, the local path now extends
one step beyond helper admission: runtime stack custody places the samples in
the `lt::SparseMirrorAngleOptimizer::optimize(...)::$_2` callback at
`0x219210`, and byte-pinned static code shows that a normal return from the same
callsite stores the helper's `xmm0` result into a per-index float vector at
`r14+0x18`.

This narrows local score custody. It does not yet prove the exact stored value,
the later consumer of the `r14+0x18` vector, all-record behavior, image/source
contribution, reducer closure, or final acceptance/rejection.
