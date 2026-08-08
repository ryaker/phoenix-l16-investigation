# LLDB Differential: Final IRAMP Score Image Effect, Wide and Tele

**Date:** 2026-07-02  
**Status:** VERIFIED; admission candidate for `CLM-MERGE-005` /
`CLM-MERGE-006`  
**Direct differential scope:** canonical Unit-1 `35mm` wide and `70mm` tele  
**Joined scope:** prior complete Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`
score-use and post-IRAMP output custody

## Question

Does the continuous direct-candidate score produced by `0x36cde0` survive
IRAMP accumulation and later cache/row processing into the final Radiance HDR,
or can a later global stage replace or suppress the composited result?

## Reusable Harness

`tools/lldb_probes/final_iramp_image_effect/`

The durable components are:

- `runtime_patch.py`: verifies and patches four live process bytes;
- `baseline_35mm_{a,b}.lldb` and `zero_score_35mm.lldb`;
- `baseline_70mm_{a,b}.lldb` and `zero_score_70mm{,_b}.lldb`;
- `compare_rgbe.py`: streaming Radiance RGBE decoder/comparator;
- `verify_final_iramp_image_effect.py`: SHA, patch-receipt, image, and
  treatment/control verifier; and
- `run_probe.sh`: complete reproduction driver.

Rerunnable full-resolution HDR outputs, patch receipts, and aggregate metrics
live under ignored `runs/final_iramp_image_effect/`. No `/tmp` or
`/private/tmp` artifact is an evidence dependency.

## Isolated Intervention

The installed dylib is pinned to SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The score epilogue is:

```text
0x36e511  mulss  xmm0, xmm1
0x36e515  sqrtss xmm0, xmm0
0x36e519  add    rsp, 0xd0
...
0x36e528  ret
```

At `main`, LLDB verifies the original bytes at `libcp+0x36e515` and changes
only:

```text
f3 0f 51 c0              sqrtss xmm0,xmm0
0f 57 c0 90              xorps  xmm0,xmm0; nop
```

This occurs after all patch-statistics, detail, and normalization work inside
`0x36cde0`. It preserves the body and changes only its returned scalar score
`t` to zero. Each intervention render writes a JSON receipt containing the
loaded image header, absolute address, relative VA, original bytes, patched
bytes, write count, and successful reread.

An earlier function-entry intervention was discarded because it also skipped
in-body patch normalization. Its outputs were overwritten and are not used by
the verifier or this admission.

## Runtime Matrix

Every render used the installed signed dylib, profile `3`, `--no-auto-lris`,
and CLI HDR export at `10432x7824`.

| Focal | Control renders | `t=0` renders | Purpose |
|---|---:|---:|---|
| Unit-1 `35mm` | 2 | 1 | wide-tier discriminator |
| Unit-1 `70mm` | 2 | 2 | tele-tier discriminator with both-condition repeat floors |

The extra tele intervention replicate addresses the materially larger
thread-scheduling/render nondeterminism observed at `70mm`.

## Final HDR Results

The metric is mean absolute difference over all four stored RGBE code bytes.
It is used as a final-file discriminator, not as a perceptual quality metric.

| Comparison | Differing pixel fraction | Mean absolute RGBE-code difference |
|---|---:|---:|
| `35mm` control A vs control B | `0.007857011` | `0.006550827` |
| `35mm` control A vs `t=0` | `0.752610538` | `11.418258333` |
| `35mm` control B vs `t=0` | `0.752004068` | `11.417676695` |
| `70mm` control A vs control B | `0.482888697` | `1.784448044` |
| `70mm` `t=0` A vs `t=0` B | `0.589154495` | `2.367870528` |
| `70mm` control A vs `t=0` A | `0.946046034` | `7.888946103` |
| `70mm` control B vs `t=0` A | `0.945916519` | `7.853223855` |
| `70mm` control A vs `t=0` B | `0.946142530` | `8.001113769` |
| `70mm` control B vs `t=0` B | `0.946023686` | `7.965880512` |

The smallest wide treatment/control distance is `1742.937` times the wide
control repeat floor. At tele, the smallest of all four treatment/control
distances is `3.317` times the larger of the control/control and
intervention/intervention repeat floors. The two tele conditions therefore
remain separated despite their larger within-condition nondeterminism.

Verifier output:

```text
PASS final IRAMP image effect wide_ratio=1742.937 tele_ratio=3.317
```

## Four-Focal Join and Consequence

Prior admitted evidence establishes at `28mm`, `35mm`, `70mm`, and `150mm`:

1. the same `0x36cde0` score body is live;
2. non-sentinel `t`, including zero, has no later local score threshold and
   enters the continuous candidate multiplier and denominator;
3. the reconstructed/composited IRAMP descriptor is handed to square/AWB
   processing, `Tile<Vec3<Float16>>`, selected-cache expansion/resampling,
   the populated `linear_prophoto_rgb` row descriptor, and the Radiance HDR
   writer; and
4. those downstream image/cache bodies receive one composited descriptor,
   not the earlier per-contributor vector and tuple identities.

The return-only differential now proves final-file consequence directly on
one representative wide route and one representative tele route. Therefore,
on the tested profile-3 CLI HDR path, a later stage does not replace or
globally suppress IRAMP's candidate-weighted composited result. The exhaustive
local sentinel/record gates plus continuous `t` policy are the final
contributor-specific selection policy on this proven route; downstream work
is image-domain shaping, storage, resampling, and output.

## Admission Boundary

Admit:

- direct candidate score `t` has final Radiance HDR image effect;
- no additional per-contributor accept/reject predicate exists after the
  composited IRAMP descriptor on the admitted profile-3 CLI route;
- the final policy is continuous weighting of every surviving non-sentinel
  candidate, followed by the already-admitted image/cache/output chain; and
- the mechanism has four-focal custody/liveness, with direct image-effect
  differential discriminators at canonical `35mm` and `70mm`.

Do not generalize:

- the intervention was not rerun separately at `28mm` or `150mm`;
- this does not claim identical numeric output across renders, bodies,
  captures, or possible camera-firmware versions;
- both direct differential LRIs are from the canonical Unit-1 corpus, so the
  result is not a body comparison; and
- GUI exports or non-profile-3 routes are outside this proof.
