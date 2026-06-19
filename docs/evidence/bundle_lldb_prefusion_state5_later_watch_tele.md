# Bundle + LLDB Proof: Prefusion State-5 Later Watch, Tele Runtime

## Scope

This note follows the next downstream fate of watched target-2 records after they become `(state=5,target=2)` through the `0x2416d0` path.

It proves only that, under clean complete canonical tele bridge HDR renders:

- watched promoted records continue to trigger hardware watchpoints after state `5`
- samples where the watched record still decodes as `(state=5,target=2)` reach `0x244560` and the `0x25d090` helper family
- the proof holds for canonical `70mm` and `150mm` tele seeds

It does not prove public state names, final acceptance/rejection semantics, downstream image contribution, reducer closure, or all state-5 record consumers.

## Repo-Local Artifacts

- Shared probe harness:
  `tools/lldb_probes/prefusion_promoted_record_watch/prefusion_promoted_record_watch_probe.py`
- Later-watch LLDB scripts:
  `tools/lldb_probes/prefusion_state5_later_watch/state5_later_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_later_watch/state5_later_150mm.lldb`
- Runners:
  `tools/lldb_probes/prefusion_state5_later_watch/run_tele.sh`
  `tools/lldb_probes/prefusion_state5_later_watch/run_150.sh`
- Verifier:
  `tools/lldb_probes/prefusion_state5_later_watch/verify_state5_later_watch.py`
- Raw output directory:
  `runs/prefusion_state5_later_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_later_watch/state5_later_70mm.json`
- `runs/prefusion_state5_later_watch/state5_later_150mm.json`

Both admitted runs wrote Radiance HDR outputs:

- `runs/prefusion_state5_later_watch/state5_later_70mm.hdr`
- `runs/prefusion_state5_later_watch/state5_later_150mm.hdr`

The shared probe gained an optional `post_state5_sample_cap` argument. Existing scripts that omit it keep their previous behavior. The later-watch scripts pass `disable_after_state5 = False` so the watchpoints remain alive after the first state-5 observation.

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe:

- captures family-B gate before/after at `0x2488b9` / `0x2488be`
- selects promoted target-2 records by comparing before/after `0x2c`-stride records
- arms hardware read/write watchpoints on representative promoted record `record+0x24..+0x2b`
- keeps watchpoints enabled after state `5` so later touches can be observed
- records only samples where `record+0x24 == 5` and `record+0x28 == 2` as state-5 evidence

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Watchpoints armed | Total watchpoint samples | State-5 target-2 samples | State-5 libcp VAs |
|---|---|---:|---|---:|---:|---:|---:|---|
| `70mm` | `L16_03434` | `0` | `false` | `0` | `2` | `512` | `11` | `0x241d3b`, `0x241d85`, `0x245383`, `0x24538f`, `0x25d15c`, `0x25d16c` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `1` | `256` | `5` | `0x241d3b`, `0x245383`, `0x25d15c`, `0x25d16c` |

Only the `State-5 target-2 samples` are admitted for the downstream state-5 claim. Other watchpoint samples can occur after the watched memory no longer decodes as the same `(state=5,target=2)` record and are not used as evidence here.

Repo-local verifier output:

```text
70mm: OK armed=[31, 68] state5_hits=11 state5_vas=0x241d3b,0x241d85,0x245383,0x24538f,0x25d15c,0x25d16c
150mm: OK armed=[17] state5_hits=5 state5_vas=0x241d3b,0x245383,0x25d15c,0x25d16c
```

## State-5 Downstream VA Buckets

The stopped PC is the instruction after the watched read/write.

| VA | Observed zooms | Bounded role |
|---:|---|---|
| `0x241d3b` | `70mm`, `150mm` | state-5 store stop inside `0x2416d0` |
| `0x241d85` | `70mm` | alternate state-5 store stop inside `0x2416d0` |
| `0x245383` | `70mm`, `150mm` | later read/use inside `0x244560` heavy-consumer family |
| `0x24538f` | `70mm` | later read/use inside `0x244560` heavy-consumer family |
| `0x25d15c` | `70mm`, `150mm` | later read/use inside `0x25d090` helper family |
| `0x25d16c` | `70mm`, `150mm` | later read/use inside `0x25d090` helper family |

Representative stacks for the later state-5 samples:

- `0x245383 -> 0x224ee8 -> 0x22a4f5 -> 0x22f3ff -> 0x227063 -> 0x3fc99d`
- `0x25d15c -> 0x245416 -> 0x224ee8 -> 0x22a4f5 -> 0x22f3ff -> 0x227063 -> 0x3fc99d`
- `0x25d16c -> 0x24543b -> 0x224ee8 -> 0x22a4f5 -> 0x22f3ff -> 0x227063 -> 0x3fc99d`

Existing installed-bundle proof already bounds the `0x25d090` helper family as candidate block-geometry / active-block state work, not exposed reducer math. This later-watch proof shows state-5 records reach that already-bounded helper family.

## Proven Facts

1. The admitted `70mm` later-watch run completed with exit status `0`, no probe errors, no step cap, and a Radiance HDR output file.
2. The admitted `150mm` later-watch run completed with exit status `0`, no probe errors, no step cap, and a Radiance HDR output file.
3. In the admitted `70mm` run, watched promoted records that become `(state=5,target=2)` are later touched at `0x245383` / `0x24538f` in the `0x244560` family and at `0x25d15c` / `0x25d16c` in the `0x25d090` helper family.
4. In the admitted `150mm` run, a watched promoted record that becomes `(state=5,target=2)` is later touched at `0x245383` in the `0x244560` family and at `0x25d15c` / `0x25d16c` in the `0x25d090` helper family.
5. The admitted samples prove state-5 records are not terminal at the `0x2416d0` store; they do not prove final image contribution or final acceptance/rejection semantics.

## Safe Conclusion

State `5` is not the terminal endpoint for the watched promoted tele records. After `0x2416d0`, the watched state-5 records are consumed by the `0x244560` heavy-consumer family and then by the already-bounded `0x25d090` candidate block-geometry / active-block helper family.

This is still state/candidate/geometry flow, not image-effect proof and not reducer closure.

## Consequence For Blocker Work

Lane A should move from generic "what does state `5` do?" to the concrete downstream path:

`0x244560 -> 0x25d090`

Follow-up evidence now bounds the immediate `0x25d090` active-block effect and the `0x244560` / `0x245a40` caller-side decision cascade into `0x2457c0` coordinate-output custody. The remaining proof target is downstream image/source contribution, final acceptance/rejection policy, or another bounded non-reducer helper beyond that coordinate-output path.
