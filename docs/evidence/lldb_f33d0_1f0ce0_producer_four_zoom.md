# LLDB Evidence: `0x1f0ce0 -> 0xf33d0` CalibStage Producer, Four Zoom

## Scope

This note follows the constructor-side `0xf33d0` producer at `0x1f0ce0`, using
the enriched four-zoom `state_helpers_23c5f0_f33d0_runtime` packets plus a
repo-local static byte verifier.

The narrow question is why the Lane B public-meaning audit admits exact public
K/pose copies for wide A1-A5 and exact public pose copies for B4 / tele C5, but
does not admit exact public K-matrix copies for B4/C5.

Bottom line: the current proof admits a sharper boundary. `0x1f0ce0` writes the
same source records into both accepted `0xf33d0` selector banks for each
captured key. At this producer edge, wide A1-A5 packets are exact public
K/pose records, but B/C K packets are not exact public fixed32-sequence copies.
B4 pose is stable and exact-public across all four focal tiers while B4 K is
zoom-variant across all four tiers. Tele C5 pose is stable and exact-public
across the tele tiers while C5 K is zoom-variant across the tele tiers.

This proves a derived / producer-local boundary for the non-exact B4/C5 K
packets. It does not decode the complete numeric derivation formula, assign
public protobuf field names to the full `state+0xe0` / `state+0x448` records,
or close the Lane B public-meaning blocker.

## Artifacts

- Static/runtime verifier:
  [verify_1f0ce0_producer.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/verify_1f0ce0_producer.py)
- Runtime probe that captured the packets:
  [state_helper_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_probe.py)
- Runtime harness:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/run_four_zoom.sh)
- Raw runtime reports:
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_28mm.json`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_35mm.json`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_70mm.json`,
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_150mm.json`
- Companion public-origin audit verifier:
  [lane_b_index5_public_meaning_audit.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lane_b_index5_public_meaning_audit.py)
- Companion evidence:
  [lldb_index5_depth_public_meaning_gap_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md)

## Verification

Command:

```bash
python3 tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/verify_1f0ce0_producer.py
```

Verifier output:

```text
static_1f0ce0_calls_and_selector_setup=OK
28mm: OK producer_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 selector_pair_source_equal=10/10 full_public=A1,A2,A3,A4,A5 pose_only_public=B4 k_not_public=B1,B2,B3,B4,B5
35mm: OK producer_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 selector_pair_source_equal=10/10 full_public=A1,A2,A3,A4,A5 pose_only_public=B4 k_not_public=B1,B2,B3,B4,B5
70mm: OK producer_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 selector_pair_source_equal=10/10 full_public=none pose_only_public=B4,C5 k_not_public=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5
150mm: OK producer_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 selector_pair_source_equal=10/10 full_public=none pose_only_public=B4,C5 k_not_public=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5
cross_tier=B4_pose_stable_K_variants4,C5_pose_stable_K_variants2,A1-A5_wide_stable
```

The verifier checks:

- the installed `libcp.dylib` bytes still contain the relevant direct call
  edges inside `0x1f0ce0`, including:
  `0x1f0cf3 -> 0xf3360`,
  `0x1f0d31 -> 0x1f0b00`,
  `0x1f0e15 -> 0xf3300`,
  `0x1f0e2a -> 0x1f96e0`,
  `0x1f0ff0 -> 0xf3350`,
  the branch-local helper calls `0x1f1072 -> 0x1f0a00`,
  `0x1f1090 -> 0xf32f0`,
  `0x1f109c -> 0x1c1860`,
  `0x1f10b2 -> 0x1c79e0`, and the two `0xf33d0` calls;
- the selector setup immediately before the two `0xf33d0` calls is still
  selector `0` at `0x1f1328` and selector `1` at `0x1f134b`;
- after the already-bounded `0xf3350` accessor call, the static byte window
  still loads scale-like fields from returned pointer offsets `+0x18` and
  `+0x1c`, multiplies K stack fields `0`, `4`, `2`, and `5`, and passes the
  same stack locals `rbp-0xb8` / `rbp-0x278` / `rbp-0x288` into both final
  `0xf33d0` copies;
- every four-zoom raw report exits cleanly with no probe errors or step cap;
- each focal tier has exactly ten producer-edge selector-`0` packets from
  return `0x1f132d` and ten selector-`1` packets from return `0x1f1350`;
