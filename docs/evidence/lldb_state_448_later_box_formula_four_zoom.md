# LLDB Evidence: `state+0x448` Later Box/Scale Formula, Four Zoom

## Scope

This note closes the immediate runtime formula for the later
`state+0x448` payload fields `+0x30..+0x3c` in the first visible
`0x3f2c40` constructor branch.

It builds on:

- [bundle_proof_iramp_state_448_later_payload_writes.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_later_payload_writes.md)
- [lldb_state_448_payload_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_payload_public_origin_four_zoom.md)
- [lldb_index5_depth_public_meaning_gap_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md)

It proves:

- `payload+0x30/+0x34` is a uniform float32 scale pair;
- `payload+0x38/+0x3c` is a float32 box-origin pair;
- both pairs are produced by the installed `0x260e40` formula from the
  `0x145980` box and the `object+0x114/+0x118` size pair;
- the formula outputs are copied byte-exactly into the found `state+0x448`
  payload for the same key.

It does not prove a public protobuf/LRI field name for the `0x145980` box
producer, nor a semantic public name for the box or scale fields.

## Artifacts

- Runtime probe:
  [box_formula_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/box_formula_probe.py)
- Verifier:
  [verify_box_formula.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/verify_box_formula.py)
- LLDB scripts:
  [box_formula_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/box_formula_28mm.lldb),
  [box_formula_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/box_formula_35mm.lldb),
  [box_formula_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/box_formula_70mm.lldb),
  [box_formula_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/box_formula_150mm.lldb)
- Runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/run_four_zoom.sh)
- Raw rerunnable outputs:
  `runs/state_448_later_box_formula/`

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`.

## Static Formula Boundary

At the callsite:

```text
0x3f3503  object -> 0xf3350
0x3f350b  add 0x8, so rsi = object+0x114
0x3f3514  rdi = rbp-0x520      ; 0x145980 box
0x3f351e  rcx = rbp-0x5d8      ; origin output
0x3f3525  r8  = rbp-0x5d0      ; scale output
0x3f352c  call 0x260e40
0x3f3599  0x2415d0(payload, rbp-0x5d0) -> payload+0x30/+0x34
0x3f35f5  0x2415f0(payload, rbp-0x5d8) -> payload+0x38/+0x3c
```

The installed `0x260e40` body implements:

```text
box = [x0, y0, x1, y1]        ; int32 from rdi
size = [width, height]        ; int32 from rsi = object+0x114

origin_out = [float32(x0), float32(y0)]
scale_x = float32(width) / float32(x1 - x0)
scale_y = float32(height) / float32(y1 - y0)

if edx != 0:
  scale_out = [max(scale_x, scale_y), max(scale_x, scale_y)]
else:
  scale_out = [scale_x, scale_y]
