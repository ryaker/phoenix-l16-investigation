# Evidence: Wide Minimum Selector and CalibStage Transfer

## Scope

This bundle corrects and extends the wide branch interpretation in
`bundle_static_runtime_prefusion_composer_transform_materialization_four_zoom.md`.
It follows the mean reprojection-residual scalar after State `0x22d250`
compares it with the existing keyed scalar at node `+0x28`.

The prior labels `keep-existing` for `score <= existing` and `update` for
`score > existing` were reversed. The installed code and fresh completed
runtime packets prove:

- `score <= existing` enters `0x22d9a0`, materializes the candidate record,
  and stores the candidate score at keyed node `+0x28`;
- `score > existing` enters `0x22d901`, finds the existing keyed
  `state+0x448` node, and copies three slices from that node into selector-1
  CalibStage storage in the per-camera `state+0xe0` object;
- the comparison is therefore a local minimum selector for the bounded keyed
  record, not a max-like comparison;
- this is an internal calibration-record selection boundary, not final image
  or merge acceptance.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_264270_output_watch_probe.py`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py`
- Outcome-targeted probe and verifier:
  `tools/lldb_probes/prefusion_wide_minimum_selector/wide_minimum_selector_probe.py`
  and `verify_wide_minimum_selector.py`
- LLDB command files:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/output_watch_28mm.lldb`
  and `output_watch_35mm.lldb`
- Completed runtime reports:
  `runs/prefusion_264270_output_watch/output_watch_28mm.json` and
  `output_watch_35mm.json`
- Outcome-targeted report:
  `runs/prefusion_wide_minimum_selector/wide_minimum_selector_28mm.json`
- Completed HDR outputs:
  `runs/prefusion_264270_output_watch/output_watch_28mm.hdr` and
  `output_watch_35mm.hdr`

All admitted renders exit `0`, report no probe errors, and write
`10432 x 7824` Radiance HDR output.

## Static Proof

The verifier pins the installed `libcp.dylib` and these relevant windows:

```text
0x22d8ed..0x22d907 comparison:
f0cce948c7dad3ae0ac8b30306fe98c104134854ffd632153ee19d5794b9f027

0x22d9a0..0x22dcaa candidate materialization:
e44ff56e342b10fd7788ec9507df8ae42a197258960c2d88c1df27313619cfa5

0x22dcc3..0x22dce5 existing-entry selection:
ca5a6e8c78767badfc4840e21404f5539f1898747d7311ee4acfd269a169e8f8

0x22df1f..0x22df49 CalibStage transfer call:
b783fb62719b519efc618e2d34fe520b57458eb5381b066bb7ef8317dc3d1cf8

0x0f33d0..0x0f349c selector copy:
ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8

0x22e20e..0x22e248 terminal first helper call:
1178507220f11f9bdfbcea5b663abec0ce5077a1681e2fb79745644b4c99aba7

0x264440..0x26444e selector-1 wrapper:
1659eacdd472b9ce2c4bbb38d5bcd3090012898f8a7f5b288847bb5e6b6f43a5

0x23cb9c..0x23cbc0 terminal helper record chain:
b0d7bc07d6abe62c70c2004b51faaddd5d46fa62003bead9e100759db72980b3

0x23ce20..0x23ce67 terminal keyed-node materialization:
bb6caf4daeda93105f4c596a09930e4c54f40f248566e4f2fdd028b540db1cf1

0x23d128..0x23d15c terminal tree-copy and transform calls:
7698830b20a521539025b4964d0ce26bd57211827299c41101e45c51fb467f0b

0x1fe8a0..0x1fe96e keyed-tree copy:
cade479bc0117877cddf8371090f2fc4b0c319b9e393ea181204e1fcfe4be4a4

0x2008d0..0x2009d2 keyed-node copy:
6dce5ffe6d6928cdd5b4d6aeb2876f5ab79949cb446c4841a4ac3335fe0f14f5

0x1ff60c..0x1ff618 transform field call:
725d89e5afce1086b3d6ba7c6552b00e2793f27ee3f116e2c1a341e984ebe996

0x200fb0..0x200ff9 field conversion:
d6dc2e2521985f8c8dedc66f0329052891fc018dfbfbdf79473b0c57768323bf

0x1fe965..0x1fea1f BA minimum-camera check:
2970e368b95710fcfc997af014b78a6f34d7511e49b84fb4ad09a04c12c205a3

0x1ff460..0x20021f camera-map normalization:
2447eb1998a2fbef33466cc53897dddbec3cae9f9c01347936a91a27c3ae5497

0x200690..0x20084f camera-map summary/transform:
36359b851faf751649382d584c74bc1f744b66f38d0cc0cc0280a31bdc45e5ed

