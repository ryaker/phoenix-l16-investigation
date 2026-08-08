# Static/Runtime Evidence: Terminal State to `PipelineCache+0x258`

## Question

Does the calibration sibling replaced after the final
`StereoAsyncAPI::ProcessingState` lambda feed the proven warp-field-record
vector at `PipelineCache+0x258`?

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/postterminal_probe.py`
- Unit-1 four-focal scripts:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/unit1_{28mm,35mm,70mm,150mm}.lldb`
- Exact-focal Unit-2 discriminator:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/unit2_35mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/run_unit1_four_zoom.sh`
- Verifiers:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/verify_postterminal.py`
  and
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/verify_postterminal_four_zoom.py`
- Rerunnable ignored packets:
  `runs/prefusion_postterminal_calib_finalize/unit1_{28mm,35mm,70mm,150mm}.{json,log,hdr}`
  and `unit2_35mm.{json,log,hdr}`

No temporary-directory artifact is a live dependency.

## Static Join

The pinned installed binary establishes two distinct objects:

```text
0x3fe46f  r12 = callback+0x08                 whole calibration State
0x3fe4d8  r14 = r12+0x280                    finalizer subobject
0x3fe538  call 0x226240(r14)
0x226388  store replacement at r14+0x28      State+0x2a8
```

The replacement constructor `0x239a90 -> 0x2399a0` is independently
SHA-pinned and decoded by the verifier. It initializes only its own fields and
does not publish its `this` pointer.

The later `initResAmp` record loop uses a different path:

```text
0x3eb70f  load holder for PipelineCache+0x180
0x3eb716  rsi = *holder                      whole calibration State
0x3eb72d  call 0x3f7040(..., rsi, key, ...)
0x3eb78a..0x3eb7e1                           copy 0x50-byte result
                                                  into PipelineCache+0x258
```

Existing installed-bundle proof for `0x3f7040` and its two branches establishes
that this whole-State argument supplies the same `state+0xe0` and
`state+0x448` source-record families used to build each stored paired
transform/warp-field record.

## Four-Focal Runtime Join

The matrix was rerun sequentially after probe validation:

| Canonical focal | Terminal State roots | Matching later `initResAmp` joins | Final sibling first later slot touch |
|---|---:|---:|---:|
| `28mm` | `1` | `5` | `0x22eaa0` |
| `35mm` | `1` | `5` | `0x22eaa0` |
| `70mm` | `1` | `5` | `0x22eaa0` |
| `150mm` | `1` | `5` | `0x22eaa0` |
| Unit-2 `35mm` | `1` | `5` | `0x22eaa0` |

For every focal tier and the exact-focal Unit-2 discriminator, the verifier
proves:

1. the finalizer owner is exactly `State+0x280`;
2. the replaced sibling slot is therefore exactly `State+0x2a8`;
3. every matching `initResAmp` event occurs after terminal finalization;
4. `*(PipelineCache+0x180)` and the `0x3f7040` State argument are
   pointer-identical to the terminal whole-State root;
5. that State argument is not the replacement sibling pointer; and
6. the replacement sibling slot receives no intervening touch before the
   destructor's `0x22eaa0..0x22eaa8` clear transaction.

Each run exits with status `0` and writes a valid Radiance HDR. The Unit-2
packet uses `2018-07-02/L16_01956`, the exact `35mm` representative under the
distinct Unit-2 calibration hash. This validates route identity across two
physical bodies without attributing LRI calibration-value differences to
body rather than capture/firmware era.

## Admission

Admitted for `CLM-WARP-003` with canonical four-zoom Unit-1 scope and an
exact-focal Unit-2 `35mm` physical-body discriminator:

- the finalized whole calibration State is retained exactly through
  `PipelineCache+0x180`;
- after the terminal calibration lambda, `initResAmp` passes that exact State
  root to `0x3f7040` once per five collected camera keys and stores the five
  resulting `0x50` records in `PipelineCache+0x258`;
- the positive calibration-to-warp-record path is therefore
  `whole State -> state+0xe0/state+0x448 -> 0x3f7040 -> PipelineCache+0x258`;
- the sibling newly installed at `State+0x2a8` is not the object passed to
  `0x3f7040` and has no later exact-slot consumer before destruction.

This closes the proposed terminal-sibling feed question by distinguishing the
live whole-State feed from the non-feeding replacement sibling.

## Non-Claims

- This does not assign one public protobuf name to the whole internal State.
- It does not claim that no external alias of the replacement could exist by
  some unobserved mechanism; it proves the sibling is not the
  `PipelineCache+0x180` / `0x3f7040` object and is untouched through its owner
  slot.
- It does not close the distributed pre-fusion reducer or final merge
  acceptance/rejection policy.
