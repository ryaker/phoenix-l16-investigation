# Bundle + LLDB Proof: Prefusion Node-Destination `0x20ca00` Gate, Selected Cross-Unit Validation

## Scope

This note asks whether the selected same-address sentinel-gate result admitted
for the Unit-1 canonical quartet is specific to that physical body.

It uses selected Unit-2 captures from the independently identified second body
in `bundle_proof_two_unit_corpus_static.md`. Two rows are same-name body
counterparts rather than exact-focal counterparts; this is deliberate
cross-body risk sampling for this probe, not a full exact-focal Unit-2 matrix.
The selected Unit-2 runtime set is:

| Role | Runtime label | Actual header focal | Unit-2 LRI |
|---|---|---:|---|
| wide anchor | exact `28mm` | `28` | `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` |
| observed divergent same-name counterpart | prior `35mm` label | `74` | `/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri` |
| tele same-name counterpart | prior `70mm` label | `149` | `/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri` |

Unit-2 has intrinsics signature `223961c6...`; the canonical Unit-1 captures
have signature `722a6e72...`. The two units carry different calibration values.
The selected captures were made on different dates and scenes, so any runtime
difference is a **cross-unit twin-capture difference**, not proof that physical
body identity alone caused it.

The exact-focal Unit-2 representatives for focal-tier work are listed in
`bundle_static_lane_b_crossunit_lri_public_carriers.md`. The Unit-2 `150mm`
crop-tier run was intentionally stopped after the wide and tele discriminators
completed. Its partial zero-byte output and log were discarded and are not used
by the verifier.

## Selection Rationale

This is risk-based cross-unit validation, not a blanket repeat of every focal
tier for every proof:

1. Exact `28mm` samples the wide anchor regime.
2. The same-name `L16_03434` counterpart, with actual focal `149`, samples the
   tele regime under a second physical body.
3. The same-name `L16_03041` counterpart, with actual focal `74`, is retained
   because the first Unit-2 run exposed a route-incidence difference from the
   Unit-1 canonical `35mm` run.
4. A second Unit-2 `L16_03041` run explicitly targets the same copied pair indices
   `11..14` to test whether the first exact gate match is stable under probe
   steering.

## Repo-Local Artifacts

- Shared probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- Unit-2 generic scripts:
  `node_dest_20ca00_gate_unit2_28mm.lldb`,
  `node_dest_20ca00_gate_unit2_35mm.lldb`, and
  `node_dest_20ca00_gate_unit2_70mm.lldb`
- Targeted repeat:
  `node_dest_20ca00_gate_unit2_target_35mm.lldb`
- Selected rerunner:
  `run_20ca00_gate_unit2_selected.sh`
- Strict comparison verifier:
  `verify_node_dest_20ca00_gate_crossunit_selected.py`
- Unit-2 generic raw reports:
  `runs/prefusion_node_dest_20ca00_gate_custody_unit2/`
- Unit-2 targeted-repeat raw report:
  `runs/prefusion_node_dest_20ca00_gate_target_custody_unit2/`

The verifier also reuses the already admitted Unit-1 selected reports. Raw
reports remain ignored under `runs/`; the probe, verifier, and this evidence
note are the durable repo-owned custody chain.

## Runtime Results

| Unit | Zoom/run | Same-address copied indices | `0x20d309` packets | Match/gate result | Scope |
|---|---|---|---:|---|---|
| Unit-1 | `28mm` selected | includes `5394` | `1258` | index `5394`, full-sentinel gate skip | admitted positive |
| Unit-1 | `35mm` generic | `278,300,2938,3165` | `2874` | no match before cap | capped negative |
| Unit-1 | `70mm` generic | includes `77` | `393` | index `77`, full-sentinel gate skip | admitted positive |
| Unit-2 | `28mm` generic | `607,768,896,933` | `661` | no match before cap | capped negative |
| Unit-2 | same-name `L16_03041`, focal `74`, generic | `11,12,13,14` | `11` | index `12`, full-sentinel gate skip | admitted positive |
| Unit-2 | same-name `L16_03041`, focal `74`, targeted repeat | `11,12,13,14` | `3114` | no match before cap | scheduling-sensitive repeat |
| Unit-2 | same-name `L16_03434`, focal `149`, generic | `3149,5737,5797,6310` | `2671` | no match before cap | capped negative |

The positive Unit-2 same-name `L16_03041` packet proves:

- copied finite bytes at pair index `12` are `0000b94300006143`,
- the same runtime source address is later full `(-1.0, -1.0)`,
- `source_index == gate_index == 12`,
- the computed destination pair is full sentinel,
- the gate computes that same destination address,
- the gate flags have `CF=0`, `ZF=0`, and `PF=0`,
- and one instruction step reaches `0x20d363 -> 0x20d565`.

The targeted repeat proves that exact match incidence is not stable under this
watchpoint schedule: the same copied indices `11..14` remained full sentinels,
but none matched a parent gate index in `3114` captured source-copy packets
before the `4096`-watch-stop cap.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_gate_crossunit_selected.py
Unit-1: OK 28mm=index5394/gate, 35mm=no-match/2874/cap, 70mm=index77/gate
Unit-2: OK 28mm=no-match/661/cap, 35mm=index12/gate, 70mm=no-match/2671/cap
Unit-2 35mm targeted repeat: OK indices=11,12,13,14 no-match/3114/cap
cross-unit mechanism: OK positive_same_address_counts=3,4,4
```

The verifier checks clean process completion, Radiance HDR custody, finite
copied bytes, same-address sentinelization, source/gate index identity,
computed destination identity, full sentinel bytes at the gate, branch flags,
and exact `0x20d363 -> 0x20d565` stepping for every admitted positive packet.
It also enforces the cap-limited scope of every no-match row.

## Proven Facts

1. The selected `0x20ca00` full-sentinel local gate-skip mechanism is observed
   on both physical units: Unit-1 at selected `28mm` / `70mm` representatives
   and Unit-2 at one complete same-name `L16_03041` representative with actual
   focal `74`.
2. The first Unit-2 same-name `L16_03041` run has an exact same-address positive packet at
   index `12`; the corresponding targeted repeat over indices `11..14` has no
   match before its watch cap.
3. Unit-1 and Unit-2 selected captures do not preserve the same positive/no-match
   pattern under these probes.
4. Therefore copied pair indices, match frequency, and runtime incidence are
   runtime/probe observations, not stable algorithm constants or body labels.

## Safe Conclusion

Concern that the local sentinel-gate mechanism was merely a Unit-1 artifact is
narrowed: the same finite-copy to same-address sentinel to computed-destination
to `0x20d565` skip chain is independently observed on Unit-2.

The result does **not** establish unit-invariant match frequency, all-pairs
terminality, or body-caused route differences. Different capture content,
calibration, and instrumentation scheduling remain confounded. It also does not
prove downstream image/source contribution, reducer closure, or final
acceptance/rejection.
