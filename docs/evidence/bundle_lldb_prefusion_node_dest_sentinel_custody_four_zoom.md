# Bundle + LLDB Proof: Prefusion Node-Destination Same-Address Sentinel + Downstream Custody, Four Zooms

## Scope

This note links two already-admitted Lane A boundaries:

- finite coordinate pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination
- later coordinate-pair sentinel invalidation at `0x21b923` and `0x21b92a` inside `0x21b2e0`

The probe records finite non-sentinel pair addresses from the node-vector copy destination, checks whether a later completed sentinel pair at `0x21b930` has the same runtime address, then arms a read/write watchpoint on that exact matched address. This proves same-address custody for one matched pair per canonical focal tier from copied finite node-vector coordinate, through sentinel invalidation, into sampled downstream touches. It does not prove all copied pairs, public state names, image effect, source contribution, reducer closure, or final acceptance/rejection semantics.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_sentinel_custody.py`
- Raw output directory:
  `runs/prefusion_node_dest_sentinel_custody/`

The admitted runtime JSON reports are:

- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.json`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.json`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.json`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.hdr`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.hdr`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.hdr`
- `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.hdr`

The static disassembly capture used for the sentinel-store window is:

- `runs/prefusion_node_dest_sentinel_custody/static_disasm_21b8f0_21b950.log`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x22a61a` | `0x22a0e0` node-vector copy call into `0xe8e70` |
| `0x22a61f` | return site after that copy |
| `0x22c93a` | `0x22c350` sibling node-vector copy call into `0xe8e70` |
| `0x22c93f` | return site after that sibling copy |
| `0x21b923` | x-lane sentinel store |
| `0x21b92a` | y-lane sentinel store |
| `0x21b930` | first instruction after the y-lane store |

At each paired node-vector copy return, the probe scans the destination vector and records finite non-sentinel pair addresses in an internal set. At `0x21b930`, it reads the just-completed pair, requires exact bytes `000080bf000080bf`, and admits a match only if that exact address was already present in the copied-address set. For each admitted match, the probe then arms one read/write watchpoint on the matched address.

The admitted scripts use `match_limit = 1` and `watch_hit_cap = 64`, so each run disables breakpoints after the first exact match and disables the watchpoint after 64 sampled downstream stops. Counts are capped observations, not full-render population counts.

## Static Anchor

Installed-bundle disassembly of `0x21b2e0` shows the local sentinel stores:

```asm
0x21b923: movl   $0xbf800000, (%rax,%rdx,8)
0x21b92a: movl   $0xbf800000, (%rcx)
0x21b930: addq   $0x4, %r13
```

The first store writes the x lane of the pair. The second writes the y lane. `0x21b930` is the first post-y-store instruction used by the probe to verify the full pair.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Copy vectors recorded | Copied finite-pair addresses | Full sentinel completions | Same-address matches | Downstream watchpoint stops |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `4` | `1770` | `1` | `1` | `64` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `4` | `5087` | `1` | `1` | `64` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `4` | `10197` | `1` | `1` | `64` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `4` | `1398` | `1` | `1` | `64` |

All admitted matches came from the `0x22a61a -> 0xe8e70 -> 0x22a61f` copy site before the one-match cap. The sibling `0x22c93a -> 0x22c93f` site is installed in the harness, but this note does not make a broad absence claim about it.

The admitted same-address byte transitions are:

| Zoom | Copy vectors | Copied addresses | Pair index | Bytes at copy | Bytes before x-store | Bytes before y-store | Bytes after y-store | Watch stops | Sampled downstream VAs |
|---|---:|---:|---:|---|---|---|---|---:|---|
| `28mm` | `4` | `1770` | `684` | `000055440080bd43` | `000055440080bd43` | `000080bf0080bd43` | `000080bf000080bf` | `64` | `0xe0bb2`, `0xe0bb7`, `0x20b912` |
| `35mm` | `4` | `5087` | `278` | `0000904200008443` | `0000904200008443` | `000080bf00008443` | `000080bf000080bf` | `64` | `0xe0bbd`, `0xe0bc3`, `0x20b912` |
| `70mm` | `4` | `10197` | `774` | `00005e440000c143` | `00005e440000c143` | `000080bf0000c143` | `000080bf000080bf` | `64` | `0xe0bd5`, `0xe0bdb`, `0x20b912`, `0x217048`, `0x217064`, `0x218bc4` |
| `150mm` | `4` | `1398` | `20` | `0020864400c02b44` | `0020864400c02b44` | `000080bf00c02b44` | `000080bf000080bf` | `64` | `0xe0bbd`, `0xe0bc3`, `0x20b912`, `0x217035`, `0x21703a`, `0x218bc4` |

