# Bundle + LLDB Proof: Prefusion State-5 Selected-Index Path, Tele Runtime

## Scope

This note follows target-2 records promoted by the family-B `0x2439b0` gate from state `3` to state `4`, then observes whether those promoted indices enter the downstream `0x2416d0` selected-index vector and state-5 store path.

It proves only that, under clean complete canonical tele bridge HDR renders:

- selected promoted target-2 record indices enter `0x2416d0` selected-index vectors
- small promoted target-2 sets at `70mm` and `150mm` are observed reaching state `5,target=2` stores through `0x2416d0`
- the proof holds for canonical `70mm` and `150mm` tele seeds

It does not prove public state names, final acceptance/rejection semantics, downstream image contribution, reducer closure, or all promoted records for every possible render.

This is a different capture strategy from `bundle_lldb_prefusion_record_state_gate_histogram_four_zoom.md`. The earlier exact-vector negative remains scoped to that probe's captured scorer-output vector. This proof admits only the promoted vectors captured by this probe.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_state5_acceptance_path/state5_acceptance_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_state5_acceptance_path/state5_acceptance_70mm.lldb`
  `tools/lldb_probes/prefusion_state5_acceptance_path/state5_acceptance_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_state5_acceptance_path/run_tele.sh`
- Verifier:
  `tools/lldb_probes/prefusion_state5_acceptance_path/verify_state5_acceptance.py`
- Raw output directory:
  `runs/prefusion_state5_acceptance_path/`

The admitted runtime JSON reports are:

- `runs/prefusion_state5_acceptance_path/state5_acceptance_70mm.json`
- `runs/prefusion_state5_acceptance_path/state5_acceptance_150mm.json`

The probe and run directory retain the original `state5_acceptance_path` tooling name. That name is not admitted as a public acceptance-semantics claim.

The direct admitted runs also wrote Radiance HDR outputs:

- `runs/prefusion_state5_acceptance_path/state5_acceptance_70mm.hdr`
- `runs/prefusion_state5_acceptance_path/state5_acceptance_150mm.hdr`

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe:

- captures family-B gate before/after at `0x2488b9` / `0x2488be`
- records promoted indices where a `0x2c`-stride record changes from `(state=3,target=2)` to `(state=4,target=2)`
- captures `0x2416d0` entry packets and decodes its selected state-4 target-index vector
- captures pre/post executor packets around `0x241bbf` / `0x241bd7`
- samples state-5 store sites after `0x241cd6`, `0x241d3b`, `0x241d6a`, and `0x241d85`

## Static Proof Anchors

Installed-bundle disassembly and the probe's register/memory packets bound the local mechanics as follows:

- `0x2416d0` receives a `0x2c`-stride record vector and a target value.
- The selection scan checks `record+0x28` against the target and `record+0x24` against state `4`, then stores selected record indices into the local integer vector captured by the probe.
- For larger selected sets, the body materializes bitset-style entries and dispatches callback address point `0x6589e0/+0x30 = 0x247390` through generic executor `0x5670`.
- The sampled post-store PCs correspond to writes that leave records at `record+0x24 = 5`.
- These anchors identify local record selection and state relabeling. They do not assign public semantics to state `4`, state `5`, target `1`, or target `2`.

## Runtime Results

| Zoom | LRI | Exit | Step cap | JSON errors | Promotion events | Promoted records captured | Target-2 `0x2416d0` entries | Promoted-overlap `0x2416d0` entries | Promoted-overlap state-5 stores |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| `70mm` | `L16_03434` | `0` | `false` | `0` | `4` | `257` | `21` | `5` | `273` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `1` | `10` | `11` | `2` | `19` |

Both output files are Radiance HDR images in `runs/prefusion_state5_acceptance_path/`.

The repo-local verifier rechecks the admitted JSON reports, exact expected hit counts, exact small-set overlaps, clean exit status, no step cap, no probe errors, Radiance HDR output custody, and observed `(state=5,target=2)` stores for every admitted small-set overlap:

```text
$ python3 tools/lldb_probes/prefusion_state5_acceptance_path/verify_state5_acceptance.py
70mm: OK promotions=4 promoted_records=257 target2_entries=21 overlap_entries=5 promoted_store_hits=273 small_sets=target=2:selected=9:overlap=7;target=2:selected=8:overlap=8
150mm: OK promotions=1 promoted_records=10 target2_entries=11 overlap_entries=2 promoted_store_hits=19 small_sets=target=2:selected=10:overlap=10
```

### `70mm` Small-Set Evidence

The first two promoted-vector events are small enough to state exactly from admitted samples:

| `0x2416d0` call | Target | Selected count | Promoted count for vector | Promoted overlap | Observed promoted state-5 stores |
|---|---:|---:|---:|---:|---:|
| `10604922:2` | `2` | `9` | `7` | `31,49,64,68,77,78,108` | `7` |
| `10604922:7` | `2` | `8` | `8` | `79,122,134,141,142,143,148,156` | `8` |

The admitted `70mm` JSON also captured later larger target-2 calls with promoted overlap counts of `121` and `121`. Store sampling is capped, so this note does not claim all records in those larger sets reached state `5`.

### `150mm` Small-Set Evidence

The captured `150mm` promoted event is small enough to state exactly from admitted samples:

| `0x2416d0` call | Target | Selected count | Promoted count for vector | Promoted overlap | Observed promoted state-5 stores |
|---|---:|---:|---:|---:|---:|
| `10610563:6` | `2` | `10` | `10` | `17,18,19,20,21,22,23,26,28,32` | `10` |

A later `150mm` sampled call also observed nine overlapping indices written to state `5,target=1`. That later target-1 observation is recorded in the JSON but is not used as target-2 state-5 evidence here.

## Proven Facts

1. The admitted `70mm` run completed with exit status `0`, no probe errors, no step cap, and a Radiance HDR output file.
2. The admitted `150mm` run completed with exit status `0`, no probe errors, no step cap, and a Radiance HDR output file.
3. In the admitted `70mm` run, promoted target-2 indices captured at `0x2439b0` later appear in `0x2416d0` target-2 selected-index vectors.
4. In the admitted `150mm` run, promoted target-2 indices captured at `0x2439b0` later appear in a `0x2416d0` target-2 selected-index vector.
5. In the admitted `70mm` run, the first captured promoted set of seven target-2 indices and the second captured promoted set of eight target-2 indices are all observed at state `5,target=2` store stops.
6. In the admitted `150mm` run, the captured promoted set of ten target-2 indices is all observed at state `5,target=2` store stops.

## Safe Conclusion

For the admitted canonical tele runs, selected target-2 records promoted by `0x2439b0` are not only later read; the promoted indices enter the concrete `0x2416d0` selected-index vector, and the small promoted sets captured here are observed reaching state `5,target=2` stores.

This is still record-selection and state-relabel proof. It is not public acceptance semantics, final image contribution, reducer closure, or final acceptance/rejection proof.

## Consequence For Blocker Work

Follow-up Lane A evidence has now moved downstream from "are promoted records consumed?" into state-5 later-watch, `0x25d090` block-state effects, caller-side block decisions, and `0x2457c0` coordinate-output custody.

The remaining proof target is the semantic effect after that bounded state-5 / block-decision path:

- determine whether state `5` records are accepted, rejected, queued, or relabeled again
- bind the bounded coordinate-output / copied-coordinate path to any image-effecting descriptor/materialization path
- keep final acceptance/rejection and reducer closure open until those effects are proven
