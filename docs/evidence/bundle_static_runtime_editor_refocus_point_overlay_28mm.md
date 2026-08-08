# Editor RefocusPoint exact post-DOF overlay

## Result

Installed-static extraction plus two complete controlled runtime replays close
the post-DOF visualization applied by public
`ImageEdit::RenderMode::RefocusPoint`. For the rendered linear-float input
`rgba`, scalar depth `d`, focus interval `[lower, upper]`, and live overlay
color `c`, the installed loop computes in binary32 instruction order:

```text
outside = (d < lower) || (upper < d)
a = outside ? c.a : 0
tint = [c.r, c.g, c.b, 1]
out = (1 - a) * rgba + a * tint
```

The comparisons are strict, so either endpoint is classified in focus. The
interval is produced immediately beforehand by installed helper `0x3f08c0`
from the DOF cache and public `MaximumInFocusBlurPixels`; its optical range
math is independently closed by the prior mode-1 optical-radius evidence.

One Unit-1 `28mm`, profile-3, RenderType-1, five-level treatment used public
`f_num=2`, center-derived `focus_depth=6020.888671875 mm`, and stable live
`c=[1,0,0,0.25]`. Two public maximum-blur settings exercise both outcomes:

| Maximum blur | Interval, mm | Outside pixels | Exact lanes | Maximum error |
|---:|---:|---:|---:|---:|
| `9.0` | `[163.2976531982422, 79525.2421875]` | 0 / 108,720,348 | 434,881,392 / 434,881,392 | 0 |
| `0.10000000149011612` | `[2886.326416015625, 16448.662109375]` | 88,002,783 / 108,720,348 | 434,881,392 / 434,881,392 | 0 |

The narrow treatment contains both inside- and outside-focus pixels. This
therefore validates both predicate outcomes and the complete four-lane blend,
not only an all-inside no-op case.

This closes the mode-1 post-DOF visualization loop for the tested editor
route. It does not alter bridge-HDR merge claims, establish other body/focal
incidence, or close the upstream DOF compositor beyond its separate admitted
evidence.

## Installed proof

Installed identity:

```text
libcp b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Pinned ranges:

| Range | Role | SHA-256 |
|---|---|---|
| `0x3bbdc4..0x3bbf12` | depth descriptor, interval call, predicate, and in-place blend | `040054dc579329d268f523783a4fd6ade326b024bacef0e6f9348d6ad4a7e609` |
| `0x3f08c0..0x3f0af0` | focus-interval helper | `08e439445e6d314790f45a6f4d6778d8057ac6d3a08b8789893a5eacbbfa0fdc` |

The inline body reads scalar depth through the established
`RendererPrivate+0x698` path, loads live color at `+0x8d0`, and passes public
ParamFloat(19) `MaximumInFocusBlurPixels` from `+0x8e0` to the interval
helper. The blend's exact `1.0f` word is stored at `0x5a8128`.

## Runtime custody

The interposer hooks `0x3f08c0` and filters its direct return to `0x3bbe28`.
An assembly entry shim captures the caller's output descriptor, renderer, and
frame pointer before a C prologue can repurpose their registers. The probe
copies the pre-overlay color and scalar depth, lets the installed loop run,
then independently replays every predicate and float lane at the original
`0x3bbf06` cleanup boundary. Both processes exit normally with 388 interval
calls, 388 overlay calls, no descriptor mismatch, and no parameter drift.

Raw rerunnable outputs are ignored under:

```text
runs/editor_render_type_topology/editor_refocus_point_overlay_28mm_max9.json
runs/editor_render_type_topology/editor_refocus_point_overlay_28mm_max0p1.json
```

## Reproduction

```bash
bash tools/lldb_probes/editor_render_type_topology/run_refocus_point_overlay.sh
python3 tools/lldb_probes/editor_render_type_topology/verify_refocus_point_overlay.py
```

The verifier pins the installed binary and both code ranges, requires the
exact observed intervals and treatment parameters, proves the narrow run
contains both predicate outcomes, and accepts only bit-exact equality for all
869,762,784 compared output lanes.

## Scope and admission recommendation

- Formula and instruction ordering are installed-static scope for the pinned
  libcp.
- Runtime route and exhaustive comparisons are one Unit-1 `28mm` input under
  the two exact settings above.
- This is editor compatibility/reference scope, not merge-critical scope.
- Other bodies/focals and complete edit semantics remain open.
- Admit as a `CLM-COMPAT-001` addendum; retain `PARTIAL` / `REFERENCE_ONLY`.
