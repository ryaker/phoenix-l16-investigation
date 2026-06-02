# Static + Runtime Proof: Prefusion Sentinel `0x216f60` Scan-Count Window

## Scope

This note refines the `0x216f60` / `0x2170d1` scan-count portion of
[bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md).

It uses:

- the already-admitted four-zoom watchpoint JSONs in
  `runs/prefusion_node_sentinel_downstream_watch/`
- a fresh repo-local static disassembly capture:
  `runs/prefusion_node_sentinel_downstream_watch/static_disasm_216f60_217110_refresh.log`

This note proves a local scan/count boundary for sampled sentinel-coordinate reads. It does not prove whole-vector terminality, final image effect, source contribution, reducer closure, or final acceptance / rejection semantics.

## Runtime Input Reused

The admitted downstream-watch runs already prove clean completion and selected later sentinel-coordinate touches. The scan-count subset in this note is:

| Zoom | LRI | Exit | Step cap | JSON errors | Sampled watchpoint stops | Scan-count-window samples | Pair bytes |
|---|---|---:|---|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `64` | `0` | none sampled |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `64` | `0` | none sampled |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `64` | `6` | `000080bf000080bf` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `65` | `4` | `000080bf000080bf` |

The admitted scan-count stops are sampled/capped watchpoint observations. The zero wide rows mean only that the admitted wide watchpoint samples did not stop inside this local scan-count window; they are not proof that wide sentinel pairs never reach it.

The admission check for this table:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false) and (.[0].watchpoint_samples | length) == 64 and (.[1].watchpoint_samples | length) == 64 and (.[2].watchpoint_samples | length) == 64 and (.[3].watchpoint_samples | length) == 65 and (([.[2].watchpoint_samples[] | select((.stack[0].libcp_va == 2191413) or (.stack[0].libcp_va == 2191418) or (.stack[0].libcp_va == 2191432) or (.stack[0].libcp_va == 2191439) or (.stack[0].libcp_va == 2191460) or (.stack[0].libcp_va == 2191466))] | length) == 6) and (([.[3].watchpoint_samples[] | select((.stack[0].libcp_va == 2191439) or (.stack[0].libcp_va == 2191466) or (.stack[0].libcp_va == 2191543) or (.stack[0].libcp_va == 2191549))] | length) == 4) and all(.[2].watchpoint_samples[] | select((.stack[0].libcp_va == 2191413) or (.stack[0].libcp_va == 2191418) or (.stack[0].libcp_va == 2191432) or (.stack[0].libcp_va == 2191439) or (.stack[0].libcp_va == 2191460) or (.stack[0].libcp_va == 2191466)); .pair_now.hex == "000080bf000080bf") and all(.[3].watchpoint_samples[] | select((.stack[0].libcp_va == 2191439) or (.stack[0].libcp_va == 2191466) or (.stack[0].libcp_va == 2191543) or (.stack[0].libcp_va == 2191549)); .pair_now.hex == "000080bf000080bf")' runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Static Capture

The disassembly capture command:

```bash
arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x216f60 --end-address 0x217110' > runs/prefusion_node_sentinel_downstream_watch/static_disasm_216f60_217110_refresh.log
```

The local vector-count window:

```text
0x217030: movss   -0x1c(%rdx), %xmm2
0x217035: movss   -0x18(%rdx), %xmm3
0x21703a: insertps $0x10, -0x14(%rdx), %xmm2
0x217048: insertps $0x30, -0x4(%rdx), %xmm2
0x21704f: xorps   %xmm4, %xmm4
0x217052: cmpltps %xmm2, %xmm4
0x217064: insertps $0x30, (%rdx), %xmm3
0x21706a: xorps   %xmm2, %xmm2
0x21706d: cmpltps %xmm3, %xmm2
0x217071: andps   %xmm4, %xmm2
0x217074: andps   %xmm1, %xmm2
0x217077: paddd   %xmm2, %xmm0
```

This vector path forms `0 < x`, forms `0 < y`, ANDs those masks, masks the result as integer counts, and adds into the vector count accumulator.

The scalar tail and threshold:

```text
0x2170b4: ucomiss (%rcx), %xmm0
0x2170b7: sbbb    %dl, %dl
0x2170b9: ucomiss 0x4(%rcx), %xmm0
0x2170bd: sbbb    %al, %al
0x2170bf: andb    %dl, %al
0x2170c1: andb    $0x1, %al
0x2170c6: addl    %eax, %ebx
0x2170d1: cmpl    $0x8, %ebx
0x2170d4: jl      0x217d00
```

This scalar path likewise adds `1` only when both lanes satisfy the positive-pair test, then requires at least eight counted entries before continuing past `0x2170d4`.

## Proven Facts

1. The admitted four-zoom downstream-watch evidence completed cleanly and wrote Radiance HDR outputs.
2. The admitted `70mm` downstream-watch run sampled six stops inside the `0x216f60` scan-count window listed above.
3. The admitted `150mm` downstream-watch run sampled four stops inside the same local scan-count window.
4. Every sampled `70mm` / `150mm` scan-count-window stop still read the watched pair as raw bytes `000080bf000080bf`, two little-endian binary32 `-1.0` values.
5. Static disassembly proves the local vector path counts only lanes where `0 < x` and `0 < y`.
6. Static disassembly proves the scalar tail also adds to the count only when both pair lanes are positive, and the local threshold requires at least eight counted entries before continuing past `0x2170d4`.

## Safe Conclusion

For the sampled tele `0x216f60` scan-count-window stops, runtime proves the input pair is still `(-1.0, -1.0)`, and static disassembly proves that this local scan/count body counts only positive `(x, y)` pairs.

Therefore the sampled sentinel pairs are local non-counting inputs to this scan/count window. This is a bounded local rejection/non-counting fact. It is not whole-vector terminality, final image-effect proof, source-contribution proof, reducer closure, or final acceptance / rejection.
