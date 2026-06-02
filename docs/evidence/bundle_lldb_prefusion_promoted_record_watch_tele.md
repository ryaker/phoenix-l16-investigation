# Bundle + LLDB Proof: Prefusion Promoted Record Watch, Tele Runtime

## Scope

This note follows records that `0x2439b0` promoted from `(state=3,target=2)` to `(state=4,target=2)` in the custody-bound candidate-scorer output vector.

It proves only that, under clean complete canonical tele bridge HDR renders:

- selected promoted records are later read by downstream code
- selected promoted records reach downstream `0x2416d0` / `0x241fd0` family consumers
- selected promoted records can be promoted again from state `4` to state `5`
- the proof holds for canonical `70mm` and `150mm` tele seeds

It does not prove public state names, final acceptance/rejection semantics, final image contribution, or reducer closure.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_promoted_record_watch/prefusion_promoted_record_watch_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_promoted_record_watch/promoted_watch_70mm.lldb`
  `tools/lldb_probes/prefusion_promoted_record_watch/promoted_watch_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_promoted_record_watch/run_tele.sh`
- Raw output directory:
  `runs/prefusion_promoted_record_watch/`

The admitted runtime JSON reports are:

- `runs/prefusion_promoted_record_watch/promoted_watch_70mm.json`
- `runs/prefusion_promoted_record_watch/promoted_watch_150mm.json`

Earlier exploratory parameter sets either hit a step cap or stopped before the state-5 transition. They are not admitted here. The admitted reports are the clean rerun whose watchpoints disable after the first observed `(state=5,target=2)` sample.

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe:

- captures family-B gate before/after at `0x2488b9` / `0x2488be`
- compares the before/after `0x2c`-stride records
- selects records that changed from `(state=3,target=2)` to `(state=4,target=2)`
- arms two representative hardware read/write watchpoints over each selected record's `record+0x24..+0x2b` state/target qword
- disables watchpoints after the first observed `(state=5,target=2)` sample

## Static Proof Anchors

Local disassembly bounds the watched field use:

- In `0x2416d0`, `0x241760..0x24176b` tests `record+0x28` against the caller target and `record+0x24` against state `4`, then accumulates selected record indices.
- In the same body, state stores at `0x241d35`, `0x241d64`, and `0x241d7f` rewrite selected records' `record+0x24` to state `5` when the current state is `4`.
- In `0x241fd0`, `0x2420d0..0x24212d` scans `0x2c`-stride records and counts selected state/target combinations.
- The sampled `0x2474c0..0x2476be` window reads record-indexed values into local integer-pair/vector materialization work. This is a downstream consumer observation, not public semantic closure.

The watchpoint PC for a store is the stopped instruction after the write. For example, a stop at `0x241d3b` corresponds to the state-5 store at `0x241d35`, and a stop at `0x241d6a` corresponds to the state-5 store at `0x241d64`.

## Runtime Results

| Zoom | LRI | Exit | Step cap | Gate before / after hits | Promotion events | Promoted records in admitted event | Watched record indices | Watchpoint samples | First state-5 stop |
|---|---|---:|---|---:|---:|---:|---|---:|---|
| `70mm` | `L16_03434` | `0` | `false` | `1 / 1` | `1` | `7` | `31`, `68` | `12` | PC `0x241d3b`, record `31`, watched qword `0500000002000000` |
| `150mm` | `L16_02285` | `0` | `false` | `2 / 2` | `1` | `10` | `17`, `22` | `44` | PC `0x241d6a`, record `17`, watched qword `0500000002000000` |

Both runs wrote complete `10432x7824` HDR outputs.

The selected promoted-record index sets for the admitted promotion events were:

- `70mm`: `31,49,64,68,77,78,108`
- `150mm`: `17,18,19,20,21,22,23,26,28,32`

Only two representative records per run were watched; the rest of each promoted set was not data-watched.

## Consumer VA Buckets

The sample counts below are capped-window hardware-watchpoint samples, not exhaustive full-render totals.

| Zoom | Sampled libcp VA | Samples | Bounded local role |
|---|---:|---:|---|
| `70mm` | `0x241764` | `4` | `0x2416d0` record target/state selection scan |
| `70mm` | `0x24176b` | `2` | `0x2416d0` state-4 selection check |
| `70mm` | `0x241d2e` | `1` | pre-store state-4 check in `0x2416d0` |
| `70mm` | `0x241d3b` | `1` | after state-5 store at `0x241d35` |
| `70mm` | `0x2420d8` | `1` | `0x241fd0` state/target scan |
| `70mm` | `0x2420ec` | `1` | `0x241fd0` state/target scan |
| `70mm` | `0x2420fc` | `1` | `0x241fd0` state/target scan |
| `70mm` | `0x242111` | `1` | `0x241fd0` state/target scan |
| `150mm` | `0x2476be` | `22` | downstream record-indexed local materialization |
| `150mm` | `0x241764` | `4` | `0x2416d0` record target/state selection scan |
| `150mm` | `0x2474d1` | `3` | downstream record-indexed local materialization |
| `150mm` | `0x247534` | `3` | downstream record-indexed local materialization |
| `150mm` | `0x24176b` | `2` | `0x2416d0` state-4 selection check |
| `150mm` | `0x2474f4` | `2` | downstream record-indexed local materialization |
| `150mm` | `0x247514` | `2` | downstream record-indexed local materialization |
| `150mm` | `0x241d5d` | `1` | pre-store state-4 check in `0x2416d0` |
| `150mm` | `0x241d6a` | `1` | after state-5 store at `0x241d64` |
| `150mm` | `0x2420df` | `1` | `0x241fd0` state/target scan |
| `150mm` | `0x2420e6` | `1` | `0x241fd0` state/target scan |
| `150mm` | `0x242103` | `1` | `0x241fd0` state/target scan |
| `150mm` | `0x24210a` | `1` | `0x241fd0` state/target scan |

## Proven Facts

1. At `70mm`, at least two selected records promoted by `0x2439b0` from `(state=3,target=2)` to `(state=4,target=2)` are later read by downstream code in the same clean render.
2. At `150mm`, at least two selected records promoted by `0x2439b0` from `(state=3,target=2)` to `(state=4,target=2)` are later read by downstream code in the same clean render.
3. At `70mm`, one watched promoted record reaches state `5,target=2` at the `0x2416d0` state-store path; the stop PC is `0x241d3b`, after store `0x241d35`.
4. At `150mm`, one watched promoted record reaches state `5,target=2` at the `0x2416d0` state-store path; the stop PC is `0x241d6a`, after store `0x241d64`.
5. The admitted samples prove downstream use of selected promoted record state/target fields; they do not prove all promoted records follow the same path.

## Safe Conclusion

The `0x2439b0` target-2 state promotion is not terminal bookkeeping. In both canonical tele seeds, selected promoted records are consumed later and at least one watched record advances from state `4` to state `5` through `0x2416d0`.

This is still not reducer closure or final acceptance/rejection. It is a concrete downstream consumer path for the promoted records and a stronger next anchor for Lane A.

## Consequence For Blocker Work

Future Lane A work should move from `0x2439b0` into the live `0x2416d0` / `0x241fd0` / `0x2474c0..0x2476be` consumer windows.

The next proof target is the semantic effect of state `5` records:

- whether state `5` means accepted, suppressed, queued, or another internal category
- what data structure receives the selected record indices from `0x2416d0`
- whether the downstream record-indexed materialization window has image-effecting consequences
- how this path connects to final contributor acceptance/rejection before or after IRAMP
