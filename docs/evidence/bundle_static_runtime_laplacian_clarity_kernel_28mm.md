# Laplacian-Pyramid Clarity Kernel and Parameters

## Question

Close checklist E1 by identifying the installed Laplacian-pyramid clarity
formula, its public tuning names, and a runtime-active parameter packet.

## Reusable artifacts

- `tools/lldb_probes/laplacian_clarity/laplacian_clarity_probe.py`
- `tools/lldb_probes/laplacian_clarity/laplacian_clarity_28mm.lldb`
- `tools/lldb_probes/laplacian_clarity/run_28mm.sh`
- `tools/lldb_probes/laplacian_clarity/verify_laplacian_clarity.py`
- ignored raw report and HDR under `runs/laplacian_clarity/`

Reproduce the complete probe and verifier:

```bash
bash tools/lldb_probes/laplacian_clarity/run_28mm.sh
```

Or recheck the pinned installed binary and retained runtime packet:

```bash
python3 tools/lldb_probes/laplacian_clarity/verify_laplacian_clarity.py
```

No live `/tmp` or `/private/tmp` artifact is an evidence dependency.

## Installed identity and public controls

Installed RTTI for callback vtable address point `0x659eb0`, typeinfo
`0x659f00`, and operator body `0x2e7360` names:

```text
CreateAndBlendLaplacianPyramids(... LaplacianPyramidConfig)::$_0
```

At runtime, seven property-lookup sites immediately preceding dedicated
setters resolve this exact `LaplacianPyramidConfig` prefix:

| Config offset | Public tuning name |
|---|---|
| `+0x00` | `lpyr_clarity` |
| `+0x04` | `lpyr_shadows` |
| `+0x08` | `lpyr_highlights` |
| `+0x0c` | `lpyr_sigma` |
| `+0x10` | `lpyr_lower_percentile` |
| `+0x14` | `lpyr_higher_percentile` |
| `+0x18` | `lpyr_mid_percentile` |
| `+0x20` | start of the float sample vector |

The installed embedded `renderer_state.proto` independently contains
`.ltpb.Settings.clarity`, optional float field `9`. This evidence does not
claim a direct byte-copy relation between that protobuf field and the
`lpyr_clarity` tuning property.

## Exact transfer kernel

Body `0x2e4cf0` allocates `0x1f71 = 8049` float samples. For
`i = 0..8048`, it computes:

```text
x_i = -16 + i * (32 / 8048)

T(x_i) =
    clamp(x_i, -2*sigma, 2*sigma)
  + clarity * x_i * exp(-(x_i*x_i) / (2*sigma*sigma))
```

Here `clarity = config+0x00` (`lpyr_clarity`) and
`sigma = config+0x0c` (`lpyr_sigma`). The verifier pins the complete
instruction range implementing the LUT, including:

- sample count `8049`;
- float step `0.00397614297` (`32/8048`);
- lower coordinate `-16`;
- symmetric clamp factor `2`;
- Gaussian denominator `-2`; and
- the `exp` call and final base-plus-detail addition.

The constructor at `0x2e3f30` installs this default prefix:

```text
lpyr_clarity          = 0.0
lpyr_shadows          = 1.0
lpyr_highlights       = 1.0
lpyr_sigma            = 0.5
lpyr_lower_percentile = -8.0
lpyr_higher_percentile= 0.2f
lpyr_mid_percentile   = -1.0
```

Its default sample vector is the 19-value sequence
`[-8.0, -7.5, ..., 0.5, 1.0]`.

## Pyramid blend

Callback `0x2e7360` evaluates each source Laplacian coefficient `p` against
the uniformly spaced sample vector:

```text
u    = clamp((p - sample[0]) / (sample[1] - sample[0]), 0, bins - 1)
lo   = floor(u)
hi   = min(lo + 1, bins - 1)
frac = clamp((p - sample[lo]) / (sample[1] - sample[0]), 0, 1)

mapped = (1 - frac) * pyramid[lo] + frac * pyramid[hi]
alpha  = pow(0.75, level)
dest   = alpha * mapped + (1 - alpha) * dest
```

The `pyramid[k]` term is the corresponding pixel in the Laplacian pyramid
created for transfer sample `k`. Thus the implementation interpolates between
adjacent transformed pyramids, then decays the replacement contribution by
`0.75^level`.

## Runtime scope

The canonical Unit-1 `28mm` no-auto-LRIS bridge-HDR run:

- completed with exit status `0` and wrote a populated Radiance HDR;
- entered `0x2e4cf0` 67 times and callback `0x2e7360` 590 times;
- resolved every public property name above through 273 lookup hits;
- observed the constructor-default seven-float prefix;
- observed callback `sample[0] = -8`, reciprocal spacing `2`, and `19` bins;
  and
- exercised pyramid levels `0,1,2,3,4`.

Counts are evidence-run observations, not algorithm constants. The formula and
defaults are installed-bundle static proof; runtime liveness is explicitly
single-zoom `28mm` scope.

## Admission boundary

Admit as `CLM-SHARPEN-002`:

- the exact 8049-sample clarity transfer formula and constants;
- the exact adjacent-pyramid interpolation and `0.75^level` blend;
- the public `lpyr_*` config names and offsets;
- the constructor defaults and 19-sample default vector; and
- active five-level execution under the canonical Unit-1 `28mm` render.

This closes checklist E1 at formula level. It does not generalize the observed
five-level count to every image size or profile, prove GUI-setting custody, or
claim four-zoom runtime coverage for this non-merge-critical path.