```

In the tested constructor path, `edx = 1`.

## Runtime Results

The verifier requires, for each key:

- complete process exit with status `0`;
- no probe errors or step cap;
- Radiance HDR output;
- one event at each of the five watched sites;
- identical `0x145980` post-box and `0x260e40` pre/post box values;
- pre-call `size_i32_wh == [4160, 3120]`;
- `object+0x114/+0x118 == [4160, 3120]`;
- `object+0x124/+0x128 == [1.0, 1.0]`;
- `edx == 1` at `0x260e40`;
- raw float32 origin/scale words exactly match the formula;
- raw formula output words exactly match the later `0x2415d0` and `0x2415f0`
  payload-copy source words.

Verifier output:

```text
28mm: OK keys=0,1,2,3,4; 0:box=[17, 13, 4141, 3106]:origin=17,13:scale=1.008729339; 1:box=[17, 13, 4141, 3106]:origin=17,13:scale=1.008729339; 2:box=[17, 13, 4140, 3105]:origin=17,13:scale=1.009055614; 3:box=[18, 14, 4140, 3105]:origin=18,14:scale=1.009382129; 4:box=[19, 15, 4138, 3104]:origin=19,15:scale=1.010035634
35mm: OK keys=0,1,2,3,4; 0:box=[17, 13, 4141, 3106]:origin=17,13:scale=1.008729339; 1:box=[17, 13, 4141, 3106]:origin=17,13:scale=1.008729339; 2:box=[17, 13, 4140, 3105]:origin=17,13:scale=1.009055614; 3:box=[18, 14, 4140, 3105]:origin=18,14:scale=1.009382129; 4:box=[19, 15, 4138, 3104]:origin=19,15:scale=1.010035634
70mm: OK keys=5,6,7,8,9; 5:box=[4, 3, 4155, 3116]:origin=4,3:scale=1.002248645; 6:box=[2, 2, 4156, 3116]:origin=2,2:scale=1.001926780; 7:box=[3, 2, 4156, 3116]:origin=3,2:scale=1.001926780; 8:box=[3, 2, 4156, 3116]:origin=3,2:scale=1.001926780; 9:box=[3, 2, 4155, 3115]:origin=3,2:scale=1.002248645
150mm: OK keys=5,6,7,8,9; 5:box=[4, 3, 4155, 3116]:origin=4,3:scale=1.002248645; 6:box=[2, 2, 4156, 3116]:origin=2,2:scale=1.001926780; 7:box=[3, 2, 4156, 3116]:origin=3,2:scale=1.001926780; 8:box=[3, 2, 4156, 3116]:origin=3,2:scale=1.001926780; 9:box=[3, 2, 4155, 3115]:origin=3,2:scale=1.002248645
```

## Proven Field Meaning

For this later direct-write slice:

```text
state+0x448 payload +0x30/+0x34
  <- rbp-0x5d0
  <- 0x260e40 uniform scale output
  <- max(4160 / (box.x1 - box.x0), 3120 / (box.y1 - box.y0))
     with float32 arithmetic

state+0x448 payload +0x38/+0x3c
  <- rbp-0x5d8
  <- 0x260e40 origin output
  <- [float32(box.x0), float32(box.y0)]

box
  <- rbp-0x520 after 0x145980(object)

size
  <- object+0x114/+0x118
  == [4160, 3120] in all admitted samples
```

The existing public-meaning audit already bounds the same object family enough
to say `object+0x10c` carries a `4160 x 3120` shape and `1.0 / 1.0` scale in
these runs. This proof connects that object shape to the later
`state+0x448` scale computation. Companion static-origin proof in
[lldb_state_448_box_producer_static_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_box_producer_static_origin_four_zoom.md)
then names the size pair as the LRI-stored full sensor ROI and bounds the
`0x145980` box as a computed distortion/undistortion envelope. It still does
not assign a public protobuf field number or semantic public name to that box.

## Safe Conclusion

- Proven:
  later `state+0x448` payload fields `+0x30..+0x3c` are not opaque bytes in the
  tested first visible constructor branch. They are formula outputs from an
  object-derived box and the `4160 x 3120` object size pair.
- Proven:
  wide tiers write keys `0..4` with the same box/scale values across `28mm`
  and `35mm`; tele tiers write keys `5..9` with the same box/scale values
  across `70mm` and `150mm`.
- Proven:
  the exact formula output words are copied into the keyed `state+0x448`
  payload by `0x2415d0` and `0x2415f0`.
- Still unproven:
  public semantic names or protobuf field numbers for the owner-backed
  distortion/undistortion calibration structure feeding the `0x145980` box,
  the semantic name of the uniform scale, and later `state+0x448` payload
  fields beyond this `+0x30..+0x3c` slice.

## Validation Commands

```bash
python3 -m py_compile \
  tools/lldb_probes/state_448_later_box_formula/box_formula_probe.py \
  tools/lldb_probes/state_448_later_box_formula/verify_box_formula.py
bash tools/lldb_probes/state_448_later_box_formula/run_four_zoom.sh
python3 tools/lldb_probes/state_448_later_box_formula/verify_box_formula.py
file runs/state_448_later_box_formula/box_formula_28mm.hdr \
  runs/state_448_later_box_formula/box_formula_35mm.hdr \
  runs/state_448_later_box_formula/box_formula_70mm.hdr \
  runs/state_448_later_box_formula/box_formula_150mm.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV|attach failed' \
  runs/state_448_later_box_formula
```

The `rg` check returned no matches.
