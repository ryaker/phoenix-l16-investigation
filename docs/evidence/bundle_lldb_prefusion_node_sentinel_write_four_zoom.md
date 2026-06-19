# Bundle + LLDB Proof: Prefusion Node Coordinate Sentinel Writes, Four Zooms

## Scope

This note follows the non-copy consumer bounded in `bundle_lldb_prefusion_state5_coord_node_dest_watch_four_zoom.md`.

Static inspection of `0x21b2e0` shows that after the `0x21c4f0` candidate/index/scoring-selection path, the same body can overwrite coordinate-pair lanes with the float sentinel `-1.0`:

- `0x21b923`: `movl $0xbf800000, (%rax,%rdx,8)`
- `0x21b92a`: `movl $0xbf800000, (%rcx)`

The runtime probe sets breakpoints at those two store instructions, records the pair before the x-lane store, records the pair between the x-lane and y-lane stores, and verifies clean output completion.

This proves only that the sentinel coordinate-invalidating store path is live under the admitted canonical bridge HDR runs. It does not prove public state names, final image contribution, merge/reducer closure, final acceptance/rejection semantics, or final merge-quality policy.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_node_sentinel_write/prefusion_node_sentinel_write_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_node_sentinel_write/node_sentinel_write_28mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_write/node_sentinel_write_35mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_write/node_sentinel_write_70mm.lldb`
  `tools/lldb_probes/prefusion_node_sentinel_write/node_sentinel_write_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_sentinel_write/run_four_zoom.sh`
- Aggregate verifier:
  `tools/lldb_probes/prefusion_node_sentinel_flow/verify_node_sentinel_flow.py`
- Raw output directory:
  `runs/prefusion_node_sentinel_write/`

The admitted runtime JSON reports are:

- `runs/prefusion_node_sentinel_write/node_sentinel_write_28mm.json`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_35mm.json`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_70mm.json`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_node_sentinel_write/node_sentinel_write_28mm.hdr`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_35mm.hdr`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_70mm.hdr`
- `runs/prefusion_node_sentinel_write/node_sentinel_write_150mm.hdr`

The static disassembly capture is:

- `runs/prefusion_node_sentinel_write/static_disasm.log`

