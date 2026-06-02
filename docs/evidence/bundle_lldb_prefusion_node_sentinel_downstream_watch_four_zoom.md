# Bundle + LLDB Proof: Prefusion Node Sentinel Downstream Touches, Four Zooms

## Scope

This note follows the sentinel coordinate writes proven in `bundle_lldb_prefusion_node_sentinel_write_four_zoom.md`.

The probe records the y-lane sentinel store at `0x21b92a`, breaks at the next instruction `0x21b930`, verifies that the full pair now reads `(-1.0, -1.0)`, arms hardware read/write watchpoints on those completed sentinel pairs, and lets the render continue.

This proves only that selected sentinel-marked node-vector coordinate pairs are touched later by downstream code under the admitted canonical bridge HDR runs. It does not prove public state names, final image contribution, final merge-quality policy, reducer closure, or final acceptance/rejection semantics.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/prefusion_node_sentinel_downstream_watch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/run_four_zoom.sh`
- Raw output directory:
  `runs/prefusion_node_sentinel_downstream_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.hdr`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.hdr`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.hdr`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.hdr`

Static disassembly captures used for this note:

- `runs/prefusion_node_sentinel_downstream_watch/static_disasm_e0ae0.log`
- `runs/prefusion_node_sentinel_downstream_watch/static_disasm_216f60.log`
- `runs/prefusion_node_sentinel_downstream_watch/static_disasm_218b30_218f90.log`
- `runs/prefusion_node_sentinel_downstream_watch/static_disasm_20ada0_20b940.log`
- `runs/prefusion_node_sentinel_downstream_watch/static_disasm_22acb0_22aec0.log`

Only the four clean JSON/HDR runs and the static disassembly logs above are admitted by this note. A parallel `70mm` launch attempt stopped at the known instrumentation-sensitive `0x2e8cc0` `EXC_BAD_ACCESS` family and was killed; it is not evidence for or against this claim. The admitted `70mm` proof is the later standalone rerun that completed cleanly.

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x21b92a` | second sentinel store, y lane |
| `0x21b930` | first instruction after the y-lane store |

At `0x21b930`, the probe only arms a watchpoint if the pair reads exactly `(-1.0, -1.0)`.

## Static Anchor

Installed-bundle disassembly shows:

- `0x21b92a` writes raw bits `0xbf800000` into the y lane of the pair, and the next instruction is `0x21b930`.
- Watchpoint stops in `0xe0ae0` are inside a 32-byte chunk copy loop. The sampled stops are on stores such as `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, and `0xe0bdb`; under the observed stacks, the caller is the State-family path through `0x20adf1` / `0x20adf6` and `0x22ae6e` / `0x22ae73`.
- Watchpoint stops around `0x216f60` are inside vector scan/count work over coordinate-like float pairs. The sampled stops include packed float loads / comparisons at `0x217035`, `0x21703a`, `0x217048`, `0x21704f`, `0x217064`, `0x21706a`, `0x2170b7`, and `0x2170bd`, with parent stack `0x22acfa -> 0x22f3ff -> 0x227063`.
- Watchpoint stops around `0x218b30` are inside a scoring/materialization loop. The sampled stop PC `0x218bc4` is immediately after a memory comparison at `0x218bc0`; the same body later writes a scalar at `0x218f88`, and the observed parent stack is `0x218f81 -> 0x5f5e -> 0x4f83 -> 0x280e`.
- Watchpoint stop `0x20b912` is inside body `0x20ada0` after the caller has copied a record with `0xe0ae0`; the local code reads coordinate pairs, loads sentinel literal `0xbf800000`, and branches through coordinate tests / fallback output assembly.

