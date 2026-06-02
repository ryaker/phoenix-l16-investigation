# Bundle + LLDB Proof: Prefusion Sentinel Guard Direct Census, Wide Tiers

## Scope

This note follows `bundle_lldb_prefusion_sentinel_score_guard_tele.md`.

The prior watchpoint proof showed:

- selected tele sentinel-marked coordinate pairs that reach `0x218bc4` skip via
  `jae 0x218cb8`
- the first six watched wide sentinel pairs did not reach `0x218bc4` within the
  watchpoint cap
- count-only wide runs observed `152` completed sentinel pairs at `28mm` and
  `106` at `35mm`

This direct census answers the next narrow wide-tier question: does the
`0x218bc4` guard site execute at all in the complete canonical wide runs while
collecting those sentinel addresses?

It does not prove that wide sentinel-marked entries are terminal, that they have
no image effect, or that final source contribution / acceptance semantics are
closed. It only bounds this one `0x218b30` scoring/materialization guard site.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_sentinel_guard_direct_census/prefusion_sentinel_guard_direct_census_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_28mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_35mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_sentinel_guard_direct_census/run_wide_direct.sh`
- Raw output directory:
  `runs/prefusion_sentinel_guard_direct_census/`

The admitted runtime JSON reports are:

- `runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_28mm.json`
- `runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_35mm.json`

The admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_28mm.hdr`
- `runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_35mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe sets direct breakpoints at:

| VA | Role |
|---:|---|
| `0x21b92a` | second sentinel store, y lane |
| `0x21b930` | first instruction after the y-lane store |
| `0x218bc4` | guard branch after x-lane compare in `0x218b30` |

The probe collects each completed `(-1.0, -1.0)` pair address at
`0x21b930`. The direct `0x218bc4` breakpoint then checks the live guard operand
address against that collected set. The guard breakpoint cap was `250000`; the
cap was not reached in either admitted run.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | `0x21b92a` store hits | Completed sentinel pairs | Unique sentinel addresses | Direct `0x218bc4` hits | Guard cap hit |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `false` | `0` | `152` | `152` | `152` | `0` | `0` |
| `35mm` | `L16_03041` | `0` | `false` | `0` | `106` | `106` | `106` | `0` | `0` |

The direct guard site `0x218bc4` recorded zero hits in both complete wide runs.
Therefore there were also zero known-sentinel guard-operand hits.

## Admission Checks

The invariant used to admit the two JSONs:

```bash
jq -s -e '.[0].process_exit_status == 0 and .[0].drive_hit_step_cap == false and (.[0].errors|length == 0) and .[0].counts.store_y_hits == 152 and .[0].counts.after_store_pair_is_sentinel == 152 and .[0].counts.unique_sentinel_addrs == 152 and .[0].counts.guard_hits == 0 and .[0].counts.guard_breakpoint_disabled_after_total_cap == 0 and .[1].process_exit_status == 0 and .[1].drive_hit_step_cap == false and (.[1].errors|length == 0) and .[1].counts.store_y_hits == 106 and .[1].counts.after_store_pair_is_sentinel == 106 and .[1].counts.unique_sentinel_addrs == 106 and .[1].counts.guard_hits == 0 and .[1].counts.guard_breakpoint_disabled_after_total_cap == 0' runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_28mm.json runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_35mm.json
```

The command returned `true`.

The HDR verification command:

```bash
file runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_28mm.hdr runs/prefusion_sentinel_guard_direct_census/sentinel_guard_direct_35mm.hdr
```

reported `Radiance HDR image data` for both outputs.

## Proven Facts

1. The admitted `28mm` and `35mm` direct-census runs completed with exit status
   `0`, no probe errors, no step cap, and Radiance HDR outputs.
2. The admitted `28mm` run collected `152` completed sentinel pairs at
   `0x21b92a -> 0x21b930`; all `152` addresses were unique.
3. The admitted `35mm` run collected `106` completed sentinel pairs at
   `0x21b92a -> 0x21b930`; all `106` addresses were unique.
4. The direct `0x218bc4` guard breakpoint had zero hits in both complete wide
   runs, and the guard breakpoint cap was not reached.

## Safe Conclusion

Under the admitted canonical `28mm` and `35mm` bridge HDR runs, the
`0x218b30` / `0x218bc4` scoring/materialization guard site is not live at all,
even while the run collects the full observed wide sentinel populations.

This refines the prior wide caveat from "the first six watched wide sentinels
did not reach this guard within cap" to "this guard site had zero direct hits
in complete admitted wide runs." It still does not prove wide sentinel entries
are terminal or non-image-effecting; they are known from the earlier downstream
watchpoint proof to be touched by other downstream copy/record/helper surfaces.