Decoded copied-pair values for the admitted matches:

| Zoom | Copied pair value | Copy site |
|---|---|---|
| `28mm` | `(852.0, 379.0)` | `copy_a_ret_22a61f` from `copy_a_call_22a61a` |
| `35mm` | `(72.0, 264.0)` | `copy_a_ret_22a61f` from `copy_a_call_22a61a` |
| `70mm` | `(888.0, 386.0)` | `copy_a_ret_22a61f` from `copy_a_call_22a61a` |
| `150mm` | `(1073.0, 687.0)` | `copy_a_ret_22a61f` from `copy_a_call_22a61a` |

The verifier requires, for every match:

- copied address equals sentinelized address
- copied pair is finite and non-sentinel
- pre-x-store bytes at the same address still equal the copied finite pair
- mid-store bytes at the same address have x changed to `-1.0` while y is not yet sentinel
- post-y-store bytes at the same address are exactly `000080bf000080bf`
- the match stack includes `0x21b930`
- the downstream watchpoint is armed on that same address
- every sampled downstream stop still reads `000080bf000080bf`

## Admission Checks

The repo-local verifier rechecks clean completion, copied-address population, exact same-address matches, byte transitions, stack VAs, and Radiance HDR output custody:

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_sentinel_custody.py
28mm: OK copy_vectors=4 copied_addrs=1770 after_store_full=1 matches=1 watch_hits=64 downstream_vas=3 unique_after=1
35mm: OK copy_vectors=4 copied_addrs=5087 after_store_full=1 matches=1 watch_hits=64 downstream_vas=3 unique_after=1
70mm: OK copy_vectors=4 copied_addrs=10197 after_store_full=1 matches=1 watch_hits=64 downstream_vas=6 unique_after=1
150mm: OK copy_vectors=4 copied_addrs=1398 after_store_full=1 matches=1 watch_hits=64 downstream_vas=6 unique_after=1
```

The HDR verification command:

```bash
file runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.hdr runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.hdr runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.hdr runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. In every admitted run, the probe recorded finite non-sentinel coordinate pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination.
3. In every admitted run, one such copied finite pair address was later observed at `0x21b923` immediately before x-lane sentinelization with the same finite bytes.
4. In every admitted run, that same address was then observed at `0x21b92a` with x already set to `-1.0` and y still non-sentinel.
5. In every admitted run, that same address was then observed at `0x21b930` as full `(-1.0, -1.0)`.
6. In every admitted run, that same address was later touched by downstream code while still reading as full `(-1.0, -1.0)`.
7. The sampled downstream stops include `0xe0ae0` copy-loop sites across all four tiers, `0x20b912` across all four tiers, and tele scan/scoring sites in the `0x216f60` / `0x218b30` families.
8. This proves same-address custody from copied node-vector destination to sentinel invalidation and sampled downstream touches for one representative pair per canonical focal tier. It does not prove all copied pairs, image effect, source contribution, reducer closure, or final acceptance/rejection semantics.

## Safe Conclusion

The node-destination scoring/selection proof, the sentinel-write proof, and sampled downstream sentinel-touch proofs are linked by exact runtime address identity under the canonical bridge HDR quartet. At least one finite coordinate pair copied into the `0x22a61a` node-vector destination per focal tier is the same memory address later rewritten by `0x21b923` / `0x21b92a` into `(-1.0, -1.0)`, then later touched while still `(-1.0, -1.0)`.

This is stronger than adjacency in the call graph: it is same-address custody. The remaining open work is still downstream image/source-contribution consequence, final acceptance/rejection policy, and reducer closure.

## Consequence For Blocker Work

Lane A can replace the looser boundary:

`node-vector copied pair -> non-copy 0x21b2e0 consumer -> sentinel writes`

with the admitted same-address boundary:

`0x22a61a node-vector copy destination finite pair -> same address at 0x21b923 pre-x-store -> same address at 0x21b92a pre-y-store -> same address full sentinel at 0x21b930 -> sampled downstream copy / scan / scoring-materialization touches while still sentinel`

The next proof target remains downstream of sentinelization: image/source contribution, final acceptance/rejection, or a bounded terminal/non-effect path for the same sentinelized coordinate route.
