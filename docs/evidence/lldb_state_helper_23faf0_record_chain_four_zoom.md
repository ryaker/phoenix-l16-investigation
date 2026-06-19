# LLDB Evidence: `0x23c5f0` Record Chain Through `0x23faf0` Into Local Tree Nodes

## Scope

This proof follows:

- [lldb_state_helpers_23c5f0_f33d0_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helpers_23c5f0_f33d0_four_zoom.md)
- [lldb_state_helper_23c5f0_exit_snapshot_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helper_23c5f0_exit_snapshot_four_zoom.md)
- [lldb_state_helper_f34e0_match_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helper_f34e0_match_four_zoom.md)
- [bundle_proof_iramp_23faf0_composition_helper.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_23faf0_composition_helper.md)

It tests the next internal handoff inside `0x23c5f0`: the selected helper
record returned through `0x264440 -> 0x264270 -> 0xf34e0`, the subsequent
`0x23faf0` record-composition call, and the local tree-node field writes that
follow.

This is internal State-helper record-custody proof. It is not proof of
post-`0x23c5f0` downstream image effect, source contribution, reducer closure,
or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [record_chain_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_probe.py)
- Runtime LLDB scripts:
  [record_chain_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_28mm.lldb),
  [record_chain_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_35mm.lldb),
  [record_chain_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_70mm.lldb),
  [record_chain_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_150mm.lldb)
- Runtime harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/run_four_zoom.sh)
- Runtime verifier:
  [verify_record_chain.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/verify_record_chain.py)
- Raw runtime outputs:
  `runs/state_helper_23faf0_record_chain/record_chain_28mm.{log,json,hdr}`,
  `runs/state_helper_23faf0_record_chain/record_chain_35mm.{log,json,hdr}`,
  `runs/state_helper_23faf0_record_chain/record_chain_70mm.{log,json,hdr}`,
  `runs/state_helper_23faf0_record_chain/record_chain_150mm.{log,json,hdr}`

The `.lldb` scripts launch with `--no-auto-lris`.

## Invocation

```bash
bash tools/lldb_probes/state_helper_23faf0_record_chain/run_four_zoom.sh
python3 tools/lldb_probes/state_helper_23faf0_record_chain/verify_record_chain.py
```

The admitted runtime facts below come from the JSON reports listed in the
Artifacts section. Log files independently show each run wrote a `10432x7824`
HDR output and exited with status `0`.

The current rerun patches the probe to capture the pre-call `0x23faf0`
left-record pointer only at `after_264440`, where static disassembly still has
`rbx+0x20` as the left argument. It deliberately does not call later
post-return `%rbx+0x20` values the left input.

## Static Boundary

Installed-bundle static disassembly shows this local sequence inside
`0x23c5f0`:

- `0x23cba6 -> 0x264440`, returning at `0x23cbab`.
- `0x23cbaf..0x23cbbc` prepares and calls `0x23faf0`:
  `rdi = rbp-0x378`, `rsi = rbx+0x20`, and `rdx = r15`.
- Runtime packets at the first two sites prove `r15 == rbp-0x420`, so this
  call is observed as `0x23faf0(rbp-0x378, rbx+0x20, rbp-0x420)` under the
  tested path.
- `0x23cbc1` is the return site after `0x23faf0`.
- `0x23cdf3..0x23ce2a` loads fields from `rbp-0x378` and nearby scratch.
- `0x23ce2e..0x23ce56` writes converted fields into local tree-node offsets
  `+0x28..+0x98`.
- `0x23ce5e` writes `0` to node `+0xa0`.
- `0x23d01e` later writes `ecx` to another node's `+0xa0`, returning control
  to `0x23d025`.

The runtime proof below tests the values at the four sites:

| VA | Probe site name |
|---|---|
| `0x23cbab` | `after_264440` |
| `0x23cbc1` | `after_23faf0` |
| `0x23ce5e` | `after_node_field_writes` |
| `0x23d025` | `after_node_a0_write` |

## Runtime Health

All four canonical no-auto-LRIS bridge HDR runs completed, wrote `10432x7824`
HDR output, and exited with status `0`.

| Zoom | LRI | JSON exit | Hits per watched site | Four-site groups | JSON errors | Step cap |
|---|---|---:|---:|---:|---:|---|
| `28mm` | `L16_02130` | `0` | `26` | `26` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `26` | `26` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `26` | `26` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `26` | `26` | `0` | `false` |

