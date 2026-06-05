# LLDB Proof: Final-Compositing Post-Gather Switch Census Across Four Zooms

## Scope

This proof follows the four-zoom queue/drain liveness proof by censusing the
post-gather switch inside `0x3bca90` under the canonical bridge-HDR CLI path.

It proves only tested-path switch/case liveness for:

- switch record-type load `0x3bce59`;
- jump-table case targets for record types `0..16`;
- invalid `>16` target `0x3be8e7`;
- orchestrator drain call-edge `0x3bcc51 -> 0x3bfe60` as a batch marker.

It does not prove public record semantics, final sink, byte-level copy-vs-blend,
anti-ghosting policy, or final merge acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_switch_census/switch_census_probe.py`
- `tools/lldb_probes/codex_final_compositing_switch_census/switch_census_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_switch_census/switch_census_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_switch_census/switch_census_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_switch_census/switch_census_150mm.lldb`
- `tools/lldb_probes/codex_final_compositing_switch_census/run_four_zoom.sh`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_switch_census/switch_census_28mm.json`
- `runs/codex_final_compositing_switch_census/switch_census_35mm.json`
- `runs/codex_final_compositing_switch_census/switch_census_70mm.json`
- `runs/codex_final_compositing_switch_census/switch_census_150mm.json`
- matching `.log` and `.hdr` files in the same directory

## Inputs

All runs used the same installed x86_64 binary/framework set and the canonical
four LRIs:

| Zoom | LRI |
|---|---|
| `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Each launch passed `--profile 3 --export-fmt 3 --no-auto-lris` and completed a
`10432x7824` HDR write.

## Static Jump Table

The switch at `0x3bce59..0x3bce75` loads the record type from `(%r13)`, rejects
values above `16`, and dispatches through the 17-entry jump table at `0x3bf2ac`.

| Case | Target |
|---:|---|
| 0 | `0x3be5ce` |
| 1 | `0x3bce77` |
| 2 | `0x3bd308` |
| 3 | `0x3bcee3` |
| 4 | `0x3bcf20` |
| 5 | `0x3bd1c1` |
| 6 | `0x3bd327` |
| 7 | `0x3bd24f` |
| 8 | `0x3bd27b` |
| 9 | `0x3bd334` |
| 10 | `0x3bceb2` |
| 11 | `0x3bd453` |
| 12 | `0x3bd360` |
| 13 | `0x3bd482` |
| 14 | `0x3be60e` |
| 15 | `0x3be8a6` |
| 16 | `0x3bd2f7` |

## Runtime Results

All four runs exited normally with no probe errors, no case/type mismatches, and
no step-cap hits.

| Zoom | Switch records | Case 1 | Case 2 | Case 3 | Case 11 | Case 16 | Case 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | 11 | 1 | 1 | 1 | 7 | 1 | 0 |
| `35mm` | 11 | 1 | 1 | 1 | 7 | 1 | 0 |
| `70mm` | 10 | 1 | 1 | 1 | 6 | 1 | 0 |
| `150mm` | 10 | 1 | 1 | 1 | 6 | 1 | 0 |

No other jump-table case target recorded a hit under these admitted runs, and
the invalid `>16` target `0x3be8e7` also recorded zero hits.

## Important Correction

The static branch beginning at case `4` target `0x3bcf20` contains the
ImagePyramid/per-tile-dispatch sequence previously highlighted in the static
queue/drain packet:

- `0x3bcf8d` `CIAPI::ImagePyramid` construction;
- `0x3bd05d` indirect call;
- adjacent Image width/height/stride/data accessor work.

This proof records zero case-`4` hits on the canonical `28mm`, `35mm`, `70mm`,
and `150mm` CLI bridge-HDR runs. Therefore, that branch is statically present,
but it is not runtime-proven for this tested path.

## Proven Facts

- The post-gather switch at `0x3bce59` is live across the canonical four-zoom
  CLI bridge-HDR quartet.
- Under these runs, the only observed record types / case targets are `1`, `2`,
  `3`, `11`, and `16`.
- The case target reached by each observed record type matches the static jump
  table; no case/type mismatches were recorded.
- Case `4` / target `0x3bcf20`, which contains the previously highlighted
  ImagePyramid/per-tile-dispatch branch, has zero hits under the tested runs.

## Non-Claims

- Zero case-`4` hits are scoped to the tested CLI bridge-HDR runs; this is not a
  universal "never fires" claim for every Lumen render/export path.
- This proof does not identify final output sink or display/file handoff.
- This proof does not prove byte-level copy-vs-blend behavior.
- This proof does not prove final output semantics, anti-ghosting policy, or
  final merge acceptance/rejection.
