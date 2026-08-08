# CCM Public Illuminants and Live Selection

## Question

Name public `ColorCalibration.type` values found in the three records per
calibrated camera, and prove how the installed renderer selects/blends them
mid-render across the canonical focal quartet.

## Reusable artifacts

- `tools/lldb_probes/ccm_illuminant_selection/ccm_illuminant_selection_probe.py`
- `tools/lldb_probes/ccm_illuminant_selection/{28mm,35mm,70mm,150mm}.lldb`
- `tools/lldb_probes/ccm_illuminant_selection/run_four_zoom.sh`
- `tools/lldb_probes/ccm_illuminant_selection/verify_ccm_illuminant_selection.py`
- ignored reports under `runs/ccm_illuminant_selection/`

Reproduce:

```bash
sh tools/lldb_probes/ccm_illuminant_selection/run_four_zoom.sh
```

The verifier independently parses the installed serialized
`color_calibration.proto` descriptor, parses the 42 public color-calibration
records from each canonical LRI, pins the installed interpolation bodies, and
joins runtime matrices byte-for-byte to their public records.

## Public schema result

Installed `color_calibration.proto` SHA-256
`986015aea1758f57c5fa36e2d29d68eafe81fc5b563a6c28fedae1a18f5f937d`
defines:

```text
ColorCalibration.type = IlluminantType

0  A
1  D50
2  D65
3  D75
4  F2
5  F7
6  F11
7  TL84
99 UNKNOWN
```

Every canonical LRI has exactly 42 `ColorCalibration` records:

```text
14 x type 0 = A
14 x type 2 = D65
14 x type 6 = F11
0 x type 1 = D50
```

Thus the checklist premise that the three stored variants are A/D50/D65 is
refuted. The exact public mapping is:

```text
f2.f1 / ColorCalibration.type 0 = A
f2.f1 / ColorCalibration.type 2 = D65
f2.f1 / ColorCalibration.type 6 = F11
```

## Installed selection formula

The live calibration pair struct exposes:

```text
+0x08  internal light-source enum for matrix 1
+0x0c  internal light-source enum for matrix 2
+0x10  color matrix 1
+0x34  color matrix 2
```

The internal light-source enum is different from the public protobuf enum:
internal `2` is A and internal `7` is D65.

SHA-pinned body `0x350bc0`:

1. converts the live input chromaticity `(x,y)` to scene CCT through
   `0xab2e0`;
2. converts both calibration light-source enums to endpoint CCTs through
   `0xab4c0`;
3. obtains the two 3x3 matrices through getters `0x3504e0`/`0x350500`; and
4. calls SHA-pinned `0xab720`.

For A and D65, `0xab720` computes:

```text
m_scene = clamp(1 / T_scene, 1 / T_D65, 1 / T_A)
alpha   = (m_scene - 1 / T_D65) / (1 / T_A - 1 / T_D65)
M       = M_D65 + alpha * (M_A - M_D65)
```

All operations use float32 intermediates. This is clamped interpolation in
reciprocal color temperature (mired space); there is no extrapolation beyond
A/D65.

## Runtime result

All four final admitted runs exit `0` and write HDR. Tele uses a one-entry
snapshot that disables its breakpoint immediately to avoid the known
debugger-timing race.

| Focal | Captured calls | Live internal pair | Exact public matrix-byte join |
|---|---:|---|---|
| `28mm` | `12` | `(2,7)` = A/D65 | 9 public cameras |
| `35mm` | `11` | `(2,7)` = A/D65 | 8 public cameras |
| `70mm` | `1` | `(2,7)` = A/D65 | B4/key-8 public records |
| `150mm` | `1` | `(2,7)` = A/D65 | B4/key-8 public records |

For every runtime sample:

- matrix 1 exactly equals one same-camera public type-`0` A
  `color_matrix`;
- matrix 2 exactly equals the same-camera public type-`2` D65
  `color_matrix`; and
- the same-camera public type-`6` F11 matrix differs and is not selected.

The completed wide captures additionally prove:

| Focal | Scene CCT | A endpoint | D65 endpoint |
|---|---:|---:|---:|
| `28mm` | `4953.66357421875 K` | `2855.63232421875 K` | `6502.08203125 K` |
| `35mm` | `4922.08349609375 K` | `2855.63232421875 K` | `6502.08203125 K` |

The verifier reconstructs every captured wide interpolated matrix with exact
float32 word equality: `108/108` words at 28mm and `99/99` at 35mm.

## Admission boundary

Admit:

- public stored variants are A, D65, and F11, not A, D50, and D65;
- the tested bridge-HDR CCM/AWB interpolation path selects same-camera A and
  D65 public `color_matrix` records;
- F11 is stored but unselected at every captured call;
- libcp uses live scene chromaticity to perform the pinned clamped mired-space
  A/D65 interpolation.

Runtime pair selection is four-focal. Exact output-matrix reconstruction is
complete-wide plus installed-same-mechanism tele because the tele probe is
intentionally reduced to one entry snapshot. This does not claim F11 is
unused by every non-bridge or GUI path.
