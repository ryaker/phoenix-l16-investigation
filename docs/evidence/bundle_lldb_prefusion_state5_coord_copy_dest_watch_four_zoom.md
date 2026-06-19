# Bundle + LLDB Proof: Prefusion State-5 Coordinate Copy-Destination Watch, Four Zooms

## Scope

This note follows the destination vector created by the already-proven `state+0x1e8 -> 0xe8e70` coordinate-vector copy-out path.

The probe stops at the two State-helper `0xe8e70` callsites:

- `0x224e23`, returning at `0x224e28`
- `0x224f03`, returning at `0x224f08`

For call/return pairs observed on the same thread, it scans the destination vector after the copy returns, arms hardware read/write watchpoints on representative finite non-sentinel `(float x, float y)` pairs, and records later watchpoint stops.

This proves only destination-vector custody / propagation under the admitted runs. It does not prove public state names, public target meanings, image contribution, final acceptance/rejection semantics, reducer closure, or final merge quality policy.

Important nuance: the watchpoints are address watches. The destination pairs are finite non-sentinel when armed, but later samples can observe the same watched addresses after mutation or reset to `(-1.0, -1.0)`. The admitted fact is the later copy/materialization custody path, not that every later read/write preserves finite coordinates.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/prefusion_state5_coord_copy_dest_watch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_28mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_35mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/run_four_zoom.sh`
- Aggregate verifier:
  `tools/lldb_probes/prefusion_state5_coord_flow/verify_state5_coord_flow.py`
- Raw output directory:
  `runs/prefusion_state5_coord_copy_dest_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_28mm.json`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_35mm.json`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_70mm.json`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_28mm.hdr`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_35mm.hdr`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_70mm.hdr`
- `runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_150mm.hdr`

The static disassembly capture used for the caller windows is:

