# Bundle + LLDB Proof: Prefusion State-5 Coordinate Consumer Watch, Four Zooms

## Scope

This note follows finite coordinate pairs emitted by `0x2457c0` into `state+0x1e8` by arming hardware read-watchpoints on representative finite non-sentinel pairs after `0x2457c0` reaches its normal return path.

It proves only that, under clean complete canonical bridge HDR renders:

- finite non-sentinel pairs emitted into `state+0x1e8` are later read by the `0xe8e70` vector-copy helper
- the immediate copy callers are the two State-helper return sites `0x224e28` and `0x224f08`
- the two caller paths are the already-bounded `0x224d70 -> 0x245a40` path and sibling `0x224e50 -> 0x245a20 -> 0x244560` path
- all four admitted runs complete with exit status `0` and Radiance HDR output

It does not prove public state names, public target meanings, image contribution, final acceptance/rejection semantics, copied-destination downstream effect, or reducer closure.

Important nuance: the watchpoints are address watches. The pairs are finite non-sentinel when armed, but later samples can observe the same watched addresses after reset to `(-1.0, -1.0)`. The admitted fact is the copy/custody path and caller stack, not that every later read still sees finite coordinates.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/prefusion_state5_coord_consumer_watch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/coord_consumer_watch_28mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/coord_consumer_watch_35mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/coord_consumer_watch_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/coord_consumer_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_state5_coord_consumer_watch/run_four_zoom.sh`
- Raw output directory:
  `runs/prefusion_state5_coord_consumer_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_28mm.json`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_35mm.json`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_70mm.json`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_28mm.hdr`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_35mm.hdr`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_70mm.hdr`
- `runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x2459d0` | `0x2457c0` normal return after total-feature-size check |
| `0x245963` | feature-size mismatch branch |
| `0x2459df` | total-feature-size mismatch branch |

At each `0x2459d0` stop, the probe scans `state+0x1e8`, arms read-watchpoints on representative finite non-sentinel pairs, and records later watchpoint stops.

## Static Anchor

Installed-bundle disassembly shows:

- `0x224d70` calls `0x245a40`, then uses `0x242b90` and conditionally calls `0xe8e70`; the return site after the copy is `0x224e28`
- `0x224e50` calls `0x245a20`; `0x245a20` tail-jumps to `0x244560`; the caller then uses `0x242b90` and conditionally calls `0xe8e70`; the return site after the copy is `0x224f08`
- `0xe8e70` is an 8-byte-vector copy helper with explicit paired 32-bit loads and stores, including representative copy sites `0xe8fb0..0xe8fb7`, `0xe8fd0..0xe8ffb`, `0xe9070..0xe9077`, and later same-family copy sites

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | `0x2457c0` returns before watch limit | Watchpoints armed | Watchpoint stops | Immediate caller sites |
|---|---|---:|---|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `3` | `48` | `0x224e28`, `0x224f08` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `3` | `48` | `0x224e28`, `0x224f08` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `3` | `48` | `0x224e28`, `0x224f08` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `4` | `3` | `44` | `0x224e28`, `0x224f08` |

The watchpoint hit-count distribution was:

| Zoom | Watchpoint hit counts |
|---|---|
| `28mm` | `18`, `16`, `14` |
| `35mm` | `18`, `16`, `14` |
| `70mm` | `18`, `16`, `14` |
| `150mm` | `18`, `16`, `10` |

Every admitted watchpoint stop had stack frame `0` inside `___lldb_unnamed_symbol_e8e70` and stack frame `1` at either `0x224e28` or `0x224f08`.

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.return_ok_hits > 0 and .counts.feature_size_mismatch_hits == 0 and .counts.total_features_size_mismatch_hits == 0 and .counts.watchpoints_armed == 3 and .counts.watchpoint_hits > 0 and all(.armed[]; .pair_at_arm.both_finite == true and .pair_at_arm.is_sentinel_neg1_neg1 == false) and any(.watchpoint_samples[]; .pair_now.both_finite == true and .pair_now.is_sentinel_neg1_neg1 == false) and all(.watchpoint_samples[]; .stack[0].function == "___lldb_unnamed_symbol_e8e70" and ((.stack[1].libcp_va == 2248232) or (.stack[1].libcp_va == 2248456))))' runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_28mm.json runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_35mm.json runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_70mm.json runs/prefusion_state5_coord_consumer_watch/coord_consumer_watch_150mm.json
```

The command returned `true`.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. Every admitted run armed three read-watchpoints on finite non-sentinel pairs emitted into `state+0x1e8` after `0x2457c0` normal return.
3. Every admitted run recorded watchpoint stops inside `0xe8e70`.
4. Every admitted watchpoint stop had immediate caller frame `0x224e28` or `0x224f08`.
5. The installed-bundle caller windows bind those caller frames to the `0x224d70 -> 0x245a40` path and the sibling `0x224e50 -> 0x245a20 -> 0x244560` path.

## Safe Conclusion

Finite coordinate pairs emitted by `0x2457c0` into `state+0x1e8` are not dead at the helper boundary. Across the canonical four-zoom bridge HDR quartet, representative finite pairs are read by `0xe8e70` vector-copy work under both State-helper copy-out paths:

`0x224d70 -> 0x245a40 -> 0x2457c0 -> state+0x1e8 -> 0xe8e70`

`0x224e50 -> 0x245a20 -> 0x244560 -> 0x2457c0 -> state+0x1e8 -> 0xe8e70`

This is coordinate-vector custody / copy-out proof, not image-effect proof and not reducer closure.

## Consequence For Blocker Work

Lane A can now treat the first downstream consumer of `state+0x1e8` as bounded through four-zoom runtime: it is copied out by `0xe8e70` under the State-helper output-copy paths.

The next proof target is the destination vector copied by `0xe8e70`: whether that copied coordinate-vector payload reaches image-effecting work, final acceptance/rejection policy, or another bounded non-reducer helper.
