# Bundle + LLDB Proof: Prefusion State-5 Coordinate Output, Four Zooms

## Scope

This note bounds the `0x2457c0` coordinate-output helper reached from the `0x244560` prefusion heavy-consumer family.

It proves only that, under clean complete canonical bridge HDR renders:

- `0x2457c0` is live and returns normally at `28mm`, `35mm`, `70mm`, and `150mm`
- sampled runtime hits at the admitted store-path site `0x24593b` have `record+0x24 == 5`
- each admitted `0x2457c0` return leaves `state+0x1e8` populated with finite non-sentinel coordinate pairs
- all four admitted runs complete with exit status `0` and Radiance HDR output

It does not prove public state names, public target meanings, image contribution, final acceptance/rejection semantics, or reducer closure.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_state5_coord_output/prefusion_state5_coord_output_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_state5_coord_output/state5_coord_output_28mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_output/state5_coord_output_35mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_output/state5_coord_output_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_coord_output/state5_coord_output_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_state5_coord_output/run_four_zoom.sh`
- Raw output directory:
  `runs/prefusion_state5_coord_output/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_coord_output/state5_coord_output_28mm.json`
- `runs/prefusion_state5_coord_output/state5_coord_output_35mm.json`
- `runs/prefusion_state5_coord_output/state5_coord_output_70mm.json`
- `runs/prefusion_state5_coord_output/state5_coord_output_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_state5_coord_output/state5_coord_output_28mm.hdr`
- `runs/prefusion_state5_coord_output/state5_coord_output_35mm.hdr`
- `runs/prefusion_state5_coord_output/state5_coord_output_70mm.hdr`
- `runs/prefusion_state5_coord_output/state5_coord_output_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets breakpoints at:

| VA | Role |
|---:|---|
| `0x2457c0` | `0x2457c0` entry |
| `0x24593b` | state-5 store path, before first coordinate write |
| `0x2459d0` | normal return after total-feature-size check |
| `0x245963` | feature-size mismatch branch |
| `0x2459df` | total-feature-size mismatch branch |

The store-path breakpoint is capped at `64` samples per run to limit debugger perturbation. Therefore the store-path hit and target counts are samples only, not total algorithm counts.

## Static Anchor

Installed-bundle disassembly of `0x2457c0` shows:

- `0x2457d4` selects the output vector header at `state+0x1e8`
- `0x245870` fills that output vector with qword `0xBF800000BF800000`, the float pair `(-1.0, -1.0)`
- `0x245890..0x24595b` walks three levels
- `0x245920` checks `record+0x24 == 5`
- `0x24593b` and `0x245941` write scaled coordinate floats into `state+0x1e8`
- `0x2459d0` is the normal return path after the total-feature-size check

Instrumentation correction:

- The first attempted post-store site `0x245948` is also the branch target for records that fail the state-5 check, so it is not admissible as store-path proof.
- The admitted probe uses `0x24593b`, which is inside the state-5 store path.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Entry hits | Normal returns | Sampled `0x24593b` hits | Sampled targets | Return vector pair count | Return finite non-sentinel range |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `9` | `9` | `64` | `target 2: 64` | `6832` | `39..669` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `9` | `9` | `64` | `target 2: 64` | `5993` | `32..1620` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `9` | `9` | `64` | `target 1: 64` | `6503` | `69..2745` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `8` | `8` | `64` | `target 1: 64` | `2399` | `79..1241` |

All sampled `0x24593b` hits have `record+0x24 == 5`.

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.entry_hits > 0 and .counts.return_ok_hits > 0 and .counts.feature_size_mismatch_hits == 0 and .counts.total_features_size_mismatch_hits == 0 and (.return_summaries|length) == .counts.return_ok_hits and all(.return_summaries[]; .return_output_vector.finite_non_sentinel > 0 and .return_output_vector.pairs_truncated == false) and all(.state5_store_path_samples[]; .record.state_0x24 == 5))' runs/prefusion_state5_coord_output/state5_coord_output_28mm.json runs/prefusion_state5_coord_output/state5_coord_output_35mm.json runs/prefusion_state5_coord_output/state5_coord_output_70mm.json runs/prefusion_state5_coord_output/state5_coord_output_150mm.json
```

The command returned `true`.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit status `0`, no probe errors, no step cap, and Radiance HDR output files.
2. The admitted runs reached `0x2457c0` and returned normally through `0x2459d0`.
3. No admitted run hit the `0x245963` feature-size mismatch breakpoint or the `0x2459df` total-feature-size mismatch breakpoint.
4. Every admitted sampled `0x24593b` store-path packet reads `record+0x24 == 5`.
5. Every admitted `0x2457c0` normal return has at least one finite non-sentinel coordinate pair in `state+0x1e8`, with no output-vector scan truncation.

## Safe Conclusion

`0x2457c0` is a live four-zoom state-5 coordinate-output materialization helper. It clears `state+0x1e8` to `(-1.0, -1.0)`, sampled admitted store-path packets all decode with `record+0x24 == 5`, and every admitted return leaves finite non-sentinel coordinate pairs in the output vector.

This is coordinate-output materialization proof, not image-effect proof and not reducer closure.

## Consequence For Blocker Work

Lane A can now treat `0x2457c0` as bounded through four-zoom runtime:

`0x244560 -> 0x2457c0 -> state+0x1e8 coordinate vector`

The next proof target is the downstream consumer of `state+0x1e8` after `0x2457c0` returns, and whether that consumer reaches image-effecting work, final acceptance/rejection policy, or another bounded non-reducer helper.
