# Evidence: Focus-Dependent K Bracket Policy

## Result

G-37 is closed for the installed focus-dependent intrinsics evaluator at
`0x1f96e0`. The handoff premise that the supported LRIs supply three focus
bundles is false for the checked corpus: every camera in all eight exact-focal
representatives from the two physical calibration signatures supplies exactly
two public `CalibrationFocusBundle` records. The retained canonical runtime
packets exercise that two-record branch at `28mm`, `35mm`, `70mm`, and
`150mm`.

The installed helper also contains explicit one-record and three-record
policies. Those branches are admitted from SHA-pinned installed-bundle static
proof so a clean-room reader does not need to assume that two records are the
only serialization the binary can accept.

## Public Inputs

For one camera, the helper receives parallel vectors of:

- public `FactoryModuleCalibration.geometry.per_focus_calibration[].intrinsics.k_mat`
  records, each represented internally as nine doubles; and
- the corresponding public
  `FactoryModuleCalibration.geometry.per_focus_calibration[].focus_hall_code`
  values, represented internally as signed integers and converted to float32.

The evaluation coordinate is the live public
`LightHeader.modules[camera].lens_position`, also converted from signed integer
to float32.

## Exact Selection Policy

The helper stably sorts the float32 Hall coordinates ascending and carries an
index vector through the same swaps. Let the sorted pairs be
`(h0,K0)`, `(h1,K1)`, and optionally `(h2,K2)`, and let `x` be the live
float32 lens position.

```text
one record:   copy K0 unchanged

two records:  use (h0,K0) and (h1,K1) for every x

three records:
    if x < h1: use (h0,K0) and (h1,K1)
    else:      use (h1,K1) and (h2,K2)
```

The `x == h1` case selects the upper pair. Values below `h0` or above the last
coordinate are extrapolated; there is no endpoint clamp and no nearest-record
selection.

For each selected scalar field value `y`, the mathematical blend coordinate
is:

```text
t = (x - h_lo) / (h_hi - h_lo)
y = y_lo + t * (y_hi - y_lo)
```

For bit-compatible output, the installed helper evaluates the equivalent
slope/intercept form with float32 rounding after every instruction:

```text
slope     = f32(f32(y_hi - y_lo) / f32(h_hi - h_lo))
intercept = f32(y_lo - f32(h_lo * slope))
y         = f32(f32(x * slope) + intercept)
```

It evaluates only row-major K fields `{0,2,4,5}` this way. It first copies the
complete first stored K record, then overwrites those four fields. Thus fields
`{1,3,6,7,8}` retain the first stored record's values; "first stored" is the
input record at vector offset zero, not necessarily the first sorted record.

The two-record path rejects a Hall-coordinate separation whose absolute
float32 value converts to double below `0.001`. The three-record path first
requires strict `h0 < h1 < h2`, then applies the same `0.001` separation guard
to the selected pair. The installed exception labels are respectively
`"x_1 and x_2 are very close. Slope close to infinity."` and
`"x ordering wrong, need ascending order"`.

## Installed Static Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier pins these windows:

| Window | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `0x1f96e0..0x1f9fb2` | 2258 | `d9782d0824cb3a8ce5ce2d10ed6fb5bbe9d013c2da92f1ddcd0d207912974e5d` | complete non-exception policy |
| `0x1f995d..0x1f99ed` | 144 | `7f879de9769967612adb17ddd76cbf76f16546d41cb63b750e03c8f41ffa12dc` | stable ascending sort |
| `0x1f9a33..0x1f9c3d` | 522 | `e5269a4f159955072e89e9ac93fc2cb53e2abc851b3d2dc02e17c18908ab8dc6` | two-record evaluator |
| `0x1f9c3d..0x1f9fb2` | 885 | `8bb0b944c82fed17ad5113ceb1d33ed70b5c3a02411612bc7129584b6b36d1ed` | three-record selector/evaluator |

Capstone assertions independently pin the compare/branch decisions, both
segment arithmetic sequences, record-2 indexed load, and output copy. The
installed double at `0x5d42c8` is exactly `0.001`.

## Public-Payload Census

The structural LRI verifier selects the compact 16-camera intrinsics block
without assuming its byte size. It finds exactly two qualifying
`(focus_hall_code,k_mat)` records for every one of the 16 cameras in every
checked file:

| Physical calibration signature | Focals | Payload bytes | Per-camera count |
|---|---|---:|---:|
| Unit-1 `722a6e721636c9c4` | `28/35/70/150mm` | 32832 | 2 |
| Unit-2 `223961c6bce6153e` | `28/35/70/150mm` | 32833 | 2 |

The one-byte payload-size difference is body calibration serialization, not a
record-count difference. Capture date and possible firmware differences are
not assigned as causes.

## Runtime Join

The retained `0x1f96e0` reports independently verify every selected camera in
complete canonical Unit-1 `28/35/70/150mm` renders. For each call, both helper
records and both scalar coordinates exactly match the same-camera public LRI
records, the live scalar equals `CameraModule.lens_position`, and all four
evaluated K fields match the installed float32 formula bit-for-bit. Both final
CalibStage selector calls receive the evaluated result.

No three-record runtime incidence is claimed because none exists in the eight
exact-focal/two-body public calibration payloads checked here.

## Scope And Admission

- Public payload cardinality: two physical calibration signatures, exact-focal
  `28/35/70/150mm` representatives, 16 cameras per file.
- Runtime formula join: canonical Unit-1 `28/35/70/150mm`, all selected
  cameras in the retained reports.
- One/two/three-record policy: installed-bundle static proof, body/focal
  independent for this binary.
- This closes G-37's bracket-pair policy and exact blend evaluation.
- It does not claim a three-record LRI incidence, body/firmware causation, or
  closure of unrelated composed-geometry fields.

Admit as a `CLM-WARP-003` addendum. Claim status remains unchanged.

## Reproduction

```bash
python3 tools/lldb_probes/g37_focus_k_policy/verify_g37_focus_k_policy.py
```

Expected terminal marker:

```text
g37_focus_k_policy=OK
```