The LLDB breakpoint hit counts and the probe's internal count fields match at
all four watched VAs in every admitted JSON. No run hit the configured cap.

## Group Invariants

Every admitted JSON contains exactly `104` sampled events, grouped into `26`
ordered four-site chains. Every chain has the same order:

```text
after_264440 -> after_23faf0 -> after_node_field_writes -> after_node_a0_write
```

For every four-site chain in every focal run:

- `rbp-0x2d0` local integer is stable across all four sites.
- `rbp-0x430` source-object pointer is stable across all four sites.
- At `after_264440`, the probe captures the pre-call argument tuple
  `0x23faf0(dst=rbp-0x378, left=rbx+0x20, right=rbp-0x420)`, and the captured
  record addresses match those three computed pointers in every group.
- The captured right record at `rbp-0x420` is byte-stable across the
  `0x23faf0` call in every group.
- `rbp-0x378` differs between `after_264440` and `after_23faf0`, proving the
  current output record is updated across the `0x23faf0` call in every group.
- `rbp-0x378` remains unchanged between `after_23faf0` and both later node
  sites.
- Node `i32_0x20` equals the sampled `rbp-0x2d0` local integer in every group.
- At `after_node_field_writes`, node `i32_0xa0` is `0` in every group.
- At `after_node_a0_write`, the same node address is preserved and all sampled
  copied fields stay stable except `i32_0xa0`.

The four focal runs have these local-key counts at every watched site:

| Zoom scope | Local-key count table |
|---|---|
| `28mm`, `35mm` | `{1:4, 2:4, 3:4, 4:4, 5:2, 6:2, 7:2, 8:2, 9:2}` |
| `70mm`, `150mm` | `{5:4, 6:4, 7:4, 9:4, 10:2, 11:2, 12:2, 13:2, 14:2}` |

## `0x23faf0` Output To Node Field Copy

For all `26` groups in each focal run, the node fields at
`after_node_field_writes` match the `rbp-0x378` output record captured at
`after_23faf0` for the directly mapped coordinate-like fields:

| Node field | Runtime-matched source field |
|---|---|
| node `f64_0x28x2` | `rbp-0x378` `f32_0x00x8[0:2]` |
| node `f64_0x38x2` | `rbp-0x378` `f32_0x00x8[2:4]` |
| node `f64_0x48x2` | `rbp-0x378` `f32_0x00x8[4:6]` |
| node `f64_0x58x2` | `rbp-0x378` `f32_0x00x8[6:8]` |

This gives `26 / 26` matched groups per focal run and `104 / 104` matched
groups across the canonical four-zoom set.

The probe does not assign public semantic names to these fields. Static
disassembly shows additional writes to node `+0x68..+0x98`, but this runtime
claim is limited to the mapped fields above plus the `i32_0x20` and `i32_0xa0`
observations.

## Final `+0xa0` Values

The later `0x23d01e` store changes node `+0xa0` from the earlier forced `0` to
the following values under the tested four-zoom runs:

| Zoom | Final node `i32_0xa0` counts |
|---|---|
| `28mm` | `{0:10, 9:8, 11:8}` |
| `35mm` | `{0:10, 9:8, 11:8}` |
| `70mm` | `{0:8, 9:8, 11:10}` |
| `150mm` | `{0:8, 9:8, 11:10}` |

By local key:

| Zoom scope | Final node `i32_0xa0` by local key |
|---|---|
| `28mm`, `35mm` | `1..4 -> {0:2, 9:2}`; `5 -> {0:2}`; `6..9 -> {11:2}` |
| `70mm`, `150mm` | `5,6,7,9 -> {0:2, 9:2}`; `10..14 -> {11:2}` |

This table is a runtime classification/value observation only. It does not
assign public meanings to `0`, `9`, `11`, `rbp-0x2d0`, or node `+0xa0`.

## Public Component Audit

The refreshed verifier checks the full 0xa4-byte source-record spans for the
pre-call left record, right record, output-before record, and output-after
record in all 26 groups per focal tier. It also compares K / rotation /
translation-shaped components against the same component-specific public
32,832-byte intrinsics-block records used by
[lldb_index5_depth_public_meaning_gap_audit_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md).

Verifier output:

