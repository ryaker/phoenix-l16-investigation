# Bundle LLDB: Prefusion Block-Geometry Effect, Four Zoom

## Scope

This bundle adds runtime effect proof for the already statically bounded
`0x25d090` candidate block-geometry / active-block helper.

It proves, under the canonical no-auto-LRIS bridge HDR quartet, that
`0x25d090` mutates block-owned pair-vector families, calls the descriptor
builder and geometry predicate, and gates the block-active byte. It does not
prove public state names, image contribution, final acceptance/rejection, or
`src1` / `src2` reducer closure.

The static interpretation of the helper family is inherited from
[bundle_proof_prefusion_block_geometry_helpers.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_prefusion_block_geometry_helpers.md).

## Artifacts

- Harness:
  `tools/lldb_probes/prefusion_block_geometry_effect/block_geometry_effect_probe.py`
- Per-zoom LLDB scripts:
  `tools/lldb_probes/prefusion_block_geometry_effect/block_geometry_effect_28mm.lldb`,
  `block_geometry_effect_35mm.lldb`,
  `block_geometry_effect_70mm.lldb`,
  `block_geometry_effect_150mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_block_geometry_effect/run_four_zoom.sh`
- Verifier:
  `tools/lldb_probes/prefusion_block_geometry_effect/verify_block_geometry_effect.py`
- Raw outputs:
  `runs/prefusion_block_geometry_effect/block_geometry_effect_28mm.json`,
  `block_geometry_effect_35mm.json`,
  `block_geometry_effect_70mm.json`,
  `block_geometry_effect_150mm.json`
- Render outputs:
  `runs/prefusion_block_geometry_effect/block_geometry_effect_28mm.hdr`,
  `block_geometry_effect_35mm.hdr`,
  `block_geometry_effect_70mm.hdr`,
  `block_geometry_effect_150mm.hdr`

## Commands

```bash
bash tools/lldb_probes/prefusion_block_geometry_effect/run_four_zoom.sh
python3 tools/lldb_probes/prefusion_block_geometry_effect/verify_block_geometry_effect.py
python3 -m py_compile \
  tools/lldb_probes/prefusion_block_geometry_effect/block_geometry_effect_probe.py \
  tools/lldb_probes/prefusion_block_geometry_effect/verify_block_geometry_effect.py
```

Each LLDB script launches `tools/lri_process` with `--profile 3`,
`--export-fmt 3`, and `--no-auto-lris`.

## Runtime Anchors

The harness records five points inside the helper:

- `0x25d090`: entry
- `0x25d243`: after the `0x25d2a0` descriptor-builder call
- `0x25d251`: after the `0x25ca70` geometry-predicate call
- `0x25d25f`: after the active-byte clear store at `block+0x04`
- `0x25d278`: return site

Each sample captures the block target at `block+0x00`, the active byte at
`block+0x04`, the descriptor payload at `block+0x08`, and both block-owned
pair-vector families rooted at `block+0x30` and `block+0x48`.

## Verifier Output

The repo-local verifier rechecks clean completion, exact helper counts, active
block effects, pair-vector growth invariants, and Radiance HDR output custody:

```text
28mm: OK entry=44 active=22 true=22 false=22 geom=22/0 clears=0 max_growth=334
35mm: OK entry=44 active=22 true=22 false=22 geom=22/0 clears=0 max_growth=781
70mm: OK entry=44 active=27 true=25 false=19 geom=25/2 clears=2 max_growth=1285
150mm: OK entry=44 active=22 true=22 false=22 geom=22/0 clears=0 max_growth=165
```

The `max_growth` values are observed vector-growth maxima in these runs, not
algorithm constants.

## Result Table

| Zoom | Entry hits | Active / inactive entries | `0x25d2a0` success / fail | `0x25ca70` accept / reject | Active clears | Return true / false |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | 44 | 22 / 22 | 22 / 0 | 22 / 0 | 0 | 22 / 22 |
| `35mm` | 44 | 22 / 22 | 22 / 0 | 22 / 0 | 0 | 22 / 22 |
| `70mm` | 44 | 27 / 17 | 27 / 0 | 25 / 2 | 2 | 25 / 19 |
| `150mm` | 44 | 22 / 22 | 22 / 0 | 22 / 0 | 0 | 22 / 22 |

All four runs exited with status `0`, hit no probe step cap, recorded no probe
errors, and wrote `10432 x 7824` HDR outputs.

## Proven Facts

1. In the admitted four-zoom runs, `0x25d090` is reached `44` times per render
   and sees block targets `{1, 2}` and levels `{1, 2, 3}`.
2. Inactive entries return false without reaching the `0x25d2a0` descriptor
   builder, and the block-active byte remains `0`.
3. Active entries reach `0x25d2a0`; every admitted `0x25d2a0` return is success.
4. True-return entries have `0x25ca70` geometry accept, preserve block-active
   byte `1`, and grow both same-level block pair-vector families rooted at
   `block+0x30` and `block+0x48` by the same positive count.
5. The only active false returns in these runs are the two `70mm` geometry
   rejects. Both already have `0x25d2a0` success, then `0x25ca70` reject, then
   the `0x25d259` active-byte clear; both return false with block-active byte
   still `0`.
6. No active-byte clears were observed in the admitted `28mm`, `35mm`, or
   `150mm` runs.

## Safe Conclusion

`0x25d090` is now runtime-bounded for the canonical quartet as block-owned
pair-vector growth plus descriptor-build / geometry-predicate / active-byte
gating. The helper is not the missing reducer by itself.

The remaining blocker is downstream of this bounded effect: image/source
contribution after the block-state decision, public meaning of state/target
fields, final acceptance/rejection, and the larger `src1` / `src2` merge or
reduction mechanism.

## Non-Admissions

- This does not prove state `5` public semantics.
- This does not prove final image contribution or non-contribution.
- This does not prove final acceptance/rejection logic.
- This does not prove full `src1` / `src2` reducer closure.
- The hit counts and vector-growth magnitudes are evidence-run observations,
  not universal constants.
- The canonical four-zoom quartet remains one body across four focal tiers; it
  is not a cross-unit universality proof.
