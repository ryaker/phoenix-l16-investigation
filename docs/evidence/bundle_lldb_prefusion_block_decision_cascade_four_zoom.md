# Bundle LLDB: Prefusion Block-Decision Cascade, Four Zoom

## Scope

This bundle follows the runtime-bounded `0x25d090` block-state effect one step
downstream into its caller-side decision logic.

It proves, under complete canonical no-auto-LRIS bridge HDR runs, that the
paired `0x25d090` calls made by the `0x244560` and `0x245a40` heavy-consumer
families feed a block-active decision that continues toward `0x2457c0` when at
least one block remains active. In the admitted runs, every sampled caller-side
decision keeps going with exactly one active block, records no abort decision,
and records no sentinel-fill path hit.

It does not prove image/source contribution, public state names, final
acceptance/rejection, or `src1` / `src2` reducer closure.

## Artifacts

- Harness:
  `tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_probe.py`
- Per-zoom LLDB scripts:
  `tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_28mm.lldb`,
  `block_decision_cascade_35mm.lldb`,
  `block_decision_cascade_70mm.lldb`,
  `block_decision_cascade_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_block_decision_cascade/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_block_decision_cascade/verify_block_decision_cascade.py`
- Raw outputs:
  `runs/prefusion_block_decision_cascade/block_decision_cascade_28mm.json`,
  `block_decision_cascade_35mm.json`,
  `block_decision_cascade_70mm.json`,
  `block_decision_cascade_150mm.json`
- Render outputs:
  `runs/prefusion_block_decision_cascade/block_decision_cascade_28mm.hdr`,
  `block_decision_cascade_35mm.hdr`,
  `block_decision_cascade_70mm.hdr`,
  `block_decision_cascade_150mm.hdr`

## Commands

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_28mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_35mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_70mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
arch -x86_64 lldb -b -s tools/lldb_probes/prefusion_block_decision_cascade/block_decision_cascade_150mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
python3 tools/lldb_probes/prefusion_block_decision_cascade/verify_block_decision_cascade.py
```

Each LLDB script launches `tools/lri_process` with `--profile 3`,
`--export-fmt 3`, and `--no-auto-lris`.

An initial batch invocation through `run_four_zoom.sh` lost the LLDB connection
on `28mm` before producing an admitted JSON. The admitted evidence is the clean
set of direct per-zoom runs listed above.

## Static Caller Anchors

The runtime probe is anchored to the caller windows extracted from the installed
`libcp.dylib`:

- `0x244560` calls `0x241fd0`, then calls `0x25d090` at `0x245411` for the
  `state+0x300` block and at `0x245436` for the `state+0x360` block.
- `0x244560` then reads `state+0x360` through `0x25d070` at `0x245442` and, if
  needed, reads `state+0x300` through `0x25d070` at `0x24544e`.
- If either block remains active, the `0x244560` path reaches the continue join
  at `0x24548d` and can call `0x2457c0` at `0x245610`.
- If both blocks are inactive, the `0x244560` path reaches the sentinel-fill
  window at `0x2454a7` and skips the `0x2457c0` call from that iteration.
- `0x245a40` has the same shape: it calls `0x241fd0`, then `0x25d090` at
  `0x246d3d` for `state+0x300` and at `0x246d60` for `state+0x360`.
- `0x245a40` reads `state+0x360` through `0x25d070` at `0x246d65` and, if
  needed, reads `state+0x300` through `0x25d070` at `0x246d75`.
- If either block remains active, the `0x245a40` path reaches the continue join
  at `0x246db0` and can call `0x2457c0` at `0x24717b`.
- If both blocks are inactive, the `0x245a40` path reaches its sentinel-fill
  window; this probe watches the fill loop site at `0x246e98`.

## Verifier Output

The repo-local verifier rechecks clean completion, exact decision/call counts,
one-active-block decision patterns, absence of abort/fill samples, and Radiance
HDR output custody:

```text
28mm: OK decisions=31 coord_output_calls=9 heavy_244560 {(0, 1, 0): 16}; heavy_245a40 {(0, 1, 0): 15}
35mm: OK decisions=31 coord_output_calls=9 heavy_244560 {(0, 1, 0): 16}; heavy_245a40 {(0, 1, 0): 15}
70mm: OK decisions=27 coord_output_calls=8 heavy_244560 {(1, 0, 0): 12}; heavy_245a40 {(0, 1, 0): 15}
150mm: OK decisions=31 coord_output_calls=9 heavy_244560 {(1, 0, 0): 16}; heavy_245a40 {(0, 1, 0): 15}
```

Tuple format is `(state+0x300 active, state+0x360 active, abort flag)`.

## Result Table

| Zoom | Decision joins | `0x244560` decision pattern | `0x245a40` decision pattern | Abort decisions | Sentinel-fill path hits | `0x2457c0` callsite hits |
|---|---:|---|---|---:|---:|---:|
| `28mm` | 31 | `(0,1,0) x16` | `(0,1,0) x15` | 0 | 0 | 9 |
| `35mm` | 31 | `(0,1,0) x16` | `(0,1,0) x15` | 0 | 0 | 9 |
| `70mm` | 27 | `(1,0,0) x12` | `(0,1,0) x15` | 0 | 0 | 8 |
| `150mm` | 31 | `(1,0,0) x16` | `(0,1,0) x15` | 0 | 0 | 9 |

All four admitted runs exited with status `0`, hit no probe step cap, recorded
no probe errors, and wrote `10432 x 7824` HDR outputs.

## Proven Facts

1. In the admitted four-zoom runs, every caller-side decision join after the
   paired `0x25d090` calls has abort flag `0`.
2. Every admitted decision join has exactly one active block: either
   `state+0x300` active and `state+0x360` inactive, or `state+0x300` inactive
   and `state+0x360` active.
3. No admitted run hits the watched sentinel-fill path for either
   `0x244560` or `0x245a40`.
4. Every admitted run reaches a `0x2457c0` callsite from these caller families,
   and every sampled `0x2457c0` callsite packet still has exactly one active
   block.
5. The wide tiers (`28mm`, `35mm`) continue through `0x244560` with
   `state+0x360` active; the tele tiers (`70mm`, `150mm`) continue through
   `0x244560` with `state+0x300` active. The `0x245a40` family continues with
   `state+0x360` active at all four focal tiers.

## Safe Conclusion

The `0x25d090` block-state effect is not terminal bookkeeping in the admitted
four-zoom runs. Its caller-side active-byte checks feed a live decision cascade:
the admitted `0x244560` / `0x245a40` decisions keep one block active, avoid the
watched sentinel-fill abort path, and continue into the already-admitted
`0x2457c0 -> state+0x1e8` coordinate-output materialization path.

This is downstream block-decision / coordinate-output custody proof. It is not
image-effect proof, final acceptance/rejection proof, or reducer closure.

## Non-Admissions

- This does not prove public state or target names.
- This does not prove that all possible `0x244560` / `0x245a40` inputs avoid
  the sentinel-fill path.
- This does not prove that the resulting `state+0x1e8` coordinates affect final
  pixels.
- This does not prove final acceptance/rejection logic.
- The counts in this bundle are evidence-run observations, not universal
  algorithm constants.