Public semantic names for these structures are not proven by this note. The safe descriptions are downstream copy/record propagation, coordinate scan/count, and scoring/materialization surfaces.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Sentinel pairs armed | Sampled watchpoint stops | Watchpoint hit counts | First sampled downstream stack class |
|---|---|---:|---|---:|---:|---:|---|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `64` | `135 / 129 / 129` | `0xe0ae0` copy loop via `0x20adf6 -> 0x22ae73` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `64` | `121 / 117 / 107` | `0xe0ae0` copy loop via `0x20adf6 -> 0x22ae73` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `64` | `52 / 52 / 49` | `0x216f60` coordinate scan/count via `0x22acfa` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `3` | `65` | `116 / 127 / 1` | `0x216f60` coordinate scan/count via `0x22acfa` |

The watchpoint hit counts and sampled-stop counts are instrumentation counts only. They are capped / sampled observations and must not be treated as algorithm constants.

Every admitted watchpoint was armed on bytes:

`000080bf000080bf`

That is two binary32 `-1.0` values in little-endian order.

For every admitted sampled watchpoint stop across all four runs:

- the watched pair still read as `(-1.0, -1.0)`
- both lanes still had raw bits `0xbf800000`
- the process completed with exit status `0`
- the output file was Radiance HDR

Sampled downstream VA coverage:

| Zoom | Sampled downstream VAs |
|---|---|
| `28mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0x20b912` |
| `35mm` | `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, `0xe0bdb`, `0x20b912` |
| `70mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, `0xe0bdb`, `0x20b912`, `0x217035`, `0x21703a`, `0x217048`, `0x21704f`, `0x217064`, `0x21706a`, `0x218bc4` |
| `150mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bd5`, `0xe0bdb`, `0x20b912`, `0x21704f`, `0x21706a`, `0x2170b7`, `0x2170bd`, `0x218bc4` |

This table is sampled coverage only, not exhaustive full-render touch coverage.

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.store_y_hits >= .counts.watchpoints_armed and .counts.after_store_pair_is_sentinel >= .counts.watchpoints_armed and .counts.watchpoints_armed > 0 and .counts.watchpoint_hits > 0 and all(.armed[]; .pair_at_arm.is_sentinel_neg1_neg1 == true) and all(.watchpoint_samples[]; .pair_now.is_sentinel_neg1_neg1 == true))' runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.hdr runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. In every admitted run, at least one complete `(-1.0, -1.0)` coordinate pair was watchpoint-armed immediately after the `0x21b92a` y-lane sentinel store.
3. In every admitted run, those sentinel-marked pairs were touched later by downstream code.
4. Every sampled later touch still observed the watched pair as `(-1.0, -1.0)`.
5. The sampled downstream touches include State-family copy/record propagation and coordinate scan/scoring/materialization surfaces as stated above.
6. This is downstream sentinel-coordinate custody / consumption proof only. It does not prove final image effect, source contribution, reducer closure, or final acceptance/rejection semantics.

## Safe Conclusion

Selected `0x21b923` / `0x21b92a` sentinel-marked node-vector coordinate pairs are not terminal at the write site under the canonical bridge HDR quartet. They are later copied/read by downstream State-family code across clean `28mm`, `35mm`, `70mm`, and `150mm` renders, and all sampled later touches preserve the `(-1.0, -1.0)` value.

This moves Lane A one hop farther, but it still does not tell us whether the sentinel-marked entries alter final source acceptance, image contribution, or merge-quality suppression.

## Consequence For Blocker Work

Lane A can move the boundary from "sentinel invalidation write" to "sentinel-marked coordinate downstream custody / sampled consumption":

`0x2457c0 -> state+0x1e8 -> State-helper 0xe8e70 copy-out -> copied destination vector -> 0xe8e70 node-vector materialization at 0x22a61a -> 0x21b2e0 / 0x21c4f0 candidate-index-scoring-selection consumer -> 0x21b923 / 0x21b92a coordinate sentinel invalidation writes -> downstream sentinel-coordinate copy / scan / scoring-materialization touches`

The next proof target is whether those sentinel-marked coordinate touches reach image-source contribution decisions, IRAMP/owner output handoff, final acceptance/rejection policy, or a bounded non-image-effect terminal path.