- for every captured key, the selector-`0` and selector-`1` packets have
  identical source-record raw values;
- the K-like source record has the shape
  `[fx, 0, cx, 0, fy, cy, 0, 0, 1]` with `fx == fy`;
- recursive public fixed32 sequence indexing over the canonical LRI
  calibration payload classes admits full exact public records only for wide
  A1-A5;
- B4 has exact public pose records but non-exact K records in all four focal
  tiers;
- C5 has exact public pose records but non-exact K records in the tele tiers;
- B4 pose is stable across all four focal tiers while B4 K has four distinct
  tier-specific variants;
- C5 pose is stable across `70mm` / `150mm` while C5 K has two distinct
  tele-tier variants;
- A1-A5 producer-edge records are stable across `28mm` / `35mm`.

## Static Boundary

The relevant static shape of `0x1f0ce0` is:

```text
0x1f0ce0
  -> 0xf3360
  -> 0x1f0b00
  -> optional/helper record preparation through 0x1f96d0 / 0x1f96e0
  -> 0xf3350
  -> load returned fields +0x18 / +0x1c and multiply K fields 0,4,2,5
  -> optional branch-local helper path through 0x1f0a00 / 0x1c1860 / 0x1c79e0
  -> 0x1f1328 -> 0xf33d0 with selector 0
  -> 0x1f134b -> 0xf33d0 with selector 1
```

The existing accessor proof bounds `0xf3350` as the `object+0x10c` accessor.
The refreshed verifier also proves the final `0xf33d0` arguments are the same
K / pose / three-int stack locals for selector `0` and selector `1`. This note
only admits that the `0x1f0ce0` producer uses that accessor and scale window
before the final two `0xf33d0` copies. It does not fully decode the numerical
source of every K variant.

## Runtime Boundary

The producer-edge key sets are:

| Zoom | Producer keys at `0x1f132d` / `0x1f1350` |
|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |

The tele producer-edge set excludes public-fired `C6`, matching the narrower
`0xf33d0` destination-key boundary already recorded by the public-meaning
audit.

For each key in each focal tier, the source records copied by selector `0` and
selector `1` are byte-identical at the producer edge. Therefore this
constructor-side edge does not show selector `0` and selector `1` as two
different public payloads; it shows one computed / selected packet copied into
both accepted `CalibStage` banks.

## Public-Origin Consequence

The public-origin result is component-scoped:

| Zoom | Full exact public K/pose records | Exact public pose only | K not exact-public at this edge |
|---|---|---|---|
| `28mm` | `A1,A2,A3,A4,A5` | `B4` | `B1,B2,B3,B4,B5` |
| `35mm` | `A1,A2,A3,A4,A5` | `B4` | `B1,B2,B3,B4,B5` |
| `70mm` | none | `B4,C5` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |
| `150mm` | none | `B4,C5` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |

The most important cross-tier guardrails are:

- B4 pose is exact-public and stable across all four tiers; B4 K is
  tier-specific with four distinct raw packets.
- C5 pose is exact-public and stable across the tele tiers; C5 K is
  tier-specific with two distinct raw packets.
- A1-A5 full packets are exact-public and stable across the wide tiers.

This explains why a byte/sequence public-origin check admits the B4/C5 pose
components but rejects B4/C5 K matrices: the non-exact K packets are already
zoom-specific at the producer edge, not merely corrupted by a later consumer.

## Non-Claims

- At the time of this packet, it did not assign the public names `factory` or
  `current` to selector `0` or selector `1`. The superseding complete-writer
  census and two-body bank-watch proof now maps `0=factory` and `1=current`;
  see `bundle_static_runtime_calibstage_public_names_two_body.md`.
- This does not prove a public protobuf field path for the full `state+0xe0`
  object family.
- This does not prove a public protobuf field path for `state+0x448`.
- This does not prove a public origin for tele `C6` in this `0xf33d0` path.
- This does not fully decode the formula that produces the B/C K variants.
- This does not close the index-5 lookup/source public meaning gap or upgrade
  any blocker status.

## Safe Statement

The `0x1f0ce0` producer edge localizes the B4/C5 K public-origin gap: the same
computed source records are copied into both accepted `0xf33d0` selector banks,
wide A1-A5 records are exact public K/pose copies, B4/C5 pose records are exact
public copies, and B4/C5 K records are zoom-variant non-exact packets before
downstream State-helper composition.
