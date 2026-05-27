# LLDB Evidence: LRIS Boundary and 28mm No-LRIS Depth Custody

## Scope

This note records a contamination boundary found in the repo-local
`tools/lri_process` harness and the follow-up no-LRIS reruns for canonical
`28mm` seed `L16_02130`.

It proves:

- `tools/lri_process` historically auto-loaded a same-name `.lris` sidecar when
  one existed beside the input `.lri`.
- Among the canonical quartet paths checked on 2026-05-20, only the `28mm`
  seed has a same-name `.lris` sidecar.
- With LRIS auto-loading disabled, the `28mm` seed still constructs the same
  index-5 `StereoLayer<false>` path and still supplies the previous-layer
  descriptor consumed by the `0x29ed90` depth upsample path.

It does not prove:

- a public LRI/protobuf field origin for the index-5 descriptor
- a public semantic name for the index-5 descriptor
- anything about arbitrary non-canonical LRIs that may have sidecars

## Artifacts

- Harness source with explicit LRIS controls:
  [lri_process.cpp](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process.cpp)
- Build script patched to use the verified installed Lumen.app fallback:
  [build.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/build.sh)
- Constructor probe:
  [stereolayer_constructor_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_constructor_provenance/stereolayer_constructor_probe.py)
- Constructor no-LRIS script:
  [ctor_28mm_no_lris_narrow.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_constructor_provenance/ctor_28mm_no_lris_narrow.lldb)
- Index-5 no-LRIS script:
  [index5_watch_28mm_no_lris.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/index5_watch_28mm_no_lris.lldb)
- Raw constructor outputs:
  `runs/stereolayer_constructor_provenance/ctor_28mm_narrow.json`,
  `runs/stereolayer_constructor_provenance/ctor_28mm_no_lris_narrow.json`
- Raw index-5 output:
  `runs/stereolayer_depth_writer/index5_watch_28mm_no_lris.json`
- Full no-LRIS render outputs:
  `runs/stereolayer_constructor_provenance/ctor_28mm_no_lris_narrow.hdr`,
  `runs/stereolayer_depth_writer/index5_watch_28mm_no_lris.hdr`,
  `runs/stereolayer_depth_writer/no_lris_smoke.hdr`

The redirected raw log
`runs/stereolayer_depth_writer/index5_watch_28mm_no_lris.log` records a failed
LLDB launch with `lost connection` and is not promoted as evidence. The
accepted index-5 no-LRIS evidence is the later successful console run that
wrote `index5_watch_28mm_no_lris.json`.

## Sidecar Boundary

Same-name sidecar check on 2026-05-20:

| Canonical seed | Same-name `.lris` | Size |
|---|---:|---:|
| `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lris` | yes | `10514107` |
| `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lris` | no | n/a |
| `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lris` | no | n/a |
| `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lris` | no | n/a |

The harness behavior was repo-local, not an installed-bundle fact:
`tools/lri_process.cpp` replaced the `.lri` suffix with `.lris` and loaded the
sidecar if the file existed. The harness now has:

- `--no-auto-lris`: keeps explicit `--lris`, but disables same-name sidecar
  discovery
- `--no-lris`: disables both explicit and auto-discovered LRIS loading

Both no-LRIS LLDB scripts in this proof launch with `--no-auto-lris`.

## Constructor Comparison

The narrow constructor probe was run twice against canonical `28mm`
`L16_02130`:

| Run | LRIS state | Process result | `0x26b750` ctor | `0x26bbd0` index setter | `0x26bca0` size setter |
|---|---|---:|---:|---:|---:|
| `ctor_28mm_narrow.json` | auto-loaded sidecar | exited `0` | `6` | `6` | `12` |
| `ctor_28mm_no_lris_narrow.json` | disabled by `--no-auto-lris` | exited `0` | `6` | `6` | `12` |

The final index-5 size-setter sample matches on the fields that matter for the
depth upsample handoff:

| Run | Size arg | Object size | Source vector count | Scale fields | Mode | Scalar |
|---|---|---|---:|---|---:|---:|
| LRIS-assisted | `[2080, 1560, 2080, 1560]` | `2080 x 1560` | `5` | `[200.0, 640000.0]` | `8` | `64` |
| no-LRIS | `[2080, 1560, 2080, 1560]` | `2080 x 1560` | `5` | `[200.0, 640000.0]` | `8` | `64` |

This proves the index-5 `StereoLayer<false>` construction path is not created
only by the 28mm `.lris` sidecar.

## Index-5 Depth Custody No-LRIS Rerun

The no-LRIS index-5 watchpoint probe captured the same critical handoff as the
older 28mm LRIS-assisted probe:

| Field | LRIS-assisted 28mm | no-LRIS 28mm |
|---|---:|---:|
| `0x26bbd0` index setter count | `6` | `6` |
| `0x26bca0` size setter count | `12` | `12` |
| `0x276790` runPass action capped count | `48` | `48` |
| `0x276860` mode-8 worker capped count | `48` | `48` |
| `0x277ccb` mode-8 worker-exit capped count | `48` | `48` |
| `0x26aa30` previous-layer slot call count | `1` | `1` |
| `0x26aa39` after-call count | `1` | `1` |

At `0x26aa39`, the no-LRIS probe records:

- previous object index: `5`
- mode: `8`
- tile: `1`
- object size fields: `+0x2a0/+0x2a4 = 2080 x 1560`
- slot `+0x90` return: `this+0x2a8`
- returned descriptor: `2080 x 1560`, stride `2080`
- first returned float samples:
  `[704.6091918945312, 707.9291381835938, 707.9291381835938, 707.9291381835938]`

The no-LRIS watchpoints also recapture the two descriptor-population phases:

| Phase | Stack | First observed descriptor samples |
|---|---|---|
| initial fill | `0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab <- 0x3fcb86` | `640000.0` repeated |
| later overwrite | `0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab <- 0x3fcb86` | `[704.6091918945312, 707.9291381835938, ...]` |

The no-LRIS index-5 probe wrote a full HDR, had an empty `errors` array, and
captured the required handoff/watchpoint facts. Its LLDB driver ended stopped
at the probe step cap (`drive_hit_step_cap = true`, `process.state = stopped`)
after the render output was written; therefore it is promoted only for the
captured handoff and descriptor-custody facts, not as a clean process-exit
test.

## Result

For canonical `28mm` `L16_02130`, the index-5 depth descriptor custody facts in
[lldb_stereolayer_index5_depth_descriptor_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_stereolayer_index5_depth_descriptor_custody.md)
are not dependent on loading the same-name `.lris` sidecar.

The remaining blocker is narrower: the public LRI/protobuf origin and public
semantic names for this descriptor and the other `0x29ed90` worker inputs are
still unknown.
