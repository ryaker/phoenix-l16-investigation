# Bundle + LLDB Proof: Prefusion Sentinel Score-Guard Skip, Tele Samples

## Scope

This note follows the sentinel-coordinate downstream-custody proof in
`bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md`.

The probe uses the same stable hardware-watchpoint strategy: it observes the
completed y-lane sentinel store at `0x21b92a -> 0x21b930`, arms read/write
watchpoints only after the full coordinate pair reads `(-1.0, -1.0)`, then
records later watchpoint stops. This follow-up adds one classification: when a
watched sentinel pair stops at `0x218bc4`, the probe records the flags produced
by the immediately preceding `ucomiss` and checks whether the static
`jae 0x218cb8` skip is taken.

This proves only the sampled guard behavior described below. It does not prove
whole-vector terminality, all sentinel entries, final image contribution,
semantic `src1` / `src2` contents, reducer closure, or final acceptance /
rejection semantics.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_sentinel_score_guard/prefusion_sentinel_score_guard_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_28mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_35mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_70mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_150mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_count.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_count.lldb`
- Runner:
  `tools/lldb_probes/prefusion_sentinel_score_guard/run_four_zoom.sh`
  `tools/lldb_probes/prefusion_sentinel_score_guard/run_wide_skip3.sh`
  `tools/lldb_probes/prefusion_sentinel_score_guard/run_wide_count.sh`
- Raw output directory:
  `runs/prefusion_sentinel_score_guard/`

The admitted runtime JSON reports are:

- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_70mm.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_150mm.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_count.json`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_count.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_70mm.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_150mm.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_count.hdr`
- `runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_count.hdr`

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

At `0x21b930`, the probe arms a watchpoint only if the full pair reads exactly
`(-1.0, -1.0)`. Each admitted run arms three such watchpoints. The watchpoint
cap is `512`, so all conclusions about later touches are sampled / capped
observations.

## Static Guard Anchor

Installed-bundle disassembly of `0x218b30` shows the relevant loop guard:

```asm
0x218b77: movq   (%r15), %rdx
0x218b7a: xorps  %xmm0, %xmm0
...
0x218bc0: ucomiss (%rdx,%rbx,8), %xmm0
0x218bc4: jae    0x218cb8
0x218bca: movss  0x4(%rdx,%rbx,8), %xmm3
0x218bd0: ucomiss %xmm0, %xmm3
0x218bd3: jbe    0x218cb8
```

Therefore a watched stop at `0x218bc4` is immediately after comparing zero
against the x lane of the coordinate pair. Runtime flags with `CF = 0` make the
static `jae 0x218cb8` branch taken, skipping the body that begins with the y
lane read at `0x218bca`.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Watchpoints armed | Watchpoint samples | Guard samples at `0x218bc4` | Guard skip-by-flags | Guard non-skip-by-flags |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `512` | `0` | `0` | `0` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `512` | `0` | `0` | `0` |
| `70mm` | `L16_03434` | `0` | `false` | `0` | `3` | `512` | `26` | `26` | `0` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `3` | `512` | `24` | `24` | `0` |

Sampled downstream VA coverage:

| Zoom | Sampled downstream VAs |
|---|---|
| `28mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0x20b912` |
| `35mm` | `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, `0xe0bdb`, `0x20b912` |
| `70mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, `0xe0bdb`, `0x20b912`, `0x217035`, `0x21703a`, `0x217048`, `0x21704f`, `0x217064`, `0x21706a`, `0x218bc4` |
| `150mm` | `0xe0bb2`, `0xe0bb7`, `0xe0bbd`, `0xe0bc3`, `0xe0bd5`, `0xe0bdb`, `0x20b912`, `0x217035`, `0x21703a`, `0x217048`, `0x21704f`, `0x217064`, `0x21706a`, `0x218bc4` |

Every admitted `70mm` / `150mm` guard sample:

- stopped at `0x218bc4`
- read the watched pair as `(-1.0, -1.0)` with raw bytes `000080bf000080bf`
- recorded `CF = 0`, `PF = 0`, `ZF = 0`
- therefore recorded `jae_taken = true` for the static `jae 0x218cb8`
- had stack frame `0x218bc4` under caller return `0x218f81`

The `28mm` and `35mm` runs did not observe `0x218bc4` for the first three
watched sentinel pairs within the 512-sample cap. That is not proof that wide
sentinel entries never reach the guard; it is only a scoped non-observation for
this watched subset.

## Wide Offset / Count Follow-Up

After the first wide runs recorded no `0x218bc4` guard samples for the first
three watched sentinel pairs, a `skip3` pass skipped those first three completed
sentinel pairs and armed the next three.

| Zoom | LRI | Exit | Step cap | JSON errors | Sentinel pairs skipped | Watchpoints armed | Watchpoint samples | Guard samples at `0x218bc4` |
|---|---|---:|---|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `3` | `3` | `512` | `0` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `3` | `3` | `512` | `0` |

The `skip3` runs therefore expand the scoped wide non-observation from the
first three watched sentinel pairs to the first six watched sentinel pairs.
They still do not prove wide-tier absence of guard hits, because each run is
watchpoint-capped and the full sentinel population is larger.

A count-only pass then ran the same sentinel-store breakpoints with
`arm_limit = 0`, so no watchpoints were armed and the breakpoints stayed active
for the full render.

| Zoom | LRI | Exit | Step cap | JSON errors | `0x21b92a` store hits | Completed sentinel pairs |
|---|---|---:|---|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `152` | `152` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `106` | `106` |

This count-only pass proves that the wide-tier sentinel populations are much
larger than the first-six watched subset. Wide guard behavior remains open.

## Admission Checks

The invariant used to admit the four JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.watchpoints_armed == 3 and .counts.after_store_pair_is_sentinel >= 3 and .counts.watchpoint_guard_not_skip_by_flags == 0 and .counts.watchpoint_guard_skip_by_flags == .counts.watchpoint_guard_known_sentinel_hits)' runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm.json runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm.json runs/prefusion_sentinel_score_guard/sentinel_score_guard_70mm.json runs/prefusion_sentinel_score_guard/sentinel_score_guard_150mm.json
```

