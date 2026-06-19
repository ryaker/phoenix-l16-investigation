# Bundle + LLDB Proof: Prefusion Record-State Gate Histogram, Four-Zoom Runtime

## Scope

This note follows the candidate-scorer output vector already custody-bound to shared gate `0x2439b0`.

It proves only that:

- `0x2439b0` receives the candidate-scorer output vector under complete canonical bridge HDR renders
- `0x2439b0` conditionally rewrites `0x2c`-stride record state field `record+0x24`
- wide family-A runs (`28mm`, `35mm`) show no before/after histogram mutation at this boundary under the admitted probe
- tele family-B runs (`70mm`, `150mm`) promote matched records from `(state=3,target=2)` to `(state=4,target=2)` at this boundary under the admitted probe
- the sampled downstream entries `0x241fd0`, `0x2416d0`, and watched store sites did not match the exact known scorer-output vector under this probe

It does not prove semantic `src1` / `src2` contents, public names for record states or target fields, final contributor acceptance/rejection, or the exact pre-fusion merge/reduction mechanism.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_record_state_gate_histogram/prefusion_record_state_gate_histogram_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_record_state_gate_histogram/custody_state_28mm.lldb`
  `tools/lldb_probes/prefusion_record_state_gate_histogram/custody_state_35mm.lldb`
  `tools/lldb_probes/prefusion_record_state_gate_histogram/custody_state_70mm.lldb`
  `tools/lldb_probes/prefusion_record_state_gate_histogram/custody_state_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_record_state_gate_histogram/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_record_state_gate_histogram/verify_record_state_gate_histogram.py`
- Raw output directory:
  `runs/prefusion_record_state_gate_histogram/`

The admitted runtime JSON reports are:

- `runs/prefusion_record_state_gate_histogram/custody_state_28mm.json`
- `runs/prefusion_record_state_gate_histogram/custody_state_35mm.json`
- `runs/prefusion_record_state_gate_histogram/custody_state_70mm.json`
- `runs/prefusion_record_state_gate_histogram/custody_state_150mm.json`

The first batch attempt failed before admission because early selector/promoter probes decoded arbitrary vectors before the known scorer-output vector had been registered. The admitted JSON reports are from the corrected probe that records selector/promoter/store details only when they match a known scorer-output vector.

## Runtime Scope

Each LLDB script launches:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probed libcp addresses are:

- family A gate before/after:
  `0x2484e4`, `0x2484e9`
- family B gate before/after:
  `0x2488b9`, `0x2488be`
- sampled downstream selector/promoter entries:
  `0x241fd0`, `0x2416d0`
- sampled downstream state-store sites:
  `0x241828`, `0x2422a6`, `0x242306`
- shared record-state gate:
  `0x2439b0`

## Static Proof

Address-bounded local disassembly of the installed `libcp.dylib` shows:

- `0x2439bb` copies the vector argument from `rsi` to `r14`.
- `0x2439be` copies the state/context argument from `rdi` to `r12`.
- The first branch checks `state+0x300` through `0x25d070`, counts records where `record+0x24 == 4` and `record+0x28 == 1`, and when the count is not greater than `7`, rewrites records where `record+0x24 == 3` and `record+0x28 == 1` to state `4` at `0x243b2c`.
- The second branch checks `state+0x360` through `0x25d070`, counts records where `record+0x24 == 4` and `record+0x28 == 2`, and when the count is not greater than `7`, rewrites records where `record+0x24 == 3` and `record+0x28 == 2` to state `4` at `0x243cac`.
- Both branches walk the same `0x2c`-stride vector passed as the second argument.

The static extraction supports the runtime histogram interpretation below. It does not assign public meanings to state value `3`, state value `4`, target value `1`, or target value `2`.

## Runtime Results

The before/after histograms below are explicit sums across the admitted gate calls in each render. They are not algorithm constants.

| Zoom | LRI | Family | Exit | Gate calls | Before aggregate `state:target` counts | After aggregate `state:target` counts | Boundary result | Exact-vector `0x241fd0` entries | Exact-vector `0x2416d0` entries | Exact-vector watched stores |
|---|---|---|---:|---:|---|---|---|---:|---:|---:|
| `28mm` | `L16_02130` | A | `0` | `4` | `{"1:0":60,"3:2":346,"4:2":198}` | `{"1:0":60,"3:2":346,"4:2":198}` | unchanged | `0` | `0` | `0` |
| `35mm` | `L16_03041` | A | `0` | `4` | `{"1:0":12,"3:2":359,"4:2":245}` | `{"1:0":12,"3:2":359,"4:2":245}` | unchanged | `0` | `0` | `0` |
| `70mm` | `L16_03434` | B | `0` | `3` | `{"1:0":13,"3:1":195,"3:2":19,"4:1":278,"4:2":2}` | `{"1:0":13,"3:1":195,"4:1":278,"4:2":21}` | `19` target-2 records promoted from state `3` to `4` | `0` | `0` | `0` |
| `150mm` | `L16_02285` | B | `0` | `3` | `{"1:0":2,"3:1":36,"4:1":52,"3:2":12}` | `{"1:0":2,"3:1":36,"4:1":52,"4:2":12}` | `12` target-2 records promoted from state `3` to `4` | `0` | `0` | `0` |

For all four admitted runs:

- `process.exit_status` is `0`
- `drive_hit_step_cap` is `false`
- probe `errors` is empty
- sampled selector/promoter/store records matching the known scorer-output vector are empty

The repo-local verifier rechecks the admitted JSON/HDR artifacts, exact
before/after aggregate histograms, family split, record counts, matched active
vector continuity, empty exact-vector downstream samples, clean process exit,
and the scoped `70mm` breakpoint-cap marker:

```text
$ python3 tools/lldb_probes/prefusion_record_state_gate_histogram/verify_record_state_gate_histogram.py
28mm: OK family=a gates=4 record_count=151 promoted_target2=0
35mm: OK family=a gates=4 record_count=154 promoted_target2=0
70mm: OK family=b gates=3 record_count=169 promoted_target2=19
150mm: OK family=b gates=3 record_count=34 promoted_target2=12
```

## Proven Facts

1. `0x2439b0` is a live record-state gate for the candidate-scorer output vector under the canonical four-zoom bridge HDR quartet.
2. Under the admitted wide family-A runs, `0x2439b0` leaves the captured scorer-output vector histograms unchanged.
3. Under the admitted tele family-B runs, `0x2439b0` promotes `(state=3,target=2)` records to `(state=4,target=2)` in the captured scorer-output vector.
4. Under this exact-vector probe, sampled downstream entries `0x241fd0` and `0x2416d0` did not receive the known scorer-output vector.
5. Under this exact-vector probe, sampled downstream store sites `0x241828`, `0x2422a6`, and `0x242306` did not write records belonging to the known scorer-output vector.

## Safe Conclusion

The candidate-scorer output is now bounded one step deeper: `0x2439b0` is not only the next custody handoff, it is a live record-state gate that is inert for the admitted wide family-A runs and performs target-2 state promotion for the admitted tele family-B runs.

This narrows Lane A by proving a boundary mutation pattern, but it still does not close `CLM-PREFUSION-002`. The public meaning of the record states/targets, the final acceptance policy, and the merge/reduction mechanism remain open.

## Consequence For Blocker Work

Future work should not reopen `0x2439b0` as an unknown black-box handoff. It is now a bounded record-state gate with proven four-zoom runtime behavior at the scorer-output boundary.

The next useful Lane A work must move beyond this boundary toward one of:

- public meaning of the `0x2c` record fields and state/target values
- downstream image-effecting use of promoted records
- final contributor acceptance/rejection logic
- true multi-input merge/reduction or distributed equivalent before IRAMP
