# Static and Runtime Proof: Unit-2 `0x2fd070` Denoise Selector

## Scope

This bundle closes the selector-cause gap for the exact-35mm Unit-2
`0x2fd070` sibling arm recorded in
`bundle_static_runtime_denoise_route_cnr_parameters_four_zoom.md`.

It proves `0x2fd070` is not an unexplained body-specific route or firmware
fork. It is the `flag=0`, kernel-size `9` arm of the same installed
`0x2f6420` bilateral-kernel-size dispatcher that selects `0x2fb320` for
kernel-size `5`.

This bundle does not by itself formula-close the full selected bilateral
callback-family bodies or assign public names to callback fields.

## Artifacts

Reusable probe scripts:

- `tools/lldb_probes/denoise_route_census/denoise_route_census_probe.py`
- `tools/lldb_probes/denoise_route_census/unit1_35mm_denoise_selector.lldb`
- `tools/lldb_probes/denoise_route_census/unit2_35mm_denoise_selector.lldb`
- `tools/lldb_probes/denoise_route_census/run_denoise_selector_two_body.sh`
- `tools/lldb_probes/denoise_route_census/verify_denoise_selector_2fd070.py`

Runtime reports:

- `runs/denoise_route_census/unit1_35mm_denoise_selector.json`
- `runs/denoise_route_census/unit2_35mm_denoise_selector.json`
- existing Unit-1 route-census reports
  `runs/denoise_route_census/unit1_{28mm,35mm,70mm,150mm}_denoise_algo.json`

Verifier result:

```text
denoise_selector_2fd070=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 dispatch_false=size5->0x2fb320,size9->0x2fd070 unit1_helper_kernels={5: 256} unit2_helper_kernels={5: 107, 9: 149}
```

The verifier also re-runs the existing route-census admission checks:

```text
denoise_route_census=OK
```

## Static Selector Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier pins:

| Body | Range | SHA-256 |
|---|---:|---|
| Selector `0x2f6420` | `0x2f6420..0x2f68a0` | `5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0` |
| Kernel-5 false worker | `0x2fb320..0x2fc11f` | `c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861` |
| Kernel-9 false worker | `0x2fd070..0x2fdce0` | `c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a` |

At selector entry, `0x2f6420` subtracts `3` from `r8d`, checks the result
against `6`, and uses `r9b` to choose one of two jump tables. Even kernel
sizes map to the installed `"Unsupported bilateral kernel size!"` path.

For the observed `r9b == 0` route:

| `r8d` kernel size | Jump-table index | Block | Callback address point | Slot `+0x30` worker |
|---:|---:|---:|---:|---:|
| `3` | `0` | `0x2f6712` | `0x65a6e8` | `0x2fa5d0` |
| `5` | `2` | `0x2f6791` | `0x65a768` | `0x2fb320` |
| `7` | `4` | `0x2f6882` | `0x65a7e8` | `0x2fc140` |
| `9` | `6` | `0x2f680a` | `0x65a868` | `0x2fd070` |

For `r9b != 0`, the sibling table maps the same sizes to
`0x2f6ad0`, `0x2f78e0`, `0x2f87e0`, and `0x2f97e0`. Those true-flag workers
are not selected by the two-body discriminator runs in this bundle.

## Runtime Discriminator

The two fresh exact-35mm discriminator runs both exit cleanly.

| Run | Helper `r8` first word in capped samples | Selector samples | Worker arms |
|---|---|---|---|
| Unit-1 `35mm` `L16_03041` | `{5: 256}` | `(r8=5,r9=0)` in `256/256` samples | `0x2fb320` only |
| Unit-2 exact `35mm` `L16_01956` | `{5: 107, 9: 149}` | sample cap fills before late kernel-9 selector entries | `0x2fb320` and `0x2fd070` |

Unit-1 coverage is strengthened by the already-admitted four-focal route
census: `unit1_{28mm,35mm,70mm,150mm}_denoise_algo.json` records zero
`0x2fd070` hits under the canonical Unit-1 quartet.

The Unit-2 `0x2fd070` worker samples have callback address point `0x65a868`,
slot `+0x30 = 0x2fd070`, and stack frames returning through selector return
site `0x2f6863`, the continuation after the `0x2f680a` case-block call.
By the pinned selector table, that case is exactly `r9b == 0` and
`r8d == 9`.

The Unit-2 `0x2fb320` worker samples have callback address point `0x65a768`,
slot `+0x30 = 0x2fb320`, and return through `0x2f67e7`, the continuation
after the `r9b == 0`, `r8d == 5` case-block call.

## Admission

Admit for `CLM-DENOISE-002`:

- the Unit-2 exact-35mm `0x2fd070` sibling arm is selected by the same
  installed `0x2f6420` dispatcher as the Unit-1-selected `0x2fb320` arm;
- the discriminator is the kernel-size argument, with `5 -> 0x2fb320` and
  `9 -> 0x2fd070` on the observed `r9b == 0` route;
- the Unit-2 exact-35mm route therefore reflects a parameterized
  kernel-size selection, not an unexplained body-specific or firmware-only
  route fork.

Non-admissions:

- This does not formula-close the full selected bilateral callback-family
  bodies.
- This does not assign public names to the callback descriptors, coefficient
  vectors, or helper config fields.
- This does not generalize Unit-2 exact-35mm kernel-size incidence across
  every Unit-2 focal/capture; it closes the selector mechanism and the tested
  discriminator.
