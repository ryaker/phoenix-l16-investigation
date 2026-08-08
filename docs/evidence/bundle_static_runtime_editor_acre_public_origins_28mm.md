# Static/Runtime Evidence: Editor ACRE Public Parameter Origins

**Date:** 2026-07-16  
**Status:** VERIFIED, scoped `CLM-COMPAT-001` addendum  
**Runtime scope:** canonical Unit-1 `28mm`, profile 3, RenderType `1`, default
level-4 mode-0 display request  
**Static scope:** SHA-pinned installed `libcp.dylib`; property construction,
enum selection, and arithmetic are body/focal independent, while the observed
values and selected route are only the runtime scope above

## Question

The selected editor ACRE worker was formula- and byte-closed with live EV
`1.0001065731048584` and LUT `libcp+0x5e41b4`, but their public origins were
not yet joined. This bundle determines whether either value is an unexplained
editor preset.

## EV Origin

Installed request-builder code at `0x42e1ea..0x42e244` constructs the exact
property name:

```text
tone_mapping.ev_offset
```

It obtains the selected `CapturedImage`, calls the already admitted helper
`0xf3fc0`, immediately calls imported `log2f`, converts the result to the
property-map value, and stores it. The property consumer at `0x31936e..0x31938c`
reads that same leaf; `0x33eb20 -> 0x2d6cb0` writes its float32 value to the
live tone-mapper object's `+0x08` field.

The prior four-focal public-field proof established the exact helper formula:

```text
numerator = float32(float32(image_integration_time_ns) * image_gain)
denominator = float32(float32(sensor_exposure) * sensor_analog_gain)
scale = float32(numerator / denominator)
ev = log2f(scale)
```

The first selected Unit-1 `28mm` capture replays as:

```text
ViewPreferences.image_integration_time_ns = 14646091
ViewPreferences.image_gain                = 1.5348176956176758
CameraModule.sensor_exposure              = 11238709
CameraModule.sensor_analog_gain           = 1.0

numerator     = 22479080.0f
denominator   = 11238709.0f
scale         = 2.000147819519043f  (word 0x4000026c)
log2f(scale)  = 1.0001065731048584f (word 0x3f80037e)
```

That final word is exactly the runtime `lt::TMO_ACRE+0x08` word captured by
the ACRE worker probe. The merged public `ViewPreferences.ev_offset` is
present with value `0.0`, and its accessor records zero hits in the same
bridge-HDR run. Therefore the observed ACRE EV is the capture-normalization
EV written into the named tone-mapping property, not the public preference's
zero value.

## LUT Origin

The same request builder constructs exact property `tone_mapping.type`. Its
default source is a static `std::string` at `0x673e48`; installed initializer
`0x436691` builds that object directly from literal:

```text
light_v1
```

The installed tone-type schema at `0x328b1a..0x328ce9` maps:

```text
none              -> 0
default           -> 1
linear            -> 2
acr               -> 3
light_v1          -> 4
light_v1_lowlight -> 5
light_v2          -> 6
```

The property consumer resolves that schema entry and passes enum `4` to
`0x339d10`. Its seven-entry jump table sends enum `4` to `0x339f41`, which
constructs `lt::TMO_ACRE` through `0x2d76b0` with curve index `1`. The
constructor's exact four-pointer table is:

```text
index 0 -> libcp+0x5e31b0
index 1 -> libcp+0x5e41b4
index 2 -> libcp+0x5e51b8
index 3 -> libcp+0x5e61bc
```

Thus the captured LUT pointer is exactly the installed curve selected by
public property `tone_mapping.type=light_v1`; it is not an anonymous table
choice inferred from address proximity.

## Deterministic Verification

`tools/lldb_probes/editor_render_type_topology/verify_editor_display_policy.py`
now pins:

- installed Lumen and libcp SHA-256 identities;
- both exact public property strings and the `light_v1` initializer;
- the full name-to-enum map entry, enum jump table, curve-index constructor,
  and four LUT pointers;
- the `0xf3fc0 -> log2f` request-builder sequence and the final object `+0x08`
  write;
- the retained public-field packet, exact float32 replay words, runtime ACRE
  object, LUT digest, and both prior full-tile clean-room replays.

```bash
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_display_policy.py
```

The verifier returns `PASS` and records the resolved origins in
`runs/editor_render_type_topology/editor_display_policy_verification.json`.

## Admission Boundary

Safe admission under reference-only `CLM-COMPAT-001`:

- at the tested default Unit-1 `28mm` display scope, ACRE EV is exactly
  `log2f((image_integration_time_ns*image_gain) /
  (sensor_exposure*sensor_analog_gain))` in the installed float32 order;
- public property `tone_mapping.type=light_v1` maps to enum `4`, ACRE curve
  index `1`, and exact installed LUT `libcp+0x5e41b4`;
- these origins close the formerly open EV/LUT public-meaning gap for the
  already admitted selected ACRE formula.

Do not generalize the observed values or `light_v1` selection to other edits,
inputs, levels, bodies, focal tiers, low-light state, profiles, or alternate
DOF/mode routes. Display index-10 color correction remains separate and open.
