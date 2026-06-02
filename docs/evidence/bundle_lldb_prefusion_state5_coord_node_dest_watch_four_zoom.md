# Bundle + LLDB Proof: Prefusion State-5 Coordinate Node-Destination Non-Copy Consumer, Four Zooms

## Scope

This note follows the node-vector destination already bounded by the coordinate-copy-destination proof.

The probe reuses the coordinate copy-destination watch harness, but overrides the copy callsites to the higher node-vector materialization/copy sites:

- `0x22a61a`, returning at `0x22a61f`
- `0x22c93a`, returning at `0x22c93f`

For call/return pairs observed on the same thread, it scans the destination vector after the copy returns, arms hardware read/write watchpoints on representative finite non-sentinel `(float x, float y)` pairs, and records later watchpoint stops.

This proves only the tested node-vector coordinate destination reaches a non-copy candidate/index/scoring-selection consumer under the admitted runs. It does not prove public state names, public target meanings, image contribution, final acceptance/rejection semantics, reducer closure, final merge quality policy, or that every copied node vector is consumed this way.

Important nuance: the admitted capped window observed the `0x22a61a -> 0x22a61f` node-vector copy site only. The sibling `0x22c93a -> 0x22c93f` site was installed but had zero observed call/return hits before the probe armed its watchpoints and disabled copy breakpoints. The older copy-destination proof already showed both node-vector copy sites can be later `0xe8e70` copy consumers; this proof only follows the `0x22a61a` destination to non-copy reads.

## Repo-Local Artifacts

- Configurable probe harness:
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/prefusion_state5_coord_copy_dest_watch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_28mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_35mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/run_four_zoom.sh`
- Raw output directory:
  `runs/prefusion_state5_coord_node_dest_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_28mm.json`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_35mm.json`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_70mm.json`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_28mm.hdr`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_35mm.hdr`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_70mm.hdr`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_150mm.hdr`

The static disassembly capture used for the consumer windows is:

- `runs/prefusion_state5_coord_node_dest_watch/static_disasm.log`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x22a61a` | `0x22a0e0` node-vector copy call into `0xe8e70` |
| `0x22a61f` | return site after that call |
| `0x22c93a` | `0x22c350` node-vector copy call into `0xe8e70` |
| `0x22c93f` | return site after that call |

The probe only arms destination watchpoints for return-site hits that have a same-thread pending callsite packet. A return-site hit without a pending call is counted separately and is not used as copy evidence.

## Static Anchor

Installed-bundle disassembly shows:

- `0x22a0e0` finds or creates a `0x40`-byte node, initializes the node vector header at `+0x28`, and conditionally copies a source vector into that node vector at `0x22a61a -> 0xe8e70 -> 0x22a61f`.
- `0x22c350` has a sibling node-vector copy site at `0x22c93a -> 0xe8e70 -> 0x22c93f`; this sibling site is not admitted as non-copy-consumed by this proof because it had zero observed call/return hits before the watch limit.
- `0x22a9b0` is a State-family body that calls `0x21b2e0` at `0x22a9e2`; runtime watchpoint stacks reach `0x21b2e0` through `0x22a9e7`.
- `0x22f0f0` is the already-bounded State dispatcher surface; the observed parent frame `0x22f3ff` is immediately after an indirect State function-object call and stores the returned `eax` into the current State slot.
- `0x21b2e0` scans the node vector header at node `+0x28/+0x30`, compares `(float x, float y)` pairs against zero at `0x21b440..0x21b44f`, appends qualifying indices to a local int vector, and requires at least eight qualifying entries before continuing.
- `0x21b2e0` initializes local selection state, calls `0x21c360` repeatedly to populate candidate state, and calls `0x21c4f0` with `r8d = 0x1f4`.
- `0x21c4f0` runs a bounded loop over the supplied count, invokes callback slots at `+0x30`, compares returned `eax` to the current best at `0x21c59c`, and copies a `0x20`-ish candidate state into the output when the score is lower.
- The callback body labelled at `0x21c080` contains arithmetic over the watched vector pair around `0x21c2ab..0x21c2bf`: it reads the pair lanes, combines them with local scalar state, normalizes by a reciprocal length, compares a threshold at `0x21c2c6`, and increments a count at `0x21c2cf`.

These are static installed-bundle facts. Public semantic names for the state, index vector, candidate state, score, and threshold are not proven by this note.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Observed node-copy call before watch limit | Observed node-copy return before watch limit | Destination pairs admitted | Watchpoints armed | Watchpoint stops |
|---|---|---:|---|---:|---|---|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `0x22a61a` | `0x22a61f` | `3` | `3` | `64` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `0x22a61a` | `0x22a61f` | `3` | `3` | `64` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `0x22a61a` | `0x22a61f` | `3` | `3` | `64` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `0x22a61a` | `0x22a61f` | `3` | `3` | `64` |

