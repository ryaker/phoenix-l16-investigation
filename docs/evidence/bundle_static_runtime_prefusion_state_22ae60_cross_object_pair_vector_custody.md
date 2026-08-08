# Static + Runtime Proof: State `0x22ae60` Cross-Object Pair-Vector Custody

## Scope

This note follows two related custody facts for State body `0x22ae60`:

- construction-time shared-ptr handle identity between the two helper objects
  used by the State body, and
- selected watched pair allocations later read through both helper objects'
  keyed-record pair-vector paths.

The two helper objects are:

- the solver owner loaded from `inner+0x10`, and
- the sibling propagation object loaded from `inner+0x28`.

The admitted scope is narrow. Static construction proves the two helper objects
are built from the same upstream handles. New live State samples on all four
canonical Unit-1 focal tiers prove those handle equalities are still present
when `0x22ae60` executes; an exact-`28mm` Unit-2 sample supplies a second-body
discriminator. Reused same-address watch reports prove selected keyed
pair-vector allocations are read through both helper objects across all four
Unit-1 focal tiers, with an exact-`28mm` Unit-2 discriminator spanning the
second sibling call.

This is handle and selected same-address custody. It is not all-record sharing,
not public field naming, not image-effect proof, not reducer closure, and not
final-acceptance proof.

## Repo-Local Verifier

Verifier:

```text
tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_state_22ae60_cross_object_pair_vector_custody.py
```

The verifier pins the installed `libcp.dylib` SHA-256, checks exact Capstone
instruction anchors, verifies clean process/HDR custody for every reused and
new runtime report, distinguishes the four State call returns by stack VA, and
checks the live State handle-equality packets for both physical bodies.

Run:

```text
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_state_22ae60_cross_object_pair_vector_custody.py
```

Output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib sha256=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
Unit-1 28mm: OK same_addr=140552203736416 stages={'pre_owner': 0, 'first_sibling': 3, 'post_owner': 7}
Unit-1 35mm: OK same_addr=140202376136880 stages={'pre_owner': 0, 'first_sibling': 3, 'post_owner': 7}
Unit-1 70mm: OK same_addr=140437143093864 stages={'pre_owner': 10, 'first_sibling': 13, 'post_owner': 17}
Unit-1 150mm: OK same_addr=140593355573208 stages={'pre_owner': 10, 'first_sibling': 13, 'post_owner': 17}
Unit-2 exact 28mm: OK same_addr=140350346526968 stages={'pre_owner': 0, 'first_sibling': 3, 'post_owner': 7, 'second_sibling': 172} sibling_local_copy_hits=4
Unit-1 exact 28mm State handle: OK top_records=6832 top_handle=(140464094284696, 140464094284672) keyed_handle=(140464094293576, 140464094293552)
Unit-1 exact 35mm State handle: OK top_records=5993 top_handle=(140643713172664, 140643713172640) keyed_handle=(140643713184232, 140643713184208)
Unit-1 exact 70mm State handle: OK top_records=6503 top_handle=(140378992104248, 140378992104224) keyed_handle=(140378992116392, 140378992116368)
Unit-1 exact 150mm State handle: OK top_records=2399 top_handle=(140271972249048, 140271972249024) keyed_handle=(140271972237128, 140271972237104)
Unit-2 exact 28mm State handle: OK top_records=3422 top_handle=(140472692553016, 140472692552992) keyed_handle=(140472692587080, 140472692587056)
scope=shared pair-vector allocation across owner +0x10 and sibling +0x28 record loops; live Unit-1 four-focal shared-handle identity plus exact-28mm Unit-2 discriminator; all-record sharing, image effect, reducer closure, and final acceptance remain open
```

## Reused Runtime Evidence

Unit-1 canonical focal reports:

- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_28mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_35mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_70mm.json`
- `runs/prefusion_node_dest_20ca00_source_index/node_dest_20ca00_index_150mm.json`

Second-body discriminator:

- report:
  `runs/prefusion_node_dest_20ca00_gate_custody_unit2/node_dest_20ca00_gate_unit2_28mm.json`
