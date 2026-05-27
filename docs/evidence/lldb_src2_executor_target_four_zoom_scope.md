# LLDB Evidence: Visible `src2` Executor Target Scope Across Four Zooms

## Scope

This proof extends the visible `src2` executor-target investigation beyond the
canonical `28mm` seed. It uses the same runtime helper as the `28mm` proof, with
dynamic hardware breakpoints for the non-28mm completion runs to avoid the
software-breakpoint perturbation seen on tele seeds.

It proves:

- `28mm`: accepted gate, accepted dispatch, dynamic worker entry, and completed
  HDR output all bind to slot `+0x30 = 0x3ed2e0`.
- `35mm`: a dynamic hardware-breakpoint completion probe accepts the visible
  `src2` gate, installs hardware dispatch and worker-entry breakpoints after
  that accepted gate, proves accepted dispatch through `0x5d94` plus worker
  entry at `+0x30 = 0x3ed2e0`, continues past the worker stop, and writes a
  completed `10432x7824` HDR output.
- `70mm`: the same dynamic hardware completion method proves accepted gate,
  accepted dispatch through `0x5d94`, worker entry at `+0x30 = 0x3ed2e0`, and
  completed `10432x7824` HDR output.
- `150mm`: the same dynamic hardware completion method proves accepted gate,
  accepted dispatch through `0x5d94`, worker entry at `+0x30 = 0x3ed2e0`, and
  completed `10432x7824` HDR output.

This does not prove semantic `src2` contents, multi-source reducer closure, or
final merge acceptance/rejection behavior.

## Artifacts

- Runtime helper:
  [src2_executor_target_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_probe.py)
- `28mm` script:
  [src2_executor_target_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_28mm.lldb)
- `35mm` script:
  [src2_executor_target_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_35mm.lldb)
- `35mm` dynamic worker-entry script:
  [src2_executor_target_35mm_hwworker.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_35mm_hwworker.lldb)
- `35mm` dynamic completion script:
  [src2_executor_target_35mm_hwcomplete.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_35mm_hwcomplete.lldb)
- `70mm` script:
  [src2_executor_target_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_70mm.lldb)
- `70mm` dynamic dispatch script:
  [src2_executor_target_70mm_hwdispatch.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwdispatch.lldb)
- `70mm` dynamic worker-entry script:
  [src2_executor_target_70mm_hwworker.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwworker.lldb)
- `70mm` dynamic completion script:
  [src2_executor_target_70mm_hwcomplete.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwcomplete.lldb)
- `150mm` script:
  [src2_executor_target_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_150mm.lldb)
- `150mm` dynamic dispatch script:
  [src2_executor_target_150mm_hwdispatch.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwdispatch.lldb)
- `150mm` dynamic worker-entry script:
  [src2_executor_target_150mm_hwworker.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwworker.lldb)
- `150mm` dynamic completion script:
  [src2_executor_target_150mm_hwcomplete.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwcomplete.lldb)
- Raw logs:
  `runs/src2_executor_target/src2_executor_target_28mm.log`,
  `runs/src2_executor_target/src2_executor_target_35mm.log`,
  `runs/src2_executor_target/src2_executor_target_35mm_hwworker.log`,
  `runs/src2_executor_target/src2_executor_target_35mm_hwcomplete.log`,
  `runs/src2_executor_target/src2_executor_target_70mm.log`,
  `runs/src2_executor_target/src2_executor_target_70mm_hwdispatch.log`,
  `runs/src2_executor_target/src2_executor_target_70mm_hwworker.log`,
  `runs/src2_executor_target/src2_executor_target_70mm_hwcomplete.log`,
  `runs/src2_executor_target/src2_executor_target_150mm.log`,
  `runs/src2_executor_target/src2_executor_target_150mm_hwdispatch.log`,
  `runs/src2_executor_target/src2_executor_target_150mm_hwworker.log`,
  `runs/src2_executor_target/src2_executor_target_150mm_hwcomplete.log`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_28mm.lldb > runs/src2_executor_target/src2_executor_target_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_35mm.lldb > runs/src2_executor_target/src2_executor_target_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_35mm_hwworker.lldb > runs/src2_executor_target/src2_executor_target_35mm_hwworker.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_35mm_hwcomplete.lldb > runs/src2_executor_target/src2_executor_target_35mm_hwcomplete.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_70mm.lldb > runs/src2_executor_target/src2_executor_target_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwdispatch.lldb > runs/src2_executor_target/src2_executor_target_70mm_hwdispatch.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwworker.lldb > runs/src2_executor_target/src2_executor_target_70mm_hwworker.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_70mm_hwcomplete.lldb > runs/src2_executor_target/src2_executor_target_70mm_hwcomplete.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_150mm.lldb > runs/src2_executor_target/src2_executor_target_150mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwdispatch.lldb > runs/src2_executor_target/src2_executor_target_150mm_hwdispatch.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwworker.lldb > runs/src2_executor_target/src2_executor_target_150mm_hwworker.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_150mm_hwcomplete.lldb > runs/src2_executor_target/src2_executor_target_150mm_hwcomplete.log