The watchpoint hit-count distribution was identical across the admitted quartet:

| Watchpoint ID | Hit count |
|---:|---:|
| `1` | `64` |
| `2` | `0` |
| `3` | `0` |

The watchpoint-hit cap is `64`, so the hit-count rows are capped observations and must not be treated as algorithm constants. Because only watchpoint `1` hit, this proof admits non-copy consumption for at least one representative finite node-destination pair per run, not for every armed pair.

Every admitted run armed all three watchpoints on finite non-sentinel destination pairs. First admitted arm packets:

| Zoom | Copy return | Pair index | First pair at arm |
|---|---|---:|---|
| `28mm` | `0x22a61f` | `0` | `(852.0, 379.0)` |
| `35mm` | `0x22a61f` | `0` | `(1332.0, 215.0)` |
| `70mm` | `0x22a61f` | `0` | `(39.0, 13.0)` |
| `150mm` | `0x22a61f` | `0` | `(1020.0, 594.0)` |

The watchpoint stack groups are identical across all four admitted runs:

| Stop VA | Frame 1 | Frame 2 | Frame 3 | Stops per run | Static role in this proof |
|---:|---:|---:|---:|---:|---|
| `0x21b444` | `0x22a9e7` | `0x22f3ff` | `0x227063` | `1` | first lane positive test in `0x21b2e0` node-vector scan |
| `0x21b44c` | `0x22a9e7` | `0x22f3ff` | `0x227063` | `1` | second lane positive test in `0x21b2e0` node-vector scan |
| `0x21c2b0` | `0x21c59c` | `0x21b639` | `0x22a9e7` | `31` | pair-lane arithmetic inside callback path reached from `0x21c4f0` |
| `0x21c2b6` | `0x21c59c` | `0x21b639` | `0x22a9e7` | `31` | pair-lane arithmetic continuation inside callback path reached from `0x21c4f0` |

Every sampled watchpoint stop preserves a finite non-sentinel pair at the watched address. The first sampled pair values match the first armed pair values shown above for each zoom.

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.copy_pairs_admitted > 0 and .counts.watchpoints_armed == 3 and .counts.watchpoint_hits > 0 and all(.armed[]; .pair_at_arm.both_finite == true and .pair_at_arm.is_sentinel_neg1_neg1 == false) and any(.watchpoint_samples[]; .pair_now.both_finite == true and .pair_now.is_sentinel_neg1_neg1 == false))' runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_28mm.json runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_35mm.json runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_70mm.json runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_150mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_28mm.hdr runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_35mm.hdr runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_70mm.hdr runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. Every admitted run armed three read/write watchpoints on finite non-sentinel coordinate pairs in the destination vector after a same-thread paired `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector copy returned.
3. The installed sibling site `0x22c93a -> 0xe8e70 -> 0x22c93f` had zero observed call/return hits before the admitted watch limit in this proof.
4. In every admitted run, the first armed watchpoint was later hit in `0x21b2e0` through the State-family stack `0x22a9b0 -> 0x22f0f0`; watchpoints `2` and `3` had zero hits before the cap.
5. Runtime stops and static disassembly bind the consumed pair to non-copy work: first to positive-pair/index filtering in `0x21b2e0`, then to callback scoring/selection arithmetic reached through `0x21c4f0`.
6. The admitted static/runtimes facts describe candidate/index/scoring-selection work only. They do not prove public semantic names, image effect, final acceptance/rejection, or reducer closure.

## Safe Conclusion

The `0x22a61a` node-vector destination is not merely a vector-copy propagation endpoint under the canonical bridge HDR quartet. Across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` renders, at least one representative finite non-sentinel coordinate pair copied into that node-vector destination is later read by non-copy candidate/index/scoring-selection code under `0x21b2e0` and its `0x21c4f0` callback path.

This is a meaningful Lane A narrowing: the state-5 coordinate custody trail now reaches non-copy selection/scoring math. It is still not image-effect proof, reducer closure, final acceptance/rejection proof, or proof that the copied coordinates reach final merge-quality policy.

## Consequence For Blocker Work

Lane A can move the state-5 coordinate boundary one hop farther:

`0x2457c0 -> state+0x1e8 -> State-helper 0xe8e70 copy-out -> copied destination vector -> 0xe8e70 node-vector materialization at 0x22a61a -> non-copy 0x21b2e0 / 0x21c4f0 candidate-index-scoring-selection consumer`

The next proof target is still downstream of this scoring/selection boundary: either a demonstrated image-effecting output/candidate-acceptance consequence, a handoff to the already-proven IRAMP/owner output path, or a bounded terminal/non-effect proof for this State-family coordinate-vector route.
