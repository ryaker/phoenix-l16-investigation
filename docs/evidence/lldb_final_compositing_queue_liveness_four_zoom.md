# LLDB Proof: Final-Compositing Queue / Drain Runtime Liveness Across Four Zooms

## Scope

This proof independently re-runs the runtime portion of Opus's quarantined
`final_compositing_consumer_FOURZOOM.md` packet for the installed
`libcp.dylib` and the canonical bridge-HDR four-zoom quartet.

It proves only runtime liveness and local operand shape for the narrowed
queue/drain surface:

- producer call-edge `0x3bf8bc -> 0x3bfc40`;
- insert entry `0x3bfc40`;
- drain entry `0x3bfe60`;
- orchestrator drain call-edge `0x3bcc51 -> 0x3bfe60`;
- post-gather 0x70-stride filter loop `0x3bccc0`.

It does not prove byte-level copy-vs-blend behavior, final file/display sink,
public type/field names, final output semantics, anti-ghosting policy, or final
merge acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_liveness/final_compositing_liveness_probe.py`
- `tools/lldb_probes/codex_final_compositing_liveness/final_compositing_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_liveness/final_compositing_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_liveness/final_compositing_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_liveness/final_compositing_150mm.lldb`
- `tools/lldb_probes/codex_final_compositing_liveness/run_four_zoom.sh`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_liveness/final_compositing_28mm.json`
- `runs/codex_final_compositing_liveness/final_compositing_35mm.json`
- `runs/codex_final_compositing_liveness/final_compositing_70mm.json`
- `runs/codex_final_compositing_liveness/final_compositing_150mm.json`
- matching `.log` and `.hdr` files in the same directory

An earlier broad 35mm probe with extra join/dispatch breakpoints stalled under
Rosetta and was narrowed before admission:

- `runs/codex_final_compositing_liveness/final_compositing_35mm_broad_failed.log`

That failed broad run is diagnostic only and is not cited as evidence for any
canonical claim.

## Inputs

Binary:

- `/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`

Frameworks:

- `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

LRIs:

| Zoom | LRI |
|---|---|
| `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All runs used:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/codex_final_compositing_liveness/final_compositing_<zoom>.lldb
```

Each launch passed `--profile 3 --export-fmt 3 --no-auto-lris` and completed a
`10432x7824` HDR write under the LLDB probe.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap.

| Zoom | Exit | Step cap | `0x3bf8bc` | `0x3bfc40` | `0x3bfe60` | `0x3bcc51` | `0x3bccc0` |
|---|---:|---|---:|---:|---:|---:|---:|
| `28mm` | `0` | `false` | 8 | 8 | 4 | 3 | 8 |
| `35mm` | `0` | `false` | 8 | 8 | 4 | 3 | 8 |
| `70mm` | `0` | `false` | 9 | 8 | 4 | 3 | 7 |
| `150mm` | `0` | `false` | 8 | 8 | 4 | 3 | 8 |

The `70mm` `0x3bf8bc` count exceeded the sample cap by one due to the capped
multi-thread breakpoint race; the report still captured capped samples and the
process exited normally.

## Operand Shape

The admitted samples reproduce the static queue/drain shape at runtime:

- At `0x3bf8bc`, the producer call-edge reaches `0x3bfc40` on all four focal
  tiers, and the captured stack record has local fields `field_i32_0x00 = 13`
  and `field_i32_0x04 = 2`.
- At `0x3bfe60`, the drain entry is live on all four focal tiers. The first
  captured drain sample per tier sees the local container with `count_0x10 = 1`,
  `stop_0x18 = 0`, and both sentinel checks false, while the output vector is
  initially empty.
- At `0x3bcc51`, the orchestrator's call-edge to `0x3bfe60` is live on all four
  focal tiers and carries the same local container/vector shape as the drain
  entry.
- At `0x3bccc0`, the post-gather loop is live on all four focal tiers and sees
  the gathered vector as 0x70-stride storage. The first captured loop sample
  has gathered-vector counts `9`, `9`, `8`, and `9` for `28mm`, `35mm`, `70mm`,
  and `150mm`, respectively.

## Proven Facts

- The previously static final-compositing queue/drain surface is runtime-live
  on the canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge-HDR quartet.
- Runtime samples bind the live producer call-edge `0x3bf8bc -> 0x3bfc40`, live
  insert body `0x3bfc40`, live drain body `0x3bfe60`, live orchestrator drain
  call-edge `0x3bcc51 -> 0x3bfe60`, and live post-gather 0x70-stride filter
  loop `0x3bccc0`.
- Runtime operands are consistent with the static intrusive queue / vector
  drain proof in `bundle_static_final_compositing_queue_drain.md`.

## Non-Claims

- This proof does not identify public C++ type or field names for the local
  0x70-byte records.
- This proof does not prove byte-level copy-vs-blend behavior for the later
  per-tile processors.
- This proof does not identify the final file/display sink.
- This proof does not close final output semantics, anti-ghosting policy, or
  final merge acceptance/rejection.
