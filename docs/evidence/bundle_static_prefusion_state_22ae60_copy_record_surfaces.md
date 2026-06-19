# Static + Reused Runtime Proof: Prefusion State `0x22ae60` Copy / Record Surfaces

## Scope

This note refines the State-family copy/record propagation bucket already admitted in
[bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md).

It classifies the sampled `0xe0ae0` copy callers reached from the corrected
`CalibDataProcessor::State()` body `0x22ae60` and its immediate helper surfaces.

This is not reducer closure, final image-effect proof, source-contribution proof,
whole-vector terminality proof, or final acceptance / rejection logic.

## Repo-Local Artifacts

Runtime packets reused from the admitted downstream-watch proof:

- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json`
- `runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json`

Verifier:

- `tools/lldb_probes/prefusion_node_sentinel_downstream_watch/verify_state_22ae60_copy_surfaces.py`

Fresh static captures:

- `runs/prefusion_state_22ae60_point_ba/static_disasm_22ae60_22aeb0.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_20bd60_20c800.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_25e4b0_25e5d0.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_20dbe0_20de10.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_20c800_20d480.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_20c880_20cfe0_focus.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_20d000_20d380_focus.log`
- `runs/prefusion_state_22ae60_point_ba/static_disasm_239ac0_23a080.log`

The fresh captures were produced from the installed bundle:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

## Runtime Reuse

The admitted downstream-watch runs all completed cleanly and sampled `0xe0ae0`
copy-loop stops with still-sentinel pairs.

This invariant was rerun for the `0x20bd60` post-copy site:

```bash
jq -s -e 'all(.[]; .process_exit_status == 0 and (.errors|length == 0) and .drive_hit_step_cap == false) and all(.[]; ([.watchpoint_samples[] | select(.stack[0].libcp_va >= 920288 and .stack[0].libcp_va < 920608 and .stack[1].libcp_va == 2146298)] | length) > 0)' runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_28mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_35mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_70mm.json runs/prefusion_node_sentinel_downstream_watch/node_sentinel_downstream_150mm.json
```

It returned `true`.

The repo-local verifier rechecks clean completion, exact sampled caller buckets,
still-sentinel pair bytes for every admitted caller-bucket sample, the
`0x20bd60` post-copy invariant, the presence of the static anchor captures, and
Radiance HDR output custody:

```text
$ python3 tools/lldb_probes/prefusion_node_sentinel_downstream_watch/verify_state_22ae60_copy_surfaces.py
static: OK captures=8
28mm: OK callers=0x20adf6:6,0x20bffa:6,0x20caca:6,0x20d309:31,0x239c34:6,0x239fd9:6
35mm: OK callers=0x20adf6:6,0x20bffa:6,0x20caca:7,0x20d309:30,0x239c34:6,0x239fd9:6
70mm: OK callers=0x20adf6:6,0x20bffa:6,0x20caca:6,0x20d309:0,0x239c34:6,0x239fd9:6
150mm: OK callers=0x20adf6:4,0x20bffa:4,0x20caca:5,0x20d309:18,0x239c34:5,0x239fd9:4
```

Sampled `0xe0ae0` caller counts from the four admitted JSONs:

| Zoom | `0x20adf6` | `0x20bffa` | `0x20caca` | `0x20d309` | `0x239c34` | `0x239fd9` |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `6` | `6` | `6` | `31` | `6` | `6` |
| `35mm` | `6` | `6` | `7` | `30` | `6` | `6` |
| `70mm` | `6` | `6` | `6` | `0` | `6` | `6` |
| `150mm` | `4` | `4` | `5` | `18` | `5` | `4` |

These are sampled watchpoint counts, not algorithm constants.

Every sampled packet in these caller buckets still read the watched pair as
`(-1.0, -1.0)`.

## Static Classification

### `0x22ae60`

Installed-bundle disassembly proves `0x22ae60` is a compact State body:

- `0x22ae6e` calls `0x20ada0` with `*(rbx+0x10)`.
- `0x22ae7e` calls `0x239ac0` with `*(rbx+0x28)`.
- `0x22ae87` calls `0x20bd60` with `*(rbx+0x10)`.
- `0x22ae97` calls `0x239ac0` again with `*(rbx+0x28)`.
- `0x22ae9c` returns State value `8`.

The already-admitted State-operator runtime census proves `0x22ae60` is live
once per canonical bridge HDR render at `28mm`, `35mm`, `70mm`, and `150mm`.

### `0x20bd60`

Installed-bundle disassembly labels this body's timer string as `"point BA"`.

Inside the main keyed-record loop:

- `0x20bff5 -> 0xe0ae0` copies the current record's pair vector.
- `0x20bffa` is the post-copy site sampled in all four admitted downstream-watch runs.
- `0x20c00d -> 0xe6ba0` resolves the keyed object.
- `0x20c020` reads `object+0x30`; `0x20c02d..0x20c02f` skips inactive objects.
- Active objects reach `0x264440`, `0x23faf0`, `0x20dca0`, and `0x25e4b0`.
- `0x20c154..0x20c17e` writes the `0x25e4b0` output fields into the keyed record returned by `0x20dca0`.
- `0x20c2f6 -> 0x5670` dispatches a stack callback object.
- `0x20c3e0..0x20c4b4` computes min/max over positive scalar fields and stores them at `state+0x78` and `state+0x7c`.

This bounds `0x20bd60` as keyed record/materialization and summary work. It does
not expose a final image reducer or final contributor acceptance policy.

### `0x25e4b0`

Installed-bundle disassembly proves `0x25e4b0` initializes a `0x50` record and
tail-calls the already-bounded `0x25e0c0` row producer:

- row diagonal/default fields at `+0x00`, `+0x14`, `+0x28`, and `+0x3c` are initialized to binary32 `1.0`
- intervening row fields are zeroed
- `record+0x40` is set to `0`
- `record+0x48/+0x4c` are set to `(1.0, 1.0)`
- `0x25e4f5` tail-jumps to `0x25e0c0`

The adjacent `0x25e500` body performs the same initialization and `0x25e0c0`
call, but additionally stores its fourth argument into `record+0x40` at
`0x25e552`. That difference matches the already-admitted pair-grid producer
evidence: `0x25e500` is the map-pointer writing composer; `0x25e4b0` is the
no-map variant.

### `0x20dca0`

Installed-bundle disassembly proves `0x20dca0` is a keyed tree find/insert helper:

- it searches by the integer key at `*rsi`
- if needed, it allocates a `0x80` node
- it initializes the node's record area at `node+0x30` through `0x25e070`
- it returns `node+0x30`

This classifies the `0x20bd60 -> 0x20dca0` edge as record storage / lookup, not
image accumulation by itself.

### `0x20ca00`

The sampled `0x20caca` and `0x20d309` copy callers are inside callback body
`0x20ca00`. Later typeinfo/vtable proof identifies it exactly as the
substantive `+0x30` callback of a `void(int,int,int)` lambda inside
`lt::Triangulator::refine3dPoints()`, not the method entry.

Static disassembly proves this body:

- copies keyed pair vectors through `0xe0ae0`
- resolves keyed objects through `0xe6ba0`
- reads and gates on `object+0x30`
- creates / updates keyed records through `0x20dca0`
- expands matrix/record fields into double-precision local storage
- sets up a `ceres::Problem`
- contains positive-coordinate gates before Ceres parameter/residual work, including `0x20d35e -> 0x20d363`

The existing runtime watchpoint packets prove still-sentinel `(-1.0, -1.0)`
pairs are copied inside this body. They do not prove that the watched copied
element is the exact later element selected by the Ceres loop. Therefore the
safe conclusion is classification of a sampled Ceres-setup surface, not sampled
sentinel terminality.

### `0x239ac0` / `0x239e00`

The sampled `0x239c34` and `0x239fd9` copy callers are inside the `0x239ac0`
family called before and after `0x20bd60` from `0x22ae60`.

Static disassembly proves:

- `0x239ac0` calls `0x239e00`, then iterates keyed records from `this+0x10`.
- `0x239c2f -> 0xe0ae0` copies each record's pair vector.
- `0x239c34` calls `0x239e00` for the copied record key.
- `0x239c4b..0x239d25` finds or creates a `0x40` keyed node and updates its payload through `0x23a5d0`.
- `0x239e00` either copies the current `0x14`-stride record vector into a local 8-byte pair vector or finds/creates a keyed `0x40` node.
- `0x239fd4 -> 0xe0ae0` copies a keyed node's pair vector into that local vector.

This classifies the sampled `0x239ac0` family as keyed record / pair-vector
propagation. It does not prove image contribution, reducer closure, or final
acceptance / rejection behavior.

## Proven Facts

1. The corrected State body `0x22ae60` is the static caller of `0x20ada0`, two
   `0x239ac0` calls, and `0x20bd60`, and returns State value `8`.
2. Existing four-zoom runtime proof already admits `0x22ae60` as live once per
   canonical bridge HDR render.
3. Existing four-zoom downstream-watch packets sample `0xe0ae0` copy callers
   `0x20adf6`, `0x20bffa`, `0x20caca`, `0x20d309`, `0x239c34`, and `0x239fd9`
   while the watched pair remains `(-1.0, -1.0)`.
4. Static disassembly classifies `0x20bd60` / `"point BA"` as keyed record
   materialization, `0x25e4b0` as the no-map `0x25e0c0` row-producer variant,
   `0x20dca0` as keyed record storage, `0x20ca00` as the named Triangulator
   lambda callback with Ceres setup and positive-coordinate gates, and
   `0x239ac0` / `0x239e00` as keyed pair-vector propagation.

## Safe Conclusion

The sampled State-family downstream copy stops are now bounded to record /
pair-vector propagation, no-map matrix-record composition, selected Ceres setup,
and keyed record update surfaces. None of these sampled static windows is proven
to be the missing `src1` / `src2` merge/reduction mechanism.

## Consequence For Blocker Work

Lane A should not treat `0x20bd60`, `0x25e4b0`, `0x20dca0`, `0x20ca00`, or
`0x239ac0` / `0x239e00` as opaque possible reducers without new evidence. The
remaining blocker is still downstream image/source-contribution consequence,
semantic `src1` / `src2` contents, and final acceptance / rejection behavior.
