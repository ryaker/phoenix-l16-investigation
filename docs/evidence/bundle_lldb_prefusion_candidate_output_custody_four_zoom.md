# Bundle + LLDB Proof: Prefusion Candidate Output Custody, Four-Zoom Runtime

## Scope

This note follows the output vector written by the already-bounded prefusion candidate-scoring family.

It proves only that:

- the `0x24c320` scorer family is dispatched through the family-A callback object installed by `0x2481a0`
- the `0x24d610` scorer family is dispatched through the family-B callback object installed by `0x248580`
- the scorer-output vector decoded from each callback context is the same vector pointer passed to the shared `0x2439b0` record-state gate under complete canonical bridge HDR renders
- the proof holds for the corrected canonical `28mm`, `35mm`, `70mm`, and `150mm` seed set

It does not prove semantic `src1` / `src2` contents, camera membership, final contributor acceptance/rejection, or the exact pre-fusion merge/reduction mechanism.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_candidate_output_custody/prefusion_candidate_output_custody_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_candidate_output_custody/custody_28mm.lldb`
  `tools/lldb_probes/prefusion_candidate_output_custody/custody_35mm.lldb`
  `tools/lldb_probes/prefusion_candidate_output_custody/custody_70mm.lldb`
  `tools/lldb_probes/prefusion_candidate_output_custody/custody_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_candidate_output_custody/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_candidate_output_custody/verify_candidate_output_custody.py`
- Raw output directory:
  `runs/prefusion_candidate_output_custody/`

The admitted runtime JSON reports are:

- `runs/prefusion_candidate_output_custody/custody_28mm.json`
- `runs/prefusion_candidate_output_custody/custody_35mm.json`
- `runs/prefusion_candidate_output_custody/custody_70mm.json`
- `runs/prefusion_candidate_output_custody/custody_150mm.json`

The `70mm` parallel batch attempt stopped with an instrumentation-sensitive `EXC_BAD_ACCESS` before useful counters. The admitted `70mm` JSON report is from the solo rerun captured in `runs/prefusion_candidate_output_custody/custody_70mm_solo.log`, which completed with exit status `0`.

## Runtime Scope

Each LLDB script launches:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probed libcp addresses are:

- family A constructor/wrapper/custody path:
  `0x2481a0`, `0x2484a6`, `0x24c320`, `0x2484bd`, `0x2484e4`
- family B constructor/wrapper/custody path:
  `0x248580`, `0x24887b`, `0x24d610`, `0x248892`, `0x2488b9`
- shared record-state gate:
  `0x2439b0`

## Static Proof

Installed-bundle inspection bounds the candidate scorer entries as indirect callback targets:

| Target | Direct qword references found | Callback table / wrapper route |
|---|---:|---|
| `0x24c320` | `0` | table address point `0x667788`, slot `+0x30 = 0x24c2d0`; wrapper adjusts `rdi += 0x8` and jumps to `0x24c320` |
| `0x24d610` | `0` | table address point `0x667808`, slot `+0x30 = 0x24d5c0`; wrapper adjusts `rdi += 0x8` and jumps to `0x24d610` |
| `0x247390` | `1` at `0x658a10` | adjacent `SparseLNR::markInliers(..., void(int,int,int))` callback table; not the family-A/B scorer route |

Installed-bundle inspection bounds the family-A constructor path:

- `0x2481a0` allocates a `0xb0`-byte callback object.
- `0x2483e5..0x2483ec` installs vtable address point `0x667788`.
- The scorer context pointer is allocated object `+0x8`.
- The output vector consumed by `0x24c320` is stored at allocated object `+0x20`, which is scorer-context `+0x18`.
- `0x2484b8` calls generic executor `0x5670`.
- `0x2484de..0x2484e4` passes the same output vector onward as the second argument to `0x2439b0`.

Installed-bundle inspection bounds the family-B constructor path:

- `0x248580` allocates a `0xa8`-byte callback object.
- `0x2487bd..0x2487c4` installs vtable address point `0x667808`.
- The scorer context pointer is allocated object `+0x8`.
- The output vector consumed by `0x24d610` is stored at allocated object `+0x30`, which is scorer-context `+0x28`.
- `0x24888d` calls generic executor `0x5670`.
- `0x2488b3..0x2488b9` passes the same output vector onward as the second argument to `0x2439b0`.

Offset caution:

- family-A output vector is allocated-object `+0x20`, scorer-context `+0x18`
- family-B output vector is allocated-object `+0x30`, scorer-context `+0x28`

Prose that mixes allocated-object offsets with scorer-context offsets is wrong.

## Runtime Results

Breakpoints at `0x24c320`, `0x24d610`, and `0x2439b0` were capped at `160` hits. Counts equal to `160` are lower bounds for that run.

| Zoom | LRI | Exit | Family | Runtime table | Context-ready hits | Scorer entry hits | Opposite scorer hits | Gate-call hits | Shared-gate matched-vector hits | Output vector | Record count |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---|---:|
| `28mm` | `L16_02130` | `0` | A | `0x1092e1788 = base+0x667788` | `4` | `>=160` at `0x24c320` | `0` at `0x24d610` | `4` | `4` | `0x304c67fd0` | `151` |
| `35mm` | `L16_03041` | `0` | A | `0x1092e1788 = base+0x667788` | `4` | `>=160` at `0x24c320` | `0` at `0x24d610` | `4` | `4` | `0x304c67fd0` | `154` |
| `70mm` | `L16_03434` | `0` | B | `0x1092e1808 = base+0x667808` | `4` | `>=160` at `0x24d610` | `0` at `0x24c320` | `4` | `4` | `0x304c67fb0` | `169` |
| `150mm` | `L16_02285` | `0` | B | `0x1092e1808 = base+0x667808` | `4` | `136` at `0x24d610` | `0` at `0x24c320` | `4` | `4` | `0x304c67fb0` | `34` |

For all four admitted runs:

- `drive_hit_step_cap` is `false`
- probe `errors` is empty
- every captured family gate call has `matches_active_output_vec = true`
- every matched `0x2439b0` entry carries the same output-vector pointer and record count as the immediately preceding family gate call

The repo-local verifier rechecks the admitted JSON reports, log/HDR artifact
presence, exact family split, expected scorer/opposite-scorer counts, four gate
calls, four matched shared-gate entries, 0x2c-stride record-vector shape, and
gate/shared pointer continuity:

```text
$ python3 tools/lldb_probes/prefusion_candidate_output_custody/verify_candidate_output_custody.py
28mm: OK family=a record_count=151 gate_calls=4 shared_matches=4
35mm: OK family=a record_count=154 gate_calls=4 shared_matches=4
70mm: OK family=b record_count=169 gate_calls=4 shared_matches=4
150mm: OK family=b record_count=34 gate_calls=4 shared_matches=4
```

## Proven Facts

1. Under the canonical bridge HDR quartet, `28mm` and true-`35mm` use the family-A callback table route:
   `0x667788/+0x30 -> 0x24c2d0 -> 0x24c320`.
2. Under the canonical bridge HDR quartet, `70mm` and `150mm` use the family-B callback table route:
   `0x667808/+0x30 -> 0x24d5c0 -> 0x24d610`.
3. Family-A runtime custody proves the `0x24c320` scorer-output vector at context `+0x18` is passed to `0x2439b0`.
4. Family-B runtime custody proves the `0x24d610` scorer-output vector at context `+0x28` is passed to `0x2439b0`.
5. The record counts observed at the gate and shared-gate boundary are run observations for the canonical seed set, not algorithm constants.

## Safe Conclusion

The candidate scorer output records are now custody-bound to the shared `0x2439b0` record-state gate by exact output-vector pointer continuity across the canonical four-zoom bridge HDR quartet.

This narrows the Lane A search because `0x24c320` / `0x24d610` plus their immediate `0x2439b0` handoff are scorer-output and record-state custody surfaces. It still does not close `CLM-PREFUSION-002`.

## Consequence For Blocker Work

Future work should not reopen the already-bounded `0x24c320` / `0x24d610` scorer entries as if their output destination were unknown.

The next useful Lane A work must move beyond this scorer-output-to-record-gate custody seam and target surfaces that can still prove one of the remaining unknowns:

- semantic `src1` / `src2` contents
- multi-input reduction or distributed merge math before IRAMP
- final contributor acceptance/rejection policy
- public meaning of the record states consumed after `0x2439b0`
