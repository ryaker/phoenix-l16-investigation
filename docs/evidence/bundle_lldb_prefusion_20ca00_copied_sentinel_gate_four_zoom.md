# Bundle + LLDB Proof: Prefusion `0x20ca00` Copied Sentinel Gate, Four Zooms

## Scope

This note follows the State `0x22ae60` copy/record-surface classification in
[bundle_static_prefusion_state_22ae60_copy_record_surfaces.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_prefusion_state_22ae60_copy_record_surfaces.md).

That prior note proved that sampled sentinel-marked pairs are copied inside
`0x20ca00`, and that `0x20ca00` contains positive-coordinate gates before Ceres
work. It did not prove that a watched copied sentinel element was the exact
element later selected by the `0x20d35e -> 0x20d363` positive-coordinate gate.

This probe closes that narrow identity question only for the sampled/capped
window described below:

- `70mm`: one watched sentinel copied by `0x20d304 -> 0xe0ae0` had
  `source_index == gate_index == 774`; the copied destination pair was later
  read at `0x20d363` as `(-1.0, -1.0)` and branched to the skip target
  `0x20d565`.
- `28mm`, `35mm`, and `150mm`: the watched sentinel pairs produced capped
  `0x20d309` source-copy observations, but no `source_index == gate_index`
  match before the source-watch cap.

This is copied-slot / local positive-gate proof only. It is not whole-vector
terminality, image-effect proof, source-contribution proof, reducer closure, or
final acceptance / rejection logic.

## Repo-Local Artifacts

- Probe harness:
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/prefusion_20ca00_copied_sentinel_gate_probe.py`
- LLDB scripts:
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_28mm.lldb`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_35mm.lldb`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_70mm.lldb`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_150mm.lldb`
- Runners:
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/run_four_zoom.sh`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/run_wide.sh`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/run_70.sh`
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/run_150.sh`
- Verifier:
  `tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/verify_20ca00_copied_sentinel_gate.py`
- Raw output directory:
  `runs/prefusion_20ca00_copied_sentinel_gate/`

The admitted runtime JSON reports are:

- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_28mm.json`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_35mm.json`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_70mm.json`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_150mm.json`

The admitted runs also wrote Radiance HDR outputs:

- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_28mm.hdr`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_35mm.hdr`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_70mm.hdr`
- `runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_150mm.hdr`

Earlier exploratory launches that hit the known instrumentation-sensitive
`0x2e8cc0` family or stopped before the final watchpoint-stop compatibility
patch are not admitted by this note. Only the clean JSON/HDR packets listed
above are admitted.

## Runtime Scope