The command returned `true`.

The invariant used to admit the `skip3` wide JSONs:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false and .counts.watchpoints_armed == 3 and .counts.sentinel_pairs_skipped_before_arm == 3 and .counts.watchpoint_guard_hits == 0)' runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.json runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.json
```

The command returned `true`.

The invariant used to admit the count-only wide JSONs:

```bash
jq -s -e '.[0].process_exit_status == 0 and .[0].drive_hit_step_cap == false and (.[0].errors|length == 0) and .[0].counts.watchpoints_armed == 0 and .[0].counts.store_y_hits == 152 and .[0].counts.after_store_pair_is_sentinel == 152 and .[1].process_exit_status == 0 and .[1].drive_hit_step_cap == false and (.[1].errors|length == 0) and .[1].counts.watchpoints_armed == 0 and .[1].counts.store_y_hits == 106 and .[1].counts.after_store_pair_is_sentinel == 106' runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_count.json runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_count.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_70mm.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_150mm.hdr
```

reported `Radiance HDR image data` for all four outputs.

The follow-up wide HDR verification command:

```bash
file runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_skip3.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_skip3.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_28mm_count.hdr runs/prefusion_sentinel_score_guard/sentinel_score_guard_35mm_count.hdr
```

reported `Radiance HDR image data` for all four follow-up outputs.

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit
   status `0`, no probe errors, no step cap, and Radiance HDR outputs.
2. In every admitted run, three completed `(-1.0, -1.0)` coordinate pairs were
   watchpoint-armed immediately after the `0x21b92a` y-lane sentinel store.
3. In the admitted `70mm` run, watched sentinel pairs stopped at `0x218bc4`
   twenty-six times; every such sample still read `(-1.0, -1.0)` and recorded
   `CF = 0`, so the static `jae 0x218cb8` skip was taken.
4. In the admitted `150mm` run, watched sentinel pairs stopped at `0x218bc4`
   twenty-four times; every such sample still read `(-1.0, -1.0)` and recorded
   `CF = 0`, so the static `jae 0x218cb8` skip was taken.
5. In the admitted `28mm` and `35mm` runs, the first three watched sentinel
   pairs did not stop at `0x218bc4` within the 512-sample watchpoint cap.
6. In the admitted `28mm` and `35mm` `skip3` runs, the next three watched
   sentinel pairs also did not stop at `0x218bc4` within the 512-sample
   watchpoint cap.
7. In the admitted count-only wide runs, the full render observed `152`
   completed sentinel pairs at `28mm` and `106` completed sentinel pairs at
   `35mm`.

## Safe Conclusion

For the admitted tele samples, selected sentinel-marked node-vector coordinate
pairs that reach the `0x218b30` scoring/materialization guard are skipped by the
x-lane `<= 0` guard before the y-lane/body work. This is a real downstream
non-contribution / rejection clue for those watched tele samples.

The broader parity blocker remains open: this does not prove all sentinel
entries, wide-tier guard behavior beyond the first six watched pairs,
image-level source contribution, reducer closure, or final acceptance /
rejection.
