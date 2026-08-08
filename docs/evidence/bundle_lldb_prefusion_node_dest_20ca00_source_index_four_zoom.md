# Bundle + LLDB Proof: Prefusion Node-Destination `0x20ca00` Source/Gate Index, Four Zooms

## Scope

This note extends
`bundle_lldb_prefusion_node_dest_20ca00_source_copy_four_zoom.md` with fresh
runtime packets that reconstruct the local `0x20ca00` source index and parent
gate index for the exact copied node-destination address.

It proves that, for one representative copied node-destination pair per
canonical focal tier:

1. the pair is copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f`
   node-vector destination as a finite non-sentinel coordinate pair,
2. the same runtime address is later sentinelized to full `(-1.0, -1.0)`,
3. that same address is source-read by `0xe0ae0` under caller return `0x20d309`,
   the second local vector copy inside `0x20ca00`,
4. and every captured `0x20d309` source/gate index packet for that watched
   address has `source_index != gate_index`.

The watchpoint cap is reached in every tier, so this is a capped-window local
non-selection proof for the representative watched address. It does not prove
all copied node-destination pairs, all `0x20ca00` invocations, destination-slot
terminality, image effect, source contribution, reducer closure, or final
acceptance/rejection.

## Repo-Local Artifacts

- Shared probe harness:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_index_28mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_index_35mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_index_70mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_index_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_index_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_source_index.py`
- Raw output directory:
  `runs/prefusion_node_dest_20ca00_source_index/`

The admitted runtime JSON reports are:

- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_28mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_35mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_70mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_28mm.hdr`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_35mm.hdr`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_70mm.hdr`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The shared same-address probe records finite node-vector destination pairs at
`0x22a61f`, matches later sentinel completions at the same address, and arms one
read/write watchpoint on the matched address. In this mode, the watchpoint
handler records an extra candidate packet when the watched address is source-read
by the `0xe0ae0` unrolled source-copy family under caller frame `0x20d309`.

For each such packet, the probe records:

- `source_index` from the live source vector header at `r15`
- `gate_index` from the parent `0x20ca00` local slot `rbp-0x2a0`
- whether the exact watched source address matches the source pair reconstructed
  from the current `0xe0ae0` source-read PC
- the copied destination address implied by the same unrolled copy offset

## Static Anchor

The `0x20ca00` second local copy and gate-index slot are the same anchors used
by `bundle_lldb_prefusion_20ca00_copied_sentinel_gate_four_zoom.md`:

```text
0x20d2f9: leaq 0x28(%rbx), %rsi
0x20d2fd: leaq -0xe0(%rbp), %rdi
0x20d304: callq 0xe0ae0
0x20d309: return site after the second local vector copy
0x20d354: movq -0x2a0(%rbp), %rax
0x20d35e: ucomiss (%r15,%rax,8), %xmm0
0x20d363: jae 0x20d565
```

This note does not trace the destination watchpoint to `0x20d363`; it only
checks whether the watched source slot equals the local gate index for captured
`0x20d309` source-copy packets.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Watch cap hit | Source index | Captured `0x20d309` packets | Index matches | Index mismatches | Gate-index range | Unique gate indices |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `1` | `684` | `117` | `0` | `117` | `703..5503` | `60` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `1` | `278` | `117` | `0` | `117` | `2401..2513` | `59` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `1` | `77` | `106` | `0` | `106` | `2..5306` | `56` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `1` | `1915` | `106` | `0` | `106` | `111..1787` | `58` |

The admitted same-address byte transitions are:

| Zoom | Pair index | Bytes at copy | Decoded copied pair | Bytes after sentinelization |
|---|---:|---|---|---|
| `28mm` | `684` | `000055440080bd43` | `(852.0, 379.0)` | `000080bf000080bf` |
| `35mm` | `278` | `0000904200008443` | `(72.0, 264.0)` | `000080bf000080bf` |
| `70mm` | `77` | `0020a74400007042` | `(1337.0, 60.0)` | `000080bf000080bf` |
| `150mm` | `1915` | `0080ec4400001c44` | `(1892.0, 624.0)` | `000080bf000080bf` |

The verifier requires every stored candidate packet to have:

- caller frame `0x20d309`
- source watch address equal to the matched node-destination address
- reconstructed source pair equal to the watched address
- readable source vector index
- readable parent `rbp-0x2a0` gate index
- parent frame `0x20d309`
- readable copied destination pair

## Admission Checks

The repo-local verifier rechecks clean completion, same-address node-destination
custody, candidate packet integrity, readable source/gate indices, and Radiance
HDR output custody:

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_source_index.py
28mm: OK same_addr=140552203736416 source_index_packets=117 stored=117 index_matches=0 index_mismatches=117
35mm: OK same_addr=140202376136880 source_index_packets=117 stored=117 index_matches=0 index_mismatches=117
70mm: OK same_addr=140437143093864 source_index_packets=106 stored=106 index_matches=0 index_mismatches=106
150mm: OK same_addr=140593355573208 source_index_packets=106 stored=106 index_matches=0 index_mismatches=106
```

The HDR verification command:

```bash
file runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_28mm.hdr runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_35mm.hdr runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_70mm.hdr runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no drive step cap, and Radiance HDR outputs.
2. In each admitted run, one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination was later matched by exact runtime address at the sentinel store path.
3. In each admitted run, that same address was later source-read by `0xe0ae0` under caller return `0x20d309` while still reading as full `(-1.0, -1.0)`.
4. In every captured `0x20d309` source/gate index packet for that watched address, `source_index` and `gate_index` were readable.
5. In every captured packet, the watched source address reconstructed to the exact source pair being read.
6. In every captured packet, `source_index != gate_index`.

## Safe Conclusion

For the representative copied node-destination pair in each canonical focal
tier, the watched sentinel source slot is copied by the `0x20ca00` second local
vector-copy path, but the captured local gate index does not select that source
slot before the watchpoint cap is reached.

This is a capped local non-selection fact for one watched address per tier. It
narrows the `0x20ca00` route, but does not prove destination-slot terminality,
whole-vector terminality, image/source contribution, final acceptance/rejection,
or reducer closure.