0x23d26a..0x23d392 terminal normalized write-back chain:
363af6d8950101f08da861c438b9a8ef08f1c5ff0653584b61fb1687def19681

0x23c0f0..0x23c5ac normalized record conversion:
81fc95be366dbe405fecfdb5d0dbc94d88bceb87940c240a7a9d6c3f3f79b248

0x2406a0..0x2406ff normalized composition prefix:
e7b2892511455950aebed9a967db0149ed19a21aa388f586312ddf1c19256d66
```

At `0x22d8f5`, State compares:

```text
candidate mean reprojection residual in xmm0
existing keyed residual at node+0x28
```

The `jbe 0x22d9a0` side reconstructs the candidate record. It calls
`0xe6ba0` and `0x264440`, then writes the exact candidate score at
`0x22db76 -> node+0x28` and record fields from node `+0x30` through at least
`+0xd0`.

The fallthrough side resolves the same key in the `state+0x448` tree. At the
admitted existing-entry site `0x22dcc3`, it saves the found node in
`rbp-0x2c0` and bypasses allocation. At `0x22df1f..0x22df45`, it calls
`0xf33d0` with:

```text
rdi = per-camera state+0xe0 object returned by 0xe6ba0
rsi = selected state+0x448 node + 0x30
rdx = selected state+0x448 node + 0x60
rcx = selected state+0x448 node + 0x54
r8d = 1
```

The pinned selector-1 body copies those slices exactly:

```text
node+0x30..+0x53 -> object+0x12c..+0x14f
node+0x60..+0x83 -> object+0x150..+0x173
node+0x54..+0x5f -> object+0x174..+0x17f
```

`0xf34e0(object, 1)` returns `object+0x12c`, so the destination is the live
selector-1 CalibStage bank already bounded elsewhere.

## Runtime Proof

First-hit branch identity varies with runtime scheduling, so the reusable
outcome-targeted harness records compare-to-effect transactions until both
outcomes complete, then disables its breakpoints. One complete Unit-1 `28mm`
render captures:

| Key | Candidate | Existing | Proven effect |
|---|---:|---:|---|
| `B2` (`6`) | `2.0703072547912598` | `2.0703072547912598` | equal candidate materialized |
| `B4` (`8`) | `3.5307581424713135` | `3.5307581424713135` | equal candidate materialized |
| `B5` (`9`) | `5.800161361694336` | `7.397486209869385` | strict lower candidate materialized |
| `B1` (`5`) | `5.103415012359619` | `4.865466117858887` | higher candidate rejected; existing record transferred |

For every materialization event, the verifier requires the runtime `jbe`
flags, `candidate <= existing`, compared-node/destination-node pointer
identity, and exact candidate-score bits at node `+0x28`.

For the existing-record transfer, the verifier requires:

- the compared node pointer and `rbp-0x2c0` selected node to be identical;
- source addresses to equal that node plus `0x30`, `0x60`, and `0x54`;
- selector `r8d` to equal `1`;
- the complete post-call `object+0x12c..+0x17f` bank to equal the exact
  concatenation of the three source slices;
- the bank to differ from its pre-call bytes.

For both route effects, the keyed node ID exactly equals the per-camera
object's `+0x60` ID, already proven to align with public `CameraModule.id`.
An independent completed `35mm` first-hit packet also proves the
existing-record transfer and supplies the checked public-byte negative result.
Keys and numeric scores are runtime observations, not constants.

Verifier output:

```text
wide_minimum_selector=OK materialize=5.80016136<=7.39748621 retain=5.10341501>4.86546612
```

## Terminal Consumer Custody

The independent completed `35mm` transfer packet arms an 8-byte hardware
watch only after the selected existing record has been copied into the live
selector-1 bank. Its first later touch:

- reads the exact unchanged bank prefix at instruction `0x264299`, reported by
  LLDB at next PC `0x26429c`;
- has `r15` equal to the exact per-camera object updated by the minimum
  selector;
- has stack ancestry
  `0x264270 <- 0x23c5f0@0x23cbab <- 0x22e1d0@0x22e249
  <- dispatcher@0x22f3ff`.

The pinned parent code proves `0x22e244` is the first of terminal State
`0x22e1d0`'s two `0x23c5f0` calls. Inside that helper, `0x23cba6` calls
wrapper `0x264440`, which sets selector `1` and tail-jumps to `0x264270`.
The latter copies the selector-1 bank into its destination record.

A route-gated breakpoint at `0x23cbbc` then proves the exact `0x264270`
destination pointer is passed as `rdx`, the right record to `0x23faf0`.
The verifier reconstructs `0x264270`'s field ordering from the selected bank
and requires the captured right-record bytes through `+0x53` to match exactly.

The `0x23faf0` destination changes across the call and remains stable to
`0x23ce5e`. There, the same local key is materialized at node `+0x20`, and
the destination's first eight float32 fields convert exactly to the eight
float64 node fields at `+0x28..+0x67`.

An outcome-gated hardware watch then proves the first later touch of
`node+0x28` is the unchanged read at instruction `0x20090b`, reported at next
PC `0x20090f`, under:

```text
0x2008d0 <- 0x1fe8a0@0x1fe8ff <- 0x23c5f0@0x23d151
         <- terminal 0x22e1d0@0x22e249
