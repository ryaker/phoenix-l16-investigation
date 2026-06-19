# Static + Runtime Proof: Prefusion Sentinel `0x20b5e0` Branch Window

## Scope

This note refines the `0x20b912` portion of
`bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md`.

It uses:

- the already-admitted four-zoom watchpoint JSONs in
  `runs/prefusion_node_sentinel_downstream_watch/`
- a fresh repo-local static disassembly capture:
  `runs/prefusion_node_sentinel_downstream_watch/static_disasm_20b5e0_20bc20.log`

This note itself does not admit a direct branch-runtime probe. A hot direct
branch-census attempt was discarded because it did not produce completed JSON
evidence. Follow-up evidence in
`bundle_lldb_prefusion_sentinel_20b5e0_branch_step_four_zoom.md` admits a
lighter branch-step runtime proof for sampled `0x20b912` sentinel reads.

This note proves the local static branch/write boundary around runtime-observed
`0x20b912` sentinel reads. It does not prove whole-vector terminality, final
image effect, source contribution, reducer closure, or final acceptance /
rejection semantics.

## Runtime Input Reused

The admitted downstream-watch runs already prove clean completion and sampled
watchpoint stops at `0x20b912`:

| Zoom | LRI | Exit | Step cap | JSON errors | Samples at `0x20b912` | Pair bytes |
|---|---|---:|---|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `000080bf000080bf` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `000080bf000080bf` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `000080bf000080bf` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `2` | `000080bf000080bf` |

The admission check for this table:

```bash
jq -s 'map({label, exit: .process_exit_status, step_cap: .drive_hit_step_cap, errors: (.errors|length), watchpoint_samples: (.watchpoint_samples|length), sentinel_20b912_samples: ([.watchpoint_samples[] | select(.stack[0].libcp_va == 2144530)] | length), sentinel_20b912_pairs: ([.watchpoint_samples[] | select(.stack[0].libcp_va == 2144530) | .pair_now.hex] | unique)})' runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json
```

`2144530` is decimal `0x20b912`.

## Static Capture

The disassembly capture command:

```bash
arch -x86_64 lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x20b5e0 --end-address 0x20bc20' > runs/prefusion_node_sentinel_downstream_watch/static_disasm_20b5e0_20bc20.log
```

The local branch/write window:

```text
0x20b90c: movss  (%rax,%r15,8), %xmm2
0x20b912: movl   $0xbf800000, %ecx
0x20b917: xorps  %xmm1, %xmm1
0x20b91a: ucomiss %xmm2, %xmm1
0x20b91d: jae    0x20ba90
...
0x20ba90: movl   $0xbf800000, %edx
0x20ba95: movl   $0xbf800000, %esi
0x20ba9a: movd   %esi, %xmm0
0x20baa8: ucomiss %xmm1, %xmm0
0x20baab: jbe    0x20bafd
0x20bac0: movl   %ecx, 0x8(%rdi,%rbx,4)
0x20bac4: movl   %edx, 0xc(%rdi,%rbx,4)
0x20bac8: movl   %esi, (%r8)
0x20bafd: incq   %r15
```

## Proven Facts

1. The admitted four-zoom watchpoint evidence sampled `0x20b912` stops in
   clean completed `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs.
2. Every sampled `0x20b912` stop still read the watched pair as raw bytes
   `000080bf000080bf`, two little-endian binary32 `-1.0` values.
3. Static disassembly proves `0x20b90c` is the x-lane load immediately before
   the sampled `0x20b912` stop.
4. Static disassembly proves the local x-lane branch compares zero against the
   loaded x value at `0x20b91a` and branches at `0x20b91d` to `0x20ba90` for
   the `jae` condition.
5. Static disassembly proves the `0x20ba90` path writes raw sentinel bits
   `0xbf800000` into `edx` and `esi`, while `ecx` was already loaded with
   `0xbf800000` at `0x20b912`.
6. Static disassembly proves the later `0x20baab -> 0x20bafd` branch bypasses
   the local update writes at `0x20bac0`, `0x20bac4`, and `0x20bac8`.

## Safe Conclusion

For the sampled `0x20b912` downstream stops, runtime proves the input pair is
still `(-1.0, -1.0)`, and static disassembly proves that this helper window has
a local nonpositive/sentinel branch path that bypasses the `0x20bac0..0x20bac8`
update-write block.

This document is a local branch-boundary fact for sampled sentinel reads. The
follow-up branch-step bundle supplies the direct runtime flags / branch-target
proof for sampled `0x20b912` reads. Neither note is exhaustive over all sentinel
entries, final acceptance / rejection proof, or image-effect proof.