The verifier also requires each admitted paired output file to start with the
Radiance HDR magic bytes.

```text
28mm: OK groups=26 full_record_lri_hits=0/104 component_nonmatches=210/312 pre_left=translation:A1x26 right=k:A2x1,A3x1,A4x1,A5x3|rotation:A2x1,A3x1,A4x1,A5x2,B4x2|translation:A2x4,A3x4,A4x4,A5x4,B4x2 output_post=rotation:A2x1,A3x1,A4x1,A5x2|translation:A2x4,A3x4,A4x4,A5x4,B4x2
35mm: OK groups=26 full_record_lri_hits=0/104 component_nonmatches=210/312 pre_left=translation:A1x26 right=k:A2x1,A3x1,A4x1,A5x3|rotation:A2x1,A3x1,A4x1,A5x2,B4x2|translation:A2x4,A3x4,A4x4,A5x4,B4x2 output_post=rotation:A2x1,A3x1,A4x1,A5x2|translation:A2x4,A3x4,A4x4,A5x4,B4x2
70mm: OK groups=26 full_record_lri_hits=0/104 component_nonmatches=284/312 pre_left=translation:B4x26 right=rotation:C5x1|translation:C5x1 output_post=none
150mm: OK groups=26 full_record_lri_hits=0/104 component_nonmatches=284/312 pre_left=translation:B4x26 right=rotation:C5x1|translation:C5x1 output_post=none
```

Admitted scope:

- no checked full 0xa4-byte source-record span is an exact byte copy of any
  canonical LRI calibration payload class;
- exact public component copies do survive inside this helper chain:
  pre-call left-record translations match A1 at `28mm` / `35mm` and B4 at
  `70mm` / `150mm`; the right record carries the listed wide A2-A5 K/pose and
  B4 pose component matches, plus one C5 pose component match in each tele
  tier;
- many checked components remain non-matches, and the composed post-`0x23faf0`
  tele output has no component-specific exact public match under this verifier.

This is component-level public-origin evidence only. It is not a full source
record public field decode, and it does not name `state+0xe0` or `state+0x448`
as public protobuf structures.

## Proven Boundary

- Under complete accepted no-auto-LRIS bridge HDR runs at `28mm`, `35mm`,
  `70mm`, and `150mm`, the `0x23c5f0` internal path after `0x264440` updates
  `rbp-0x378` through `0x23faf0`.
- The `0x23faf0` output record at `rbp-0x378` is then materialized into local
  tree nodes through the static `0x23ce2e..0x23ce56` write window.
- The sampled node coordinate-like fields `+0x28..+0x58` match the
  `rbp-0x378` output record in all admitted groups.
- Node `i32_0x20` equals the local integer sampled at `rbp-0x2d0` in all
  admitted groups.
- Node `+0xa0` is first set to `0` at `0x23ce5e`, then later receives the
  observed `{0,9,11}` distribution at `0x23d01e`.
- The refreshed verifier binds the pre-call `0x23faf0` left/right/output
  record pointers at `after_264440` and proves no checked full source-record
  span is an exact LRI calibration-payload byte copy, while admitting only the
  component-specific public matches listed above.

## Non-Claims

- This does not assign public names or semantics to `rbp-0x2d0`,
  `rbp-0x378`, `rbp-0x420`, node `i32_0x20`, node `i32_0xa0`, `CalibStage`,
  or any public State value.
- This does not prove that `state+0xe0` or `state+0x448` are public protobuf
  records; the admitted public-origin bridge remains component-scoped.
- This does not prove post-`0x23c5f0` downstream image effect.
- This does not prove source contribution, reducer closure, final
  acceptance/rejection, or merge parity.
- This does not prove behavior outside the accepted canonical no-auto-LRIS
  bridge HDR quartet.
- This does not close `CLM-PREFUSION-002`.

## Consequence For Blocker Work

The `0x23c5f0` helper chain is now bounded one step deeper than the prior
`0xf34e0` custody edge: copied selector-`1` destination objects feed an
internal `0x264440 -> 0x264270 -> 0xf34e0` path, the resulting helper record is
composed through `0x23faf0`, and the composed record is materialized into local
tree nodes. The remaining Lane A work is to follow those nodes, or their
derived vectors/records, to a proven post-helper image/source effect,
distributed reducer behavior, or final acceptance/rejection decision.