```

Static and runtime identity agree that `0x1fe8a0` traverses the keyed tree and
`0x2008d0` allocates a `0xa8` node, copying the selected source node payload
from `+0x20..+0xa3`. At return `0x2009c3`, the captured new node's complete
`0x84`-byte payload is byte-identical to the selected source node.

The copied-node watch next proves its first later touch is the unchanged read
at instruction `0x200fb4`, reported at `0x200fb7`, with `rsi` equal to copied
node `+0x28` under:

```text
0x200fb0 <- 0x1ff460@0x1ff618 <- 0x23c5f0@0x23d15d
         <- terminal 0x22e1d0@0x22e249
```

The pinned helper preserves the first input double and derives its second
output double by dividing input `+0x20` by that first value before copying
additional fields. This closes selected-record custody through terminal
composition, keyed-node materialization, exact tree copy, and entry into the
immediate terminal record-field transform. It does not prove that transform
changes an image, contributes a source, closes the distributed reducer, or
determines final acceptance.

## BA Camera-Map Write-Back

Installed strings and their SHA-pinned xrefs provide an internal semantic
boundary for this transform:

```text
0x1fe97f -> "Very few cameras for BA reconstruction."
0x200816 -> "Empty camera map."
```

The first xref lies in the keyed-tree copy/constructor immediately before
`0x1ff460`; the second lies in `0x200690`, called by `0x1ff460` while
transforming the camera map. This admits the surface as internal BA
camera-map normalization, not a public API or protobuf name.

The completed `35mm` outcome-gated packet proves:

- `0x1ff460` changes the copied keyed node but leaves the selected source node
  byte-identical;
- the first later read of an actually changed copied-node qword is instruction
  `0x23d2aa`, reported at `0x23d2ae`, with `rax` equal to the exact copied
  node;
- the `0x7c` bytes passed at `0x23d2ee -> 0x23c0f0` exactly equal copied-node
  `+0x28..+0xa3`;
- `0x23c0f0` returns its changed `0xa4` float-record destination, which is
  passed byte-identically as the right operand to
  `0x23d34d -> 0x2406a0`;
- `0x2406a0` returns its changed destination, whose slices
  `+0x00..+0x23`, `+0x30..+0x53`, and `+0x24..+0x2f` become the exact three
  selector-1 `0xf33d0` sources at `0x23d38d`;
- `f33d0` copies those sources exactly into object
  `+0x12c..+0x17f`, changing the destination bank;
- selected-node key, copied-node key, outer-loop local key, and destination
  object `+0x60` all equal `5`, whose public carrier is
  `CameraModule.id`.

This is a same-public-camera-key BA calibration-record normalization and
CalibStage write-back loop. The loop is concrete calibration-state work, not
evidence of a direct image reducer, source-image contribution, or final
acceptance.

## Public-Origin Boundary

This closes a concrete relationship between the two previously bounded State
surfaces:

```text
selected keyed state+0x448 calibration record
  <-> selector-1 CalibStage bank in same-key per-camera state+0xe0 object
```

Earlier evidence gives public calibration ancestry for portions of the
`state+0x448` record at construction time:

- public anchor
  `FactoryModuleCalibration.geometry.per_focus_calibration[2].extrinsics.canonical`
  rotation and translation;
- derived box/scale fields whose inputs come from public
  `geometry.distortion.polynomial` and
  `CameraModule.sensor_data_surface.size`.

The three transferred `35mm` slices do not exactly match any complete
fixed32 sequence in the checked public calibration payloads and do not exactly
match the compact public K, rotation, or translation components. The selected
record is therefore admitted as a derived internal calibration record with
publicly anchored inputs, not as a direct protobuf-field byte copy at this
later transfer.

## Admission

This correction and terminal-consumer extension are admitted for `CLM-PREFUSION-001` and
`CLM-PREFUSION-002`. It changes the interpretation of an already-admitted
branch and adds exact `state+0x448 -> state+0xe0 -> terminal 0x23c5f0 /
0x264270 -> 0x23faf0 -> keyed node -> copied tree -> BA camera-map
normalization -> same-key selector-1 CalibStage write-back` selected-record
custody. Claim status remains `PARTIAL`.

It does not name the complete selected record, prove every key or body takes
both outcomes, name the `0x1ff460` transform in public terms, establish
source-image contribution, close the distributed reducer, or prove final
merge acceptance/rejection.
