# C6 Terminal Filter: Static + Runtime Differential

## Question

Does the proven `CapturedImage.is_enabled = 0` mutation at
`libcp+0x3c90a5` terminally exclude tele C6 from the successful super-resolution
output path, or can C6 remain image-effective through an alternate route?

## Method

The probe makes one controlled intervention after the proven clear:

```text
break at 0x3c90a9
identify key 15 / C6 through item+0x60
confirm item+0x30 == 0
baseline: leave byte unchanged
forced-active: write only item+0x30 = 1
continue the complete render
```

Two baseline and two forced-active repeats were run independently at each
canonical tele focal tier.

Reusable artifacts:

- `tools/lldb_probes/c6_is_enabled_differential/c6_is_enabled_differential_probe.py`
- `tools/lldb_probes/c6_is_enabled_differential/{70mm,150mm}_{baseline,forced}_{1,2}.lldb`
- `tools/lldb_probes/c6_is_enabled_differential/run_differential.sh`
- `tools/lldb_probes/c6_is_enabled_differential/verify_c6_is_enabled_differential.py`
- ignored raw outputs under `runs/c6_is_enabled_differential/`

Reproduce:

```bash
sh tools/lldb_probes/c6_is_enabled_differential/run_differential.sh
```

## Installed static boundary

The verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and the complete `0x3e74e0..0x3e77c8` per-key `SourceImageCache` payload
constructor.

The relevant installed sequence is:

```asm
0x3e763c  call  0x3de260
0x3e7644  call  0xf2750       ; returns item+0x58
0x3e7649  mov   0x4(%rax),%ecx
0x3e764c  or    (%rax),%ecx
0x3e764e  js    0x3e7708
...
0x3e771d  lea   "Super-res does not support mono modules!",%rsi
0x3e773c  call  0x7820        ; throw
```

The independent public-origin verifier proves `item+0x58/+0x5c` is
`CameraModule.sensor_bayer_red_override.{x,y}`. On both physical bodies, C6
is the unique tele item with public pair `(-1,-1)`. The constructor therefore
classifies an enabled C6 as unsupported mono input.

## Runtime matrix

All eight runs independently reached the post-clear transaction exactly once
for key `15`, with `active_before = 0`.

| Focal | Condition | Repeats | Intervention | Exit | Output | Result |
|---|---|---:|---|---:|---|---|
| `70mm` | baseline | 2 | none | `0` | populated `10432x7824` HDR | success |
| `70mm` | forced-active | 2 | one-byte `0 -> 1` | `1` | zero-byte file | `Super-res does not support mono modules!` |
| `150mm` | baseline | 2 | none | `0` | populated `10432x7824` HDR | success |
| `150mm` | forced-active | 2 | one-byte `0 -> 1` | `1` | zero-byte file | `Super-res does not support mono modules!` |

Every forced transaction reports:

```text
key = 15
active_before = 0
write_count = 1
write_error = null
active_after = 1
```

The baseline repeats have ordinary nondeterminism:

| Focal | baseline-to-baseline ImageMagick MAE | normalized MAE |
|---|---:|---:|
| `70mm` | `254.06` | `0.00387671` |
| `150mm` | `120.509` | `0.00183885` |

No cross-condition pixel metric exists because the forced-active path
deterministically rejects before writing image data. That rejection is the
measured acceptance consequence.

## Joined terminal proof

This differential closes the remaining interpretation gap when joined to the
already admitted route evidence:

1. public C6 is constructed enabled;
2. `0x3c90a5` clears its public `is_enabled` byte;
3. all later same-byte watchpoint stops observe `0`;
4. direct payload and stereo candidate gates filter the inactive item;
5. all 58 direct key-getter callsites have tele census coverage;
6. the residual rect/ImagePyramid geometry route is fully zero-filled, has
   zero selected downstream-candidate hits, and has zero first/middle/last
   data-watch hits across all five levels; and
7. undoing only the clear causes the installed per-key image payload
   constructor to reject C6's public mono override before output.

For the tested canonical tele bridge-HDR path, C6 is therefore a fired module
that must be terminally excluded from successful super-resolution image
payload construction by `is_enabled = 0`. A clean-room implementation should
not admit C6 as a tele super-resolution image contributor.

## Scope and non-conclusions

- Runtime focal scope: canonical Unit-1 `70mm` and `150mm`, two baseline and
  two forced-active repeats each.
- Cross-body support: the public C6 `sensor_bayer_red_override=(-1,-1)`
  identity is independently verified on both physical bodies; the
  forced-active render differential itself is not repeated on Unit-2.
- Installed static scope: pinned `libcp.dylib`.

This closes `CLM-C6-001` for canonical tele bridge HDR. It does not claim C6
hardware is absent, does not generalize to non-bridge or GUI paths, and does
not identify behavior for an imaginary C6 with a non-mono public override.
