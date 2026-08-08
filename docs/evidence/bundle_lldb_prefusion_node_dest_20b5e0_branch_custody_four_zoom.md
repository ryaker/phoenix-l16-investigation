# Bundle + LLDB Proof: Prefusion Node-Destination Same-Address `0x20b5e0` Branch Custody, Four Zooms

## Scope

This note extends
`bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md` with a local
branch-step trace through the already-bounded `0x20b5e0` helper window.

It proves that one finite coordinate pair copied into the
`0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal
tier is later:

1. observed at the same runtime address before the `0x21b923` x-lane sentinel store,
2. observed at that same address as full `(-1.0, -1.0)` at `0x21b930`,
3. watched at that same address until a downstream stop at `0x20b912`,
4. single-stepped through the local `0x20b5e0` sentinel / nonpositive branch path,
5. and skipped the local update-write block at `0x20bac0..0x20bac8`.

This is representative same-address local branch-custody proof only. It does not
prove all copied pairs, whole-vector terminality, image effect, source
contribution, reducer closure, public acceptance semantics, or final
acceptance/rejection.

## Repo-Local Artifacts

- Shared probe harness:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- Branch-step LLDB scripts:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20b5e0_branch_28mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20b5e0_branch_35mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20b5e0_branch_70mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20b5e0_branch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20b5e0_branch_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20b5e0_branch_custody.py`
- Raw output directory:
  `runs/prefusion_node_dest_20b5e0_branch_custody/`

The admitted runtime JSON reports are:

- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_28mm.json`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_35mm.json`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_70mm.json`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_28mm.hdr`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_35mm.hdr`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_70mm.hdr`
- `runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The shared same-address probe was extended with an optional branch-step mode.
The original same-address scripts leave that mode disabled. The scripts for
this note enable `branch_step_20b5e0 = True`, keep `match_limit = 1`, and set
`branch_trace_limit = 1`.

At the first copied-address sentinel match, the probe arms one read/write
watchpoint on the exact matched pair address. When that watched address stops at
`0x20b912` while still full sentinel, the probe single-steps the same thread
through the local branch window.

## Static Branch Anchors

The branch-step trace is interpreted against the static window admitted by
`bundle_static_prefusion_sentinel_20b5e0_branch_window.md`:

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

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Copied finite-pair addresses | Same-address matches | Watch stops | Branch traces | `0x20b91d -> 0x20ba90` | `0x20baab -> 0x20bafd` | Update write reached |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `1770` | `1` | `3` | `1` | `1` | `1` | `0` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `5087` | `1` | `3` | `1` | `1` | `1` | `0` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `14712` | `1` | `13` | `1` | `1` | `1` | `0` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `883` | `1` | `13` | `1` | `1` | `1` | `0` |

The same-address byte transitions and branch results are:

| Zoom | Pair index | Bytes at copy | Bytes before x-store | Bytes before y-store | Bytes after y-store | Bytes at `0x20b912` | `0x20b91d` flags / target | `0x20baab` flags / target |
|---|---:|---|---|---|---|---|---|---|
| `28mm` | `684` | `000055440080bd43` | `000055440080bd43` | `000080bf0080bd43` | `000080bf000080bf` | `000080bf000080bf` | `CF=0` / `0x20ba90` | `CF=1` / `0x20bafd` |
| `35mm` | `278` | `0000904200008443` | `0000904200008443` | `000080bf00008443` | `000080bf000080bf` | `000080bf000080bf` | `CF=0` / `0x20ba90` | `CF=1` / `0x20bafd` |
| `70mm` | `77` | `0020a74400007042` | `0020a74400007042` | `000080bf00007042` | `000080bf000080bf` | `000080bf000080bf` | `CF=0` / `0x20ba90` | `CF=1` / `0x20bafd` |
| `150mm` | `20` | `0020864400c02b44` | `0020864400c02b44` | `000080bf00c02b44` | `000080bf000080bf` | `000080bf000080bf` | `CF=0` / `0x20ba90` | `CF=1` / `0x20bafd` |

Decoded copied-pair values for the admitted matches:

| Zoom | Copied pair value | Copy site |
|---|---|---|
| `28mm` | `(852.0, 379.0)` | `copy_a_ret_22a61f` |
| `35mm` | `(72.0, 264.0)` | `copy_a_ret_22a61f` |
| `70mm` | `(1337.0, 60.0)` | `copy_a_ret_22a61f` |
| `150mm` | `(1073.0, 687.0)` | `copy_a_ret_22a61f` |

## Admission Checks

The repo-local verifier rechecks clean completion, exact copied-address match
custody, full-sentinel bytes at `0x20b912`, runtime flags and branch-step
targets, absence of the local update-write block, and Radiance HDR output
custody:

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20b5e0_branch_custody.py
28mm: OK copied_addrs=1770 watch_hits=3 branch_traces=1 pair_addr=140642066634080
35mm: OK copied_addrs=5087 watch_hits=3 branch_traces=1 pair_addr=140289628244144
70mm: OK copied_addrs=14712 watch_hits=13 branch_traces=1 pair_addr=140386983903848
150mm: OK copied_addrs=883 watch_hits=13 branch_traces=1 pair_addr=140349968253600
```

The HDR verification command:

```bash
file runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_28mm.hdr runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_35mm.hdr runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_70mm.hdr runs/prefusion_node_dest_20b5e0_branch_custody/node_dest_20b5e0_branch_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` branch-custody runs completed with exit status `0`, no probe errors, no drive step cap, and Radiance HDR outputs.
2. In each admitted run, one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination was later matched by exact runtime address at the sentinel store path.
3. In each admitted run, that same address changed from its copied finite bytes to x-lane sentinel at `0x21b923`, then full `(-1.0, -1.0)` at `0x21b930`.
4. In each admitted run, the same watched address later stopped at `0x20b912` and still read as `000080bf000080bf`.
5. In each admitted run, single-stepping the stopped thread reached `0x20b91d` with `CF = 0` and stepped to `0x20ba90`.
6. In each admitted run, the same branch trace then reached `0x20baab` with `CF = 1` and stepped to `0x20bafd`.
7. No admitted branch trace visited the local update-write block beginning at `0x20bac0`.

## Safe Conclusion

The same-address chain now extends one local consumer step beyond downstream
touch. For one representative node-vector destination pair per canonical focal
tier, LLDB proves:

`copied finite node-destination pair -> same-address sentinel rewrite -> same-address 0x20b912 downstream read -> local 0x20b5e0 sentinel/nonpositive branch skip`

This strengthens the sampled `0x20b5e0` branch-step evidence by carrying the
copied node-destination identity into the branch trace. It remains sampled and
local; downstream image/source-contribution consequence, all-pairs coverage,
final acceptance/rejection, and reducer closure remain open.