Only the four clean JSON/HDR runs and the static disassembly log are admitted by this note. Earlier failed launch attempts in this raw-output directory are not evidence for or against the claim.

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x21b923` | first sentinel store, x lane |
| `0x21b92a` | second sentinel store, y lane |

## Static Anchor

Installed-bundle disassembly shows:

- `0x22a9b0` calls `0x21b2e0` at `0x22a9e2`; the already admitted node-destination watch reached `0x21b2e0` through this State-family body.
- `0x21b2e0` calls `0x21c4f0` with `r8d = 0x1f4`; `0x21c4f0` runs callback-driven candidate/index/scoring-selection work and copies the best candidate state into its output.
- After `0x21c4f0`, `0x21b2e0` calls `0x21ccb0` with the selected candidate state and `state+0xa00`; `0x21ccb0` allocates/populates a three-float-per-entry transformed vector through scalar multiply/add rows.
- `0x21b2e0` then loops over the earlier positive-pair index vector. For each index, it reads three floats from the transformed vector, finds or creates the matching node, computes a normalized scalar test against the current node-vector coordinate pair, and can reach the sentinel write block.
- At `0x21b923` and `0x21b92a`, the code writes raw bits `0xbf800000`, which is binary32 `-1.0`, into the two lanes of the coordinate pair.

Public semantic names for the candidate state, transformed vector, scalar test, and sentinel meaning are not proven by this note. The safe description is "coordinate-pair sentinel invalidation/write path."

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | `0x21b923` hits | `0x21b92a` hits | Hit cap reached | First pre-store pair | First mid-store pair at `0x21b92a` |
|---|---|---:|---|---:|---:|---:|---|---|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `152` | `152` | no | `(852.0, 379.0)` | `(-1.0, 379.0)` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `255` | `255` | no | `(185.0, 1307.0)` | `(-1.0, 1307.0)` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `512` | `512` | yes | `(888.0, 386.0)` | `(-1.0, 386.0)` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `2` | `2` | no | `(1892.0, 624.0)` | `(-1.0, 624.0)` |

The hit cap was `512`, so the `70mm` hit count is capped and must not be treated as an algorithm constant. The other three admitted counts are evidence-run counts, not public constants.

For every admitted run:

- `store_x_pre_finite_non_sentinel == store_x_hits`
- `store_y_mid_x_is_sentinel == store_y_hits`
- every sampled x-store pre-pair is finite and not `(-1.0, -1.0)`
- every sampled y-store mid-pair has x already equal to `-1.0`

Representative first store stacks:

| Zoom | Store-stack shape |
|---|---|
| `28mm` | `0x21b923 -> 0x22a9e7 -> 0x22f3ff -> 0x227063` |
| `35mm` | `0x21b923 -> 0x22a9e7 -> 0x22f3ff -> 0x227063` |
| `70mm` | `0x21b923 -> 0x22a9e7 -> 0x22f3ff -> 0x227063` |
| `150mm` | one sample through `0x22a9e7 -> 0x22f3ff -> 0x227063`; one sample through `0x22cd52 -> 0x22f3ff -> 0x2277b8` |

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.store_x_hits > 0 and .counts.store_y_hits > 0 and .counts.store_x_pre_finite_non_sentinel > 0 and .counts.store_y_mid_x_is_sentinel > 0 and (.store_x_samples|length > 0) and (.store_y_samples|length > 0) and all(.store_x_samples[]; .pair_before_store.both_finite == true and .pair_before_store.is_sentinel_neg1_neg1 == false) and all(.store_y_samples[]; .pair_mid_store.x_is_sentinel == true))' runs/prefusion_node_sentinel_write/node_sentinel_write_28mm.json runs/prefusion_node_sentinel_write/node_sentinel_write_35mm.json runs/prefusion_node_sentinel_write/node_sentinel_write_70mm.json runs/prefusion_node_sentinel_write/node_sentinel_write_150mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_node_sentinel_write/node_sentinel_write_28mm.hdr runs/prefusion_node_sentinel_write/node_sentinel_write_35mm.hdr runs/prefusion_node_sentinel_write/node_sentinel_write_70mm.hdr runs/prefusion_node_sentinel_write/node_sentinel_write_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. Both sentinel store instructions at `0x21b923` and `0x21b92a` are live under all four admitted runs.
3. Every sampled pre-store pair at `0x21b923` is finite and not already `(-1.0, -1.0)`.
4. Every sampled mid-store pair at `0x21b92a` has x already changed to `-1.0` while y still holds its prior finite value.
5. Static disassembly proves the next instruction at `0x21b92a` writes the same `0xbf800000` sentinel bits into y.
6. The admitted runtime/static facts prove a live coordinate-pair sentinel invalidation/write path downstream of `0x21b2e0` / `0x21c4f0`; they do not prove final image effect, final acceptance/rejection semantics, or reducer closure.

## Safe Conclusion

The non-copy `0x21b2e0` candidate/index/scoring-selection path is now proven to have a concrete coordinate-pair invalidation effect: it writes `(-1.0, -1.0)` sentinel coordinates into selected node-vector entries across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders.

This is stronger than generic "scoring" or "copy custody," but it is still not final merge-quality policy. The safe implementation consequence is that any clean-room replacement likely needs an equivalent candidate-coordinate rejection/invalidation stage before claiming parity, but the downstream image/effect and public acceptance semantics remain open.

## Consequence For Blocker Work

Lane A can move the state-5 coordinate boundary one hop farther:

`0x2457c0 -> state+0x1e8 -> State-helper 0xe8e70 copy-out -> copied destination vector -> 0xe8e70 node-vector materialization at 0x22a61a -> 0x21b2e0 / 0x21c4f0 candidate-index-scoring-selection consumer -> 0x21b923 / 0x21b92a coordinate sentinel invalidation writes`

The next proof target is downstream of the invalidated node-vector entries: prove whether these sentinel-marked coordinates affect candidate acceptance, source contribution, an IRAMP/owner output handoff, or are terminal/non-effecting under the tested bridge HDR path.