- `runs/prefusion_state5_coord_copy_dest_watch/static_disasm.log`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x224e23` | `0x224d70` vector-copy call into `0xe8e70` |
| `0x224e28` | return site after that call, also reachable by the static skip branch |
| `0x224f03` | `0x224e50` vector-copy call into `0xe8e70` |
| `0x224f08` | return site after that call, also reachable by the static skip branch |

The probe only arms destination watchpoints for return-site hits that have a same-thread pending callsite packet. A return-site hit without a pending call is counted separately and is not used as copy evidence.

## Static Anchor

Installed-bundle disassembly shows:

- `0xe8e70` is an 8-byte vector copy helper. It stores copied 32-bit lanes at sites including `0xe8fb0..0xe8fb7`, `0xe8fd0..0xe8ffb`, `0xe9070..0xe9077`, and `0xe9120..0xe9153`.
- `0x224d70` calls `0x245a40`, obtains a source vector through `0x242b90`, and conditionally calls `0xe8e70` at `0x224e23` with destination vector header `object+0x38`.
- `0x224e50` calls `0x245a20`, obtains a source vector through `0x242b90`, and conditionally calls `0xe8e70` at `0x224f03` with destination vector header `object+0x38`.
- `0x22a0e0` calls `0x224e50` at `0x22a4f0`; later in the same body it finds or creates a `0x40`-byte node, initializes node vector header `+0x28`, and conditionally copies `(*r12)+0x38..+0x40` into that node vector at `0x22a61a -> 0xe8e70`.
- `0x22c350` calls `0x224d70` at `0x22c824`; later in the same body it finds or creates a `0x40`-byte node, initializes node vector header `+0x28`, and conditionally copies `(*r12)+0x38..+0x40` into that node vector at `0x22c93a -> 0xe8e70`.
- `0x22f0f0` is the already-bounded State dispatcher surface; the observed parent frame `0x22f3ff` is immediately after an indirect State function-object call and stores the returned `eax` into the current State slot.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Paired copy calls before watch limit | Paired copy return sites before watch limit | Destination pairs admitted | Watchpoints armed | Watchpoint stops |
|---|---|---:|---|---:|---|---|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `0x224f03` | `0x224f08` | `3` | `3` | `64` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `0x224f03` | `0x224f08` | `3` | `3` | `64` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `0x224f03` | `0x224f08` | `3` | `3` | `64` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `0x224e23`, `0x224f03` | `0x224e28`, `0x224f08` | `4` | `3` | `64` |

The watchpoint hit-count distribution was:

| Zoom | Watchpoint hit counts |
|---|---|
| `28mm` | `24`, `22`, `18` |
| `35mm` | `24`, `22`, `18` |
| `70mm` | `26`, `22`, `16` |
| `150mm` | `32`, `20`, `12` |

The watchpoint-hit cap is `64`, so the hit-count rows are capped observations and must not be treated as algorithm constants.

Every admitted run armed all three watchpoints on finite non-sentinel destination pairs. Example admitted arm packets:

| Zoom | Copy return | Pair index | Pair at arm |
|---|---|---:|---|
| `28mm` | `0x224f08` | `684` | `(852.0, 379.0)` |
| `35mm` | `0x224f08` | `128` | `(1332.0, 215.0)` |
| `70mm` | `0x224f08` | `75` | `(1146.0, 13.0)` |
| `150mm` | `0x224f08` | `0` | `(1020.0, 594.0)` |
| `150mm` | `0x224e28` | `4` | `(470.0, 186.0)` |

All admitted watchpoint stops have stack frame `0` inside `0xe8e70`. The immediate caller-frame set across the admitted quartet is:

| Immediate caller frame | Static role in this proof |
|---:|---|
| `0x224e28` | return site after the `0x224d70 -> 0xe8e70` State-helper copy call |
| `0x224f08` | return site after the `0x224e50 -> 0xe8e70` State-helper copy call |
| `0x22a61f` | return site after the `0x22a0e0` node-vector copy call at `0x22a61a -> 0xe8e70` |
| `0x22c93f` | return site after the `0x22c350` node-vector copy call at `0x22c93a -> 0xe8e70` |

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.copy_pairs_admitted > 0 and .counts.watchpoints_armed == 3 and .counts.watchpoint_hits > 0 and all(.armed[]; .pair_at_arm.both_finite == true and .pair_at_arm.is_sentinel_neg1_neg1 == false) and any(.watchpoint_samples[]; .pair_now.both_finite == true and .pair_now.is_sentinel_neg1_neg1 == false))' runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_28mm.json runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_35mm.json runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_70mm.json runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_150mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_28mm.hdr runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_35mm.hdr runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_70mm.hdr runs/prefusion_state5_coord_copy_dest_watch/copy_dest_watch_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. Every admitted run armed three read/write watchpoints on finite non-sentinel coordinate pairs in the destination vector after a same-thread paired State-helper `0xe8e70` copy call returned.
3. In the admitted capped window, `28mm`, `35mm`, and `70mm` armed destination watchpoints from the `0x224e50 -> 0x224f03 -> 0xe8e70 -> 0x224f08` path; `150mm` armed from both `0x224d70 -> 0x224e23 -> 0xe8e70 -> 0x224e28` and `0x224e50 -> 0x224f03 -> 0xe8e70 -> 0x224f08`.
4. Every admitted later watchpoint stop is inside `0xe8e70`.
5. The admitted later watchpoint-stop caller frames are bounded to State-helper recopy sites and two higher node-vector copy/materialization sites at `0x22a61a -> 0xe8e70 -> 0x22a61f` and `0x22c93a -> 0xe8e70 -> 0x22c93f`.
6. The static parent surface for those node-vector copy sites is under the already-bounded State dispatcher family, with observed `0x22f3ff` parent frame after an indirect State function-object call.

## Safe Conclusion

The copied coordinate-vector destination is not terminal at the first State-helper copy-out boundary. Across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders, representative finite destination pairs are touched again by `0xe8e70` vector-copy work, including higher node-vector materialization/copy sites in `0x22a0e0` and `0x22c350`.

This is further coordinate-vector custody / propagation proof. It is not image-effect proof, reducer closure, final acceptance/rejection proof, or proof that these copied coordinates reach final merge-quality policy.

## Consequence For Blocker Work

Lane A can move the state-5 coordinate custody boundary one hop farther:

`0x2457c0 -> state+0x1e8 -> State-helper 0xe8e70 copy-out -> copied destination vector -> additional 0xe8e70 node-vector/materialization copies`

The next proof target is still downstream of these copied vectors: either a non-copy consumer that affects image data / candidate acceptance, or a bounded terminal/non-effect proof for this State-family coordinate-vector route.
