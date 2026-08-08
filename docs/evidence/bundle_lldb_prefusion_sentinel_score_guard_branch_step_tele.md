# Bundle + LLDB Proof: Prefusion Sentinel Score-Guard Branch-Step, Tele Samples

## Scope

This note follows
`bundle_lldb_prefusion_sentinel_score_guard_tele.md` and replaces the remaining
"skip by flags" inference for selected tele samples with direct single-step
runtime branch-target proof.

It proves only that, under clean complete canonical tele bridge HDR renders,
watched sentinel-coordinate pairs that stop at the `0x218b30` scoring /
materialization guard:

- still read as `(-1.0, -1.0)` at `0x218bc4`
- have runtime flags for the static `jae 0x218cb8` branch
- single-step directly from `0x218bc4` to `0x218cb8`

It does not prove whole-vector terminality, all sentinel entries, final image
contribution, semantic `src1` / `src2` contents, reducer closure, or final
acceptance / rejection semantics.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_sentinel_score_guard/prefusion_sentinel_score_guard_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_branch_70mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_branch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_sentinel_score_guard/run_tele_branch_step.sh`
- Verifier:
  `tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard_branch_step.py`
- Raw output directory:
  `runs/prefusion_sentinel_score_guard_branch_step/`

The admitted runtime JSON reports are:

- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_70mm.json`
- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_150mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_70mm.hdr`
- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe uses the same hardware-watchpoint strategy as the prior score-guard
evidence: it arms read/write watchpoints only after a completed y-lane sentinel
store at `0x21b92a -> 0x21b930` leaves the full pair as `(-1.0, -1.0)`.

The new branch-step mode is disabled by default for the older score-guard
scripts. These tele scripts enable it and stop after a bounded number of branch
traces, then disable watchpoints so the render can finish.

## Static Guard Anchor

Installed-bundle disassembly of `0x218b30` shows:

```asm
0x218bc0: ucomiss (%rdx,%rbx,8), %xmm0
0x218bc4: jae    0x218cb8
0x218bca: movss  0x4(%rdx,%rbx,8), %xmm3
0x218bd0: ucomiss %xmm0, %xmm3
0x218bd3: jbe    0x218cb8
```

Therefore a direct step from `0x218bc4` to `0x218cb8` proves the local loop
skips the y-lane read and the scoring/materialization body for that sample.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Watchpoints armed | Watchpoint stops | Guard branch traces | `0x218bc4 -> 0x218cb8` | Not-to-skip traces |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `12` | `6` | `6` | `0` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `3` | `3117` | `3` | `3` | `0` |

Every admitted branch trace has:

- `pair_at_branch.hex == 000080bf000080bf`
- `CF = 0`, `PF = 0`, `ZF = 0`
- `jae_taken = true`
- `branch_step.before == 0x218bc4`
- `branch_step.after == 0x218cb8`

The different branch-trace counts are probe caps, not algorithm constants.

## Validation

```text
$ python3 tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard_branch_step.py
70mm: OK branch_traces=6 guard_hits=6 to_skip=6 watch_hits=12
150mm: OK branch_traces=3 guard_hits=3 to_skip=3 watch_hits=3117
```

The verifier rechecks clean completion, no drive step cap, no probe errors,
Radiance HDR output custody, exact admitted counts, still-sentinel branch
operands, runtime flags, and direct branch-step targets.

The older score-guard verifier still passes with the default no-branch-step
mode:

```text
$ python3 tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard.py
28mm: OK main guard_hits=0 skip_by_flags=0
35mm: OK main guard_hits=0 skip_by_flags=0
70mm: OK main guard_hits=26 skip_by_flags=26
150mm: OK main guard_hits=24 skip_by_flags=24
28mm: OK skip3 watched_pairs=3 guard_hits=0
35mm: OK skip3 watched_pairs=3 guard_hits=0
28mm: OK count_only completed_sentinels=152
35mm: OK count_only completed_sentinels=106
```

## Proven Facts

1. The admitted `70mm` branch-step run completed with exit status `0`, no probe
   errors, no drive step cap, and a Radiance HDR output.
2. The admitted `150mm` branch-step run completed with exit status `0`, no
   probe errors, no drive step cap, and a Radiance HDR output.
3. In the admitted `70mm` run, six watched sentinel pairs stopped at `0x218bc4`
   and single-stepped directly to `0x218cb8`.
4. In the admitted `150mm` run, three watched sentinel pairs stopped at
   `0x218bc4` and single-stepped directly to `0x218cb8`.
5. No admitted branch-step trace reaches the y-lane read at `0x218bca` or the
   local scoring/materialization body behind the positive-coordinate guard.

## Safe Conclusion

For the admitted tele samples, the `0x218b30` score/materialization guard does
not merely have flags consistent with a skip. Runtime single-step proof shows
the watched sentinel pairs actually branch from `0x218bc4` to `0x218cb8`,
bypassing the guarded y-lane/body work.

This is still sampled local guard proof. It does not prove all sentinel entries,
whole-vector terminality, image-level source contribution, reducer closure, or
final acceptance / rejection.