```

## Runtime Summary

| Seed | Proof mode | Accepted gate | Accepted dispatch | Worker entry | Slot `+0x30` | Output |
|---|---:|---:|---:|---:|---:|---|
| `28mm` / `L16_02130` | software breakpoints, full render | `1` | `1` | `1` | `0x3ed2e0` | completed HDR |
| `35mm` / `L16_03041` | dynamic hardware breakpoints, completion render | `1` | `4` | `1` | `0x3ed2e0` | completed HDR |
| `70mm` / `L16_03434` | dynamic hardware breakpoints, completion render | `1` | `1` | `1` | `0x3ed2e0` | completed HDR |
| `150mm` / `L16_02285` | dynamic hardware breakpoints, completion render | `1` | `1` | `1` | `0x3ed2e0` | completed HDR |

Line evidence:

- `28mm`: the process writes `10432x7824`, exits status `0`, and reports one
  accepted gate, one accepted dispatch, one worker entry, and slot
  `4117216 == 0x3ed2e0`
  (`src2_executor_target_28mm.log:34`, `:36`, `:39`).
- `35mm`: the completion run uses a launch-time hardware breakpoint at
  `0x3ec462`, creates the `0x5d94` hardware dispatch breakpoint dynamically
  after the accepted gate, continues through the worker stop, writes
  `10432x7824`, and reports one accepted gate, four accepted dispatches, one
  worker entry, and slot / worker VA `4117216 == 0x3ed2e0`
  (`src2_executor_target_35mm_hwcomplete.log:55`, `:58`, `:59`).
- `70mm`: the completion run writes `10432x7824`, exits status `0`, and reports
  one accepted gate, one accepted dispatch, one worker entry, and slot / worker
  VA `4117216 == 0x3ed2e0`
  (`src2_executor_target_70mm_hwcomplete.log:16`, `:18`, `:22`, `:23`).
- `150mm`: the completion run writes `10432x7824` and reports one accepted gate,
  one accepted dispatch, one worker entry, and slot / worker VA
  `4117216 == 0x3ed2e0`
  (`src2_executor_target_150mm_hwcomplete.log:48`, `:51`, `:52`).

All four JSON packets report `"errors": []`
(`src2_executor_target_28mm.log:40`,
`src2_executor_target_35mm_hwcomplete.log:59`,
`src2_executor_target_70mm_hwcomplete.log:23`,
`src2_executor_target_150mm_hwcomplete.log:52`).

## Runtime State Samples

The first accepted packet values are runtime samples, not constants:

| Seed | `+0x08` descriptor | `+0x10` descriptor | Tile offset | Transform origin | State offsets | Matrix class |
|---|---|---|---|---|---|---|
| `28mm` | `220x220`, stride `220` | `217x217`, stride `217` | `(0, 0)` | `(0, 0)` | `(2020.0, 1505.0)` | `0.991346...` diagonal, translation `(17, 13)` |
| `35mm` | `234x234`, stride `234` | `233x233`, stride `233` | `(1616, 1416)` | `(1616, 1414)` | `(2020.0, 1505.0)` | same sampled matrix as `28mm` |
| `70mm` | `252x250`, stride `252` | `249x249`, stride `249` | `(0, 0)` | `(0, 0)` | `(2075.0, 1590.0)` | `0.998077...` diagonal, translation near `(3, 2)` |
| `150mm` | `270x270`, stride `270` | `265x265`, stride `265` | `(944, 704)` | `(940, 700)` | `(2075.0, 1590.0)` | `0.998077...` diagonal, translation near `(3, 2)` |

The radial table heads/tails also differ by tier:

- `28mm` and `35mm`: head begins `1.0, 1.0000052452087402, ...`; tail sample
  at index `4092` is `0.9999083280563354`.
- `70mm` and `150mm`: head begins with five `1.0` entries followed by
  `1.0000001192092896`; tail sample at index `4092` is
  `0.9997740983963013`.

See each run's JSON packet for the full captured sample
(`src2_executor_target_28mm.log:40`,
`src2_executor_target_35mm_hwcomplete.log:59`,
`src2_executor_target_70mm_hwcomplete.log:23`,
`src2_executor_target_150mm_hwcomplete.log:52`).

## Perturbation Boundary

The dynamic hardware completion runs prove output completion under this
instrumentation profile. They are proof of the visible `src2` executor target
path and render completion, not proof of semantic `src2` contents,
multi-source reducer closure, final merge acceptance/rejection, or
Lumen-quality image parity.

## Safe Conclusion

Across the canonical `28mm`, `35mm`, `70mm`, and `150mm` seeds, the first
accepted visible-`src2` executor gate exposes callback vtable address point
`0x65f7e8` and slot `+0x30 = 0x3ed2e0`.

At all four canonical seeds, the same target is additionally proven by accepted
dispatch through generic tiler forwarding site `0x5d94`, dynamic worker entry,
and completed `10432x7824` HDR output.

Static classification of `0x3ed2e0` remains the one from
[lldb_src2_executor_target_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_executor_target_28mm.md):
one-source descriptor resampling/materialization over `cache+0x1e0`
projection/radial state, a 4096-entry radial table, 1/64 fractional
coefficient-table indexing, 4x4 SIMD sampling/clamping, and 16-byte vector
output.

## Remaining Unknowns

- public semantic names and LRI origins for `cache+0x1e0` fields
- full coefficient-table values / generator behind callback `+0x28`
- public semantic identity and LRI origin of the source descriptor consumed at
  callback `+0x08`; producer custody is now bounded separately in
  [lldb_src2_descriptor_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_descriptor_origin_four_zoom.md)
- whether `0x3ed2e0` materializes an already selected descriptor or feeds a
  later merge-quality decision
