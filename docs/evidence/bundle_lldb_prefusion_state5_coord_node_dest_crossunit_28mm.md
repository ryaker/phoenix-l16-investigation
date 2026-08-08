# Bundle + LLDB Proof: Prefusion State-5 Coordinate Node-Destination Consumer, Unit-2 Exact 28mm

## Scope

This note adds a second-body discriminator for the already-admitted four-zoom
Unit-1 node-destination non-copy consumer proof.

It proves only that, under one clean complete exact-`28mm` Unit-2 bridge HDR
render:

- the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector copy site is live;
- representative finite non-sentinel coordinate pairs are copied into the
  node-vector destination;
- one watched copied pair reaches the same non-copy `0x21b2e0` /
  `0x21c4f0` candidate/index/scoring-selection consumer VAs already observed
  in the Unit-1 four-focal proof.

It does not prove all bodies, all focal tiers, all copied pairs, image effect,
source contribution, reducer closure, or final acceptance/rejection.

The Unit-2 LRI used here is the exact-`28mm` representative identified by the
tracked two-unit corpus/crossunit LRI carrier evidence:

`/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri`

## Repo-Local Artifacts

- Shared configurable probe harness:
  `tools/lldb_probes/prefusion_state5_coord_copy_dest_watch/prefusion_state5_coord_copy_dest_watch_probe.py`
- Unit-2 LLDB script:
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.lldb`
- Unit-2 runner:
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/run_unit2_28.sh`
- Unit-2 verifier:
  `tools/lldb_probes/prefusion_state5_coord_node_dest_watch/verify_node_dest_crossunit.py`
- Raw output directory:
  `runs/prefusion_state5_coord_node_dest_watch/`

The admitted runtime artifacts are:

- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.json`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.hdr`
- `runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.log`

## Runtime Scope

The LLDB script launches:

`/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri" runs/prefusion_state5_coord_node_dest_watch/node_dest_watch_unit2_28mm.hdr --profile 3 --export-fmt 3 --no-auto-lris`

The script uses the installed Lumen framework path:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`

The probe reuses the exact node-vector copy-site configuration from the Unit-1
proof:

| VA | Role |
|---:|---|
| `0x22a61a` | `0x22a0e0` node-vector copy call into `0xe8e70` |
| `0x22a61f` | return site after that copy |
| `0x22c93a` | sibling `0x22c350` node-vector copy call into `0xe8e70` |
| `0x22c93f` | return site after that sibling copy |

As in the Unit-1 proof, the admitted Unit-2 run observed the `0x22a61a`
site before the watch limit; the sibling `0x22c93a` site had zero observed
call/return hits in this proof.

## Runtime Results

| Body | Zoom | LRI | Exit | Step cap | JSON errors | Copy calls / returns at `0x22a61a` / `0x22a61f` | Destination pairs admitted | Watchpoints armed | Watchpoint hits |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| Unit-2 | exact `28mm` | `L16_02130` | `0` | `false` | `0` | `3 / 3` | `3` | `3` | `64` |

The HDR output is a complete `10432x7824` Radiance HDR image.

The first admitted watched pair was copied to pair index `79` and armed as
finite non-sentinel `(1016.0, 36.0)`.

The capped watchpoint window hit the same consumer VA set as the Unit-1
four-focal proof:

| VA | Bounded local role |
|---:|---|
| `0x21b444` | first lane positive test in `0x21b2e0` node-vector scan |
| `0x21b44c` | second lane positive test in `0x21b2e0` node-vector scan |
| `0x21c2b0` | pair-lane arithmetic inside callback path reached from `0x21c4f0` |
| `0x21c2b6` | pair-lane arithmetic continuation inside callback path reached from `0x21c4f0` |

Every admitted watchpoint sample preserved a finite non-sentinel pair at the
watched address. The frame-1 stack set was `{0x22a9e7, 0x21c59c}`, matching
the already-bounded State-family / `0x21c4f0` callback consumer route.

Verifier output:

```text
$ python3 tools/lldb_probes/prefusion_state5_coord_node_dest_watch/verify_node_dest_crossunit.py
Unit-2 exact 28mm: OK admitted=3 watchpoints=3 hits=64 first_pair_index=79 consumer_vas=0x21b444,0x21b44c,0x21c2b0,0x21c2b6
scope=second-body discriminator for state-5 node-destination non-copy candidate/index/scoring consumer; image effect, reducer closure, and final acceptance remain open
```

## Proven Facts

1. The Unit-2 exact-`28mm` run completed with exit status `0`, no probe errors,
   no step cap, and a Radiance HDR output.
2. The run observed three same-thread `0x22a61a -> 0xe8e70 -> 0x22a61f`
   node-vector copy call/return pairs before the watch limit.
3. The run armed three watchpoints on finite non-sentinel copied destination
   pairs.
4. The run observed 64 capped watchpoint hits on the first watched pair.
5. The Unit-2 watchpoint stops hit the same four non-copy consumer VAs admitted
   for the Unit-1 four-focal proof: `0x21b444`, `0x21b44c`, `0x21c2b0`,
   and `0x21c2b6`.

## Safe Conclusion

The state-5 node-destination non-copy candidate/index/scoring-selection consumer
is not Unit-1-only under the tested conditions. The same downstream consumer
shape is observed on the exact-`28mm` Unit-2 representative.

This is a risk-reducing cross-body discriminator only. Unit-1 remains the
four-focal coverage set, and this proof does not claim all-body/all-focal
universality, image effect, reducer closure, or final acceptance/rejection.