- script:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_unit2_28mm.lldb`
- exact-focal Unit-2 LRI:
  `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri`
- Unit-2 intrinsics signature:
  `223961c6bce6153e...`

The Unit-2 run is the exact `28mm` counterpart identified by the tracked
two-body corpus verifier. It is used as a risk-based body discriminator, not as
a substitute for four focal tiers on the second body.

All five reports exited `0`, did not hit their drive-step cap, recorded no probe
errors, and wrote Radiance HDR output. Every admitted sample used below still
read the watched bytes as `000080bf000080bf`, or `(-1.0, -1.0)`.

## Live Handle Evidence

New handle-identity probes:

- Unit-1 four-focal runner:
  `tools/lldb_probes/calib_state_operator_runtime/run_state5_handle_identity_unit1_focals.sh`
- Unit-1 `28mm` plus Unit-2 exact-`28mm` runner:
  `tools/lldb_probes/calib_state_operator_runtime/run_state5_handle_identity_two_body.sh`
- shared callback:
  `tools/lldb_probes/calib_state_operator_runtime/state_operator_probe.py`
- Unit-1 scripts:
  `tools/lldb_probes/calib_state_operator_runtime/state5_handle_identity_unit1_28mm.lldb`
  through
  `tools/lldb_probes/calib_state_operator_runtime/state5_handle_identity_unit1_150mm.lldb`
- Unit-2 script:
  `tools/lldb_probes/calib_state_operator_runtime/state5_handle_identity_unit2_28mm.lldb`
- reports:
  `runs/state5_handle_identity_two_body/state5_handle_identity_unit1_{28,35,70,150}mm.json`
  plus
  `runs/state5_handle_identity_two_body/state5_handle_identity_unit2_28mm.json`

All five live handle runs completed with process exit `0`, no drive-step cap,
no probe errors, and Radiance HDR output. The Unit-1 runs use the canonical
`28mm`, `35mm`, `70mm`, and `150mm` LRIs. The Unit-2 run uses the exact-`28mm`
counterpart `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri`.

At the first `0x22ae60` State sample in each run, the verifier requires all four
live handle-equality groups to be true:

| Upstream inner handle | Solver-owner field | Sibling field | Meaning in this note |
|---|---|---|---|
| `inner+0x40` | `owner+0x00` | `sibling+0x00` | top-level `0x14` record-vector handle |
| `inner+0x50` | `owner+0x28` | `sibling+0x10` | keyed-record pair-vector tree handle |
| `inner+0x30` | `owner+0x38` | `sibling+0x20` | shared auxiliary handle |
| `inner+0xa0` | `owner+0x48` | `sibling+0x30` | shared auxiliary handle |

The live top-level record vector is readable and `0x14`-stride in every run:

| Run | Top-level records |
|---|---:|
| Unit-1 exact `28mm` | `6832` |
| Unit-1 exact `35mm` | `5993` |
| Unit-1 exact `70mm` | `6503` |
| Unit-1 exact `150mm` | `2399` |
| Unit-2 exact `28mm` | `3422` |

These counts are admitted report facts, not algorithm constants.

## Static Construction Map

Installed-bundle anchors now make the live handle equalities expected rather
than accidental:

- `0x3fc980` loads the owner-side outer object, checks byte `+0x3fa`, adds
  `0x280`, and calls `0x226c70`.
- `0x226c70` saves that `this+0x280` object in `r12`; at `0x226f8f`, it installs
  State `runReferenceGroupCams::$_5` address point `0x6585d8`, and stores
  `r12` as closure field `+0x8`.
- `0x22ae60` later loads that same closure field with
  `mov rbx, qword ptr [rdi+8]`.
- `0x225160` constructs the `this+0x280` inner object, then allocates the
  solver owner at `inner+0x10` through `0x20ad60` and the sibling object at
  `inner+0x28` through `0x239a90`.

The deterministic mapping checked by the verifier is:

| Upstream inner field | `0x20ad60` / owner destination | `0x239a90` / sibling destination |
|---|---|---|
| `inner+0x30` | `owner+0x38/+0x40` | `sibling+0x20/+0x28` |
| `inner+0xa0` | `owner+0x48/+0x50` | `sibling+0x30/+0x38` |
| `inner+0x40` | `owner+0x00/+0x08` | `sibling+0x00/+0x08` |
| `inner+0x50` | `owner+0x28/+0x30` | `sibling+0x10/+0x18` |
| `inner+0x100` | `owner+0x70/+0x74` only | not passed |

The owner constructor also initializes `owner+0x78/+0x7c` to
`(-1.0f, -1.0f)`. The separate phase-reuse note covers the later use of that
owner range; this note uses it only as a construction anchor.

## Static Object Split

Installed-bundle instructions prove the State sequence:

| State site | Object argument | Call | Return site |
|---:|---|---:|---:|
| `0x22ae6a` | `*(inner+0x10)` | `0x20ada0` | `0x22ae73` |
| `0x22ae73` | `*(inner+0x28)` | `0x239ac0` | `0x22ae83` |
| `0x22ae83` | `*(inner+0x10)` | `0x20bd60` | `0x22ae8c` |
| `0x22ae8c` | `*(inner+0x28)` | `0x239ac0` | `0x22ae9c` |

The two object pointers are loaded from different fields. Static code does not
prove that the pointers themselves are equal, and this note does not claim that.

The pair-vector source paths are:

- `0x20ada0` saves the owner in `r15`, traverses the owner tree at `owner+0x28`,
  and passes current keyed record `+0x28` to `0xe0ae0` at `0x20adf1`.
- `0x20bd60` saves the same owner in `r15`, traverses the same owner field
  `owner+0x28`, and passes current keyed record `+0x28` to `0xe0ae0` at
  `0x20bff5`.
- `0x239ac0` saves the sibling object in `r12`, traverses the keyed-record tree
  reached through `sibling+0x10`, and passes current keyed record `+0x28` to
  `0xe0ae0` at `0x239c2f`.
- Nested helper `0x239e00` can also copy a keyed node's pair vector through
  `0x239fd4 -> 0xe0ae0`.

Separately, `0x239e00` reads `*(sibling+0x00)` and advances that source by
`0x14` bytes per record. The static construction map and the new live packets
now equate the sibling top-level vector handle with `owner+0x00` for sampled
State entries across all four Unit-1 focal tiers and the exact-`28mm` Unit-2
run. That still does not prove that every record in that vector later shares
every downstream allocation or has final image effect.

## Same-Address Runtime Join

For each Unit-1 focal report, the verifier selects the admitted matched pair
address and requires this ordered same-address sequence:

1. source read under `0x20adf6`, returning to State at `0x22ae73`;
2. source read under `0x239c34`, returning to State at `0x22ae83`;
3. source read under `0x20bffa`, returning to State at `0x22ae8c`.

The static anchors above identify those reads respectively as the solver-owner
record tree, the sibling record tree, and the solver-owner record tree again.
The identical watched runtime address therefore occurs in both objects' keyed
record pair-vector paths across all four canonical focal tiers on Unit-1.

The exact-focal Unit-2 `28mm` report has a larger watch window and proves the
fourth stage too:

4. source read under `0x239c34`, returning to State at `0x22ae9c`.

Thus the selected Unit-2 address is observed in the sibling propagation path
both before and after the owner `0x20bd60` phase. The same report also records
four same-address reads under nested sibling-local copy return `0x239fd9`.

## Proven Facts

1. State body `0x22ae60` alternates between a solver owner from `inner+0x10`
   and a sibling propagation object from `inner+0x28` in the order shown above.
2. The solver owner and sibling object are constructed from shared upstream
   handles: `inner+0x40` feeds both top-level `0x14` record-vector handles, and
   `inner+0x50` feeds both keyed pair-vector tree handles.
3. Live State samples across all four Unit-1 focal tiers and exact-`28mm`
   Unit-2 prove those shared handle identities are still present at the
   `0x22ae60` entry sample.
4. `0x20ada0` and `0x20bd60` copy pair vectors from keyed records under the
   solver owner's `+0x28` tree; `0x239ac0` copies pair vectors from keyed records
   under the sibling object's `+0x10` tree.
5. One admitted watched pair allocation per canonical Unit-1 focal tier is read
   at the same runtime address by the owner path, then sibling path, then owner
   path in State order.
6. One exact-focal Unit-2 `28mm` watched allocation follows that same sequence
   and is read by the second sibling call after `0x20bd60` as well.

## Safe Conclusion

The solver-owner and sibling objects used by State `0x22ae60` are different
objects, but they are not independent record graphs. Static construction and
live samples across the Unit-1 focal quartet plus exact-`28mm` Unit-2 prove
shared top-level and keyed-tree handles, while reused same-address watch packets
prove selected pair-vector allocations move through both keyed paths across the
State phase boundary. This removes the unproven "independent sibling copy"
interpretation for those selected records and supplies a concrete post-solve
propagation route.

The result does not establish all-record sharing, and it does not give these
fields public semantic names. Image or source contribution, the missing `src1` /
`src2` reducer, and final acceptance or rejection remain open.
