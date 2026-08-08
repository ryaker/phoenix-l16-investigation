# Bundle + LLDB Proof: Prefusion Sentinel `0x20b5e0` Branch-Step Runtime

## Scope

This note follows `bundle_static_prefusion_sentinel_20b5e0_branch_window.md` and replaces its remaining "not direct runtime flags proof" caveat for the sampled `0x20b912` sentinel-read path.

It proves only that, under clean complete canonical four-zoom bridge HDR renders, three watched sentinel-coordinate pairs per focal tier that stop at `0x20b912`:

- still read as `(-1.0, -1.0)` at the watchpoint stop
- step through `0x20b91d` with runtime flags for `jae 0x20ba90`
- step through `0x20baab` with runtime flags for `jbe 0x20bafd`
- do not step into the local `0x20bac0..0x20bac8` update-write block

It does not prove whole-vector terminality, final image effect, source contribution, public acceptance semantics, reducer closure, or final acceptance/rejection.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/prefusion_sentinel_20b5e0_branch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_28mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_35mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_70mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_sentinel_20b5e0_branch/verify_20b5e0_branch.py`
- Raw output directory:
  `runs/prefusion_sentinel_20b5e0_branch/`

The admitted runtime JSON reports are:

- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_28mm.json`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_35mm.json`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_70mm.json`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_150mm.json`

The admitted runs also wrote Radiance HDR outputs:

- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_28mm.hdr`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_35mm.hdr`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_70mm.hdr`
- `runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe avoids the discarded hot direct branch-census strategy. It sets breakpoints only at the already-proven sentinel y-lane store and after-store sites `0x21b92a` / `0x21b930`, arms read/write watchpoints on completed `(-1.0, -1.0)` pairs, and only when a watched pair stops at `0x20b912` does it single-step the stopped thread through the local branch window.

## Static Branch Anchors

The branch-step trace is interpreted against the static window already captured in `runs/prefusion_node_sentinel_downstream_watch/static_disasm_20b5e0_20bc20.log`:

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

| Zoom | LRI | Exit | Step cap | JSON errors | `0x20b912` branch traces | `0x20b91d -> 0x20ba90` | `0x20baab -> 0x20bafd` | `0x20bac0` reached | Watchpoint stops |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `3` | `3` | `0` | `9` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `3` | `3` | `0` | `9` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `3` | `3` | `0` | `40` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `3` | `3` | `3` | `0` | `40` |

Every branch trace has `pair_at_20b912.hex == 000080bf000080bf`.

For every `0x20b91d` trace, the captured flags have `CF = 0` and therefore `jae 0x20ba90` is taken. For every `0x20baab` trace, the captured flags have `CF = 1` and therefore `jbe 0x20bafd` is taken.

## Validation

The repo-local verifier rechecks clean completion, exact branch-step counts,
runtime flags/targets for each sampled trace, absence of local update-write
hits, and Radiance HDR output custody:

```text
$ python3 tools/lldb_probes/prefusion_sentinel_20b5e0_branch/verify_20b5e0_branch.py
28mm: OK 20b912_traces=3 x_to_20ba90=3 output_to_20bafd=3 update_writes=0 watch_hits=9
35mm: OK 20b912_traces=3 x_to_20ba90=3 output_to_20bafd=3 update_writes=0 watch_hits=9
70mm: OK 20b912_traces=3 x_to_20ba90=3 output_to_20bafd=3 update_writes=0 watch_hits=40
150mm: OK 20b912_traces=3 x_to_20ba90=3 output_to_20bafd=3 update_writes=0 watch_hits=40
```

```text
$ file runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_*.hdr
runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_150mm.hdr: Radiance HDR image data
runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_28mm.hdr:  Radiance HDR image data
runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_35mm.hdr:  Radiance HDR image data
runs/prefusion_sentinel_20b5e0_branch/sentinel_20b5e0_branch_70mm.hdr:  Radiance HDR image data
```

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` branch-step runs completed with exit status `0`, no probe errors, no drive step cap, and Radiance HDR outputs.
2. Each admitted run armed three watchpoints on completed sentinel coordinate pairs after `0x21b92a -> 0x21b930`.
3. Each admitted run captured three watched-pair stops at `0x20b912`; every captured pair still read as `(-1.0, -1.0)`.
4. In all twelve admitted `0x20b912` traces, single-stepping reaches `0x20b91d` with runtime flags satisfying the `jae 0x20ba90` branch.
5. In all twelve admitted traces, single-stepping then reaches `0x20baab` with runtime flags satisfying the `jbe 0x20bafd` branch.
6. No admitted trace steps into the local update-write block starting at `0x20bac0`.

## Safe Conclusion

For the sampled `0x20b912` sentinel reads in the admitted canonical four-zoom runs, runtime branch-step evidence now proves the local `0x20b5e0` helper takes the sentinel/nonpositive branch path and skips the local update writes at `0x20bac0..0x20bac8`.

This strengthens the earlier static branch-window proof to a direct runtime flags/branch-target proof for the sampled watched pairs. It remains a local sampled fact, not exhaustive terminality, image-effect proof, source-contribution proof, reducer closure, or final acceptance/rejection.
