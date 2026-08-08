# Final-Stage Constants: Installed Static + Four-Focal Runtime Proof

## Question

Independently recover and verify:

1. the four wavelet-detail weights at `libcp+0x5fdb10`;
2. the seven-tap Gaussian coefficients used by the sharpen path;
3. the spatial support/falloff of `ImageDenoiseBilateralGeneric<5,true>`;
4. the live NLM search window/radius; and
5. the SIMD absolute-value mask at `libcp+0x5a81f0`.

This bundle does not rely on an Opus interpretation. It pins the installed
`libcp.dylib` and checks the runtime values independently.

## Reusable artifacts

- `tools/lldb_probes/final_stage_constants/final_stage_constants_probe.py`
- `tools/lldb_probes/final_stage_constants/unit1_{28mm,35mm,70mm,150mm}.lldb`
- `tools/lldb_probes/final_stage_constants/run_unit1_four_zoom.sh`
- `tools/lldb_probes/final_stage_constants/verify_final_stage_constants.py`
- ignored raw reports: `runs/final_stage_constants/unit1_{28mm,35mm,70mm,150mm}.json`

Reproduce:

```bash
tools/lldb_probes/final_stage_constants/run_unit1_four_zoom.sh
python3 tools/lldb_probes/final_stage_constants/verify_final_stage_constants.py
```

The verifier requires installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## A1: wavelet detail weights

The exact 16 bytes at `0x5fdb10` are:

```text
ab aa aa bb  ab aa 2a bc  ab aa aa bc  ab aa 2a bd
```

Interpreted as little-endian float32:

| Scale | Word | float32 | Exact source value before float32 rounding |
|---:|---:|---:|---:|
| 1 | `0xbbaaaaab` | `-0.0052083334885537624` | `-1/192` |
| 2 | `0xbc2aaaab` | `-0.010416666977107525` | `-1/96` |
| 4 | `0xbcaaaaab` | `-0.02083333395421505` | `-1/48` |
| 8 | `0xbd2aaaab` | `-0.0416666679084301` | `-1/24` |

The installed values therefore form the requested dyadic `1:2:4:8`
sequence. This is installed-bundle static proof and is not zoom-dependent.

## A2: seven-tap Gaussian

Installed RTTI identifies `ConvLineFactory<float,7>` and its wrapped
`HConvBuffer<float,7>` implementation. The generator at `0x96980` implements
the normalized centered Gaussian coefficient construction; its installed
body and the `0x3588f0` seven-tap worker are independently SHA-pinned by the
verifier.

At the return from `0x35f940 -> 0x96980`, all four complete canonical
Unit-1 renders captured the same 28 bytes:

```text
4fd6403d 2838f43d 1c44553e 3b6a803e 1c44553e 2838f43d 4fd6403d
```

The exact float32 coefficients are:

```text
0.047079380601644516
0.11924773454666138
0.20826762914657593
0.2508104741573334
0.20826762914657593
0.11924773454666138
0.047079380601644516
```

They are symmetric and sum to float32-normalized unity within ordinary
rounding. Runtime scope is `28mm`, `35mm`, `70mm`, and `150mm`, all clean
exit under `--no-auto-lris`.

## A3: bilateral spatial kernel

Installed RTTI names the selected body
`ImageDenoiseBilateralGeneric<5,true>`. The full body
`0x2f78e0..0x2f860e` is SHA-pinned. Its worker:

- expands the requested region by radius `2`;
- executes five horizontal samples per row;
- iterates exactly five rows (`mov edx,5` at `0x2f8418`);
- applies the same data/range tent calculation to every one of the 25
  offsets; and
- contains no offset-indexed coefficient read or `dx`/`dy`-dependent
  spatial multiplication.

Thus the spatial factor for this installed specialization is the uniform
box:

```text
S(dx,dy) = 1,  if |dx| <= 2 and |dy| <= 2
         = 0,  otherwise
```

The separately admitted tent factor remains the data/range weight. This
result is installed-bundle static proof only. It does not claim that this
specialization is the selected first-visible-`src1` route; the admitted
route census selects sibling body `0x2fb320` under that tested gate.

## A4: NLM search radius

Installed RTTI names both callback bodies as
`ImageDenoisePatchNLM<4>`. The property block contains the public keys
`nlm_denoiser.window_size`, `patch_size`, and `step_size`; the SHA-pinned
configuration transfer stores those values in the first three config
words.

At `0x2f5b2c`, 16 samples per complete canonical focal render agreed:

```text
config[0] / window_size = 5
config[1] / patch_size  = 5
config[2] / step_size   = 2
r8                      = 5
r9                      = 2
```

For the odd full search window, the search radius is therefore
`(window_size - 1) / 2 = 2` pixels, i.e. offsets `[-2,+2]`. Runtime scope is
the canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` quartet, with 16
consistent observations per focal tier.

## A5: absolute-value mask

The exact 16 bytes at `0x5a81f0` are four little-endian lanes of
`0x7fffffff`. Applied with packed bitwise AND, this clears each float32 sign
bit and preserves exponent/mantissa:

```text
abs_mask = (0x7fffffff, 0x7fffffff, 0x7fffffff, 0x7fffffff)
```

This is installed-bundle static proof and is not zoom-dependent.

## Verifier result

```text
static_final_stage_constants=OK ... bilateral=uniform_5x5
28mm: OK ... window_size=5 search_radius=2 step_size=2
35mm: OK ... window_size=5 search_radius=2 step_size=2
70mm: OK ... window_size=5 search_radius=2 step_size=2
150mm: OK ... window_size=5 search_radius=2 step_size=2
final_stage_constants=OK
```

## Admission boundary

Admit the five exact constants/formulas above. This bundle does not by
itself close the complete sharpen/denoise pipeline, merge acceptance,
public meanings of unrelated internal vectors, or the pre-fusion reducer.