Each LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process <canonical-lri> <run-output>.hdr --profile 3 --export-fmt 3 --no-auto-lris`

All admitted runs use the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe:

1. Breaks at `0x21b92a` / `0x21b930` and arms source watchpoints only on
   completed `(-1.0, -1.0)` sentinel pairs.
2. Watches for those source pairs being copied by `0xe0ae0` under caller return
   `0x20d309`.
3. Reconstructs `source_index` from the source vector header and `gate_index`
   from the parent `0x20ca00` local at `rbp-0x2a0`.
4. Only when `source_index == gate_index`, arms a destination watchpoint on the
   copied slot computed from the `0xe0ae0` source/destination cursors.
5. Records whether that copied destination is later read at the positive
   coordinate gate `0x20d35e -> 0x20d363`, and single-steps the branch.

## Static Anchors

Installed-bundle disassembly proves the helper and gate identities used by the
probe:

```text
0xe0ae0: copies an 8-byte pair vector from source header r15 to destination header r14
0x20d2f9: leaq 0x28(%rbx), %rsi
0x20d2fd: leaq -0xe0(%rbp), %rdi
0x20d304: callq 0xe0ae0
0x20d309: return site after the second local vector copy
0x20d34d: movq -0xe0(%rbp), %r15
0x20d354: movq -0x2a0(%rbp), %rax
0x20d35e: ucomiss (%r15,%rax,8), %xmm0
0x20d363: jae 0x20d565
```

At the gate, `xmm0` is zero, so a copied x lane of `-1.0` yields `CF = 0` and
takes the `jae 0x20d565` skip branch.

## Runtime Results

| Zoom | Exit | Non-watch stops | Source watch hits | `0x20d309` source-copy hits | Index matches | Dest watchpoints | Dest watch hits | Gate hits | Gate skip hits | Source cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `0` | `4097` | `1912` | `0` | `0` | `0` | `0` | `0` | `1` |
| `35mm` | `0` | `0` | `4097` | `2224` | `0` | `0` | `0` | `0` | `0` | `1` |
| `70mm` | `0` | `0` | `310` | `244` | `1` | `1` | `301` | `1` | `1` | `0` |
| `150mm` | `0` | `0` | `4097` | `731` | `0` | `0` | `0` | `0` | `0` | `1` |

The `28mm`, `35mm`, and `150mm` no-match observations are capped source-watch
windows, not exhaustive whole-render negatives.

For the admitted `70mm` match:

- source watchpoint pair matched the `0xe0ae0` source cursor reconstruction
- `source_index == gate_index == 774`
- copied destination address was `140700206766128`
- copied destination pair at candidate time was `000080bf000080bf`
- the later gate read at `0x20d363` computed the same destination address
- gate pair still read `000080bf000080bf`
- runtime flags after `ucomiss` were `CF = 0`, `ZF = 0`, `PF = 0`
- single-step from `0x20d363` went to `0x20d565`

The repo-local verifier rechecks clean completion, exact copied-slot counts,
the admitted `70mm` gate identity / branch step, the scoped no-match windows in
the other tiers, and Radiance HDR output custody:

```text
$ python3 tools/lldb_probes/prefusion_20ca00_copied_sentinel_gate/verify_20ca00_copied_sentinel_gate.py
28mm: OK copy20d309=1912 matches=0 dest_gate_hits=0 source_cap=1
35mm: OK copy20d309=2224 matches=0 dest_gate_hits=0 source_cap=1
70mm: OK copy20d309=244 matches=1 dest_gate_hits=1 source_cap=0
150mm: OK copy20d309=731 matches=0 dest_gate_hits=0 source_cap=1
```

HDR verification:

```text
$ file runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_*.hdr
runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_28mm.hdr:  Radiance HDR image data
runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_35mm.hdr:  Radiance HDR image data
runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_70mm.hdr:  Radiance HDR image data
runs/prefusion_20ca00_copied_sentinel_gate/copied_sentinel_gate_150mm.hdr: Radiance HDR image data
```

## Proven Facts

1. The admitted `28mm`, `35mm`, `70mm`, and `150mm` runs completed with exit
   status `0`, no probe errors, no non-watchpoint stops, no drive step cap, and
   Radiance HDR output files.
2. All admitted runs armed three source watchpoints on completed sentinel pairs
   immediately after `0x21b92a -> 0x21b930`.
3. All admitted runs observed those watched sentinel pairs being copied by the
   second `0x20ca00` local vector copy at `0x20d304 -> 0xe0ae0 -> 0x20d309`.
4. In the admitted `70mm` run, one watched copied sentinel had
   `source_index == gate_index == 774`; the copied destination was later read by
   the positive-coordinate gate at `0x20d363`, still read as `(-1.0, -1.0)`, and
   stepped to skip target `0x20d565`.
5. In the admitted `28mm`, `35mm`, and `150mm` runs, no watched copied sentinel
   had `source_index == gate_index` before the source-watch cap.

## Safe Conclusion

The prior `0x20ca00` Ceres-setup classification can now be sharpened for one
sampled tele case: under the admitted `70mm` run, an exact watched copied
sentinel slot is selected by the local positive-coordinate gate and rejected by
the `0x20d363 -> 0x20d565` branch.

The wide tiers and `150mm` did not produce an exact copied-slot/gate-index match
within the admitted capped watched windows. That is useful negative evidence
against this narrow lead for those watched sentinels, but it is not an
exhaustive proof that no sentinel coordinate ever reaches the `0x20ca00` gate in
those tiers.

## Consequence For Blocker Work

Lane A should no longer treat the `0x20ca00` positive-coordinate gate as a fully
opaque possible reducer for the admitted `70mm` copied-sentinel sample: that
sample is a local sentinel skip, not Ceres contribution. The broader blocker
remains open because this does not prove whole-vector terminality, image/source
contribution consequences, semantic `src1` / `src2` contents, reducer closure,
or final acceptance/rejection.
