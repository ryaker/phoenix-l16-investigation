# Editor RefocusSlider exact visualization formula

## Result

Installed-static extraction plus a complete controlled runtime replay closes
the public `ImageEdit::RenderMode::RefocusSlider` visualization formula.
For rendered linear float color `rgba`, scalar depth `d`, and live focus depth
`F`, the route computes:

```text
Y = (rgba.g * 0.587 + rgba.r * 0.299) + rgba.b * 0.114

s = F * 0.075
q = 1 / (s * s)
x = clamp(-((d - F) * (d - F) * q), -126, 128)
n = trunc_i32(x) + (signbit(x) ? -1 : 0)
f = x - float(n)
p = (((f * 0.07802452147006989
       + 0.22606715559959412) * f
       + 0.69583356380462646) * f
       + 0.99992519617080688)
E = bitcast_float(bitcast_u32(p) + (uint32(n) << 23))
m = (1 - E) * 0.4

out = (1 - m) * Y + m * [0, 0.75, 1, 1]
out.a = 1
```

All operations above are binary32 in installed instruction order. `E` is the
installed fast base-2 exponential approximation. The `n` rule intentionally
maps an exact negative integer one step lower and lets the polynomial at
`f=1` restore the corresponding power of two; it must not be replaced by a
generic `floorf` plus library `exp2f` when bit parity is required.

One Unit-1 `28mm`, profile-3, RenderType-1, five-level treatment with
`MaximumInFocusBlurPixels=9`, public `f_num=2`, and center-derived
`F=6020.888671875 mm` produced 388 calls at each of the scalar, mask, and
blend boundaries. Clean-room replay matched:

| Boundary | Compared values | Exact | Maximum absolute error |
|---|---:|---:|---:|
| vec4 to Rec.601 scalar | 108,720,348 pixels | 108,720,348 | 0 |
| depth to visualization mask | 108,720,348 pixels | 108,720,348 | 0 |
| scalar/mask to cyan vec4 | 434,881,392 lanes | 434,881,392 | 0 |

This closes exact mode-2 visualization math for the tested editor route. It
does not change bridge-HDR merge claims, prove other focal/body route
incidence, name or decode the eleven DebugView objects, or close general edit
history and depth-edit semantics.

## Installed proof

Installed identity:

```text
libcp b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Pinned ranges:

| Range | Role | SHA-256 |
|---|---|---|
| `0x3a900..0x3abb7` | selected type-7/16 vec4-to-float converter | `df97caff040beaa6043e59c6a23b1e17a54119b39029438d49a9aacf3c21df7f` |
| `0x3bbb43..0x3bbd83` | RefocusSlider callsite and descriptor construction | `ec6fdf181d96e721b6bcf347fabca7e914c216c21af3657de0db9b01251e441a` |
| `0x3c0fc0..0x3c1273` | scalar/mask/tint combine worker | `624dcfd6c714ae431b9b077bfc312195a89efd9b394d5be64ab935f9edb24c9e` |
| `0x3c1280..0x3c154d` | depth-distance mask worker | `d0a5ac84ca03f182d449e2ceb585e9d7f29a6e705a48bd703f3e0c1a406b43b5` |

The converter selector `0x1cd40(7,16)` returns exact installed target
`0x3a900`. Its constants at `0x5a91ec..0x5a91f4` are float32 words
`0x3e991687`, `0x3f1645a2`, and `0x3de978d5`, or exact stored values `0.299`,
`0.587`, and `0.114`. The worker multiplies green and red separately, adds
green plus red, then adds the multiplied blue value.

The callsite gets `F` from `DOFCache+0x9c`, reads the scalar depth image from
the established `RendererPrivate+0x698` path, and forms `q` with exact
float32 `0.075` at `0x6027a8`. The observed stable parameter words are:

```text
F     = 0x45bc271c = 6020.888671875
q     = 0x36a48d99 = float32(1 / float32(float32(F*0.075)^2))
one   = 0x3f800000 = 1
scale = 0x3ecccccd = 0.4
```

The mask worker uses sign mask `0x80000000`, bounds `-126` and `128`, and
polynomial words at `0x5dae2c..0x5dae38`. The combine callsite embeds exact
float32 color `[0,0.75,1,1]` at `0x602790`; `0x232440` then fills the alpha
lane with exact `1.0`.

## Runtime custody

The interposer filters the shared `0x2e7710` conversion helper to return
address `0x3bbcad`, so the scalar census excludes two other users observed in
the same treatment. It parses the callsite-built descriptor trees at
`0x3c1280` and `0x3c0fc0`, calls the installed body through a trampoline, and
replays each resulting pixel locally with contraction disabled. The report
records no parameter mismatch over 388 mask calls.

Raw rerunnable output is ignored under:

```text
runs/editor_render_type_topology/editor_refocus_slider_formula_28mm.json
runs/editor_render_type_topology/editor_refocus_slider_formula_run.log
```

## Reproduction

```bash
bash tools/lldb_probes/editor_render_type_topology/run_refocus_slider_formula.sh
python3 tools/lldb_probes/editor_render_type_topology/verify_refocus_slider_formula.py
```

The verifier SHA-pins the four installed ranges and exact constants, checks
the runtime parameter relation, and requires exact equality for every scalar,
mask pixel, and blend lane.

## Scope and admission recommendation

- Formula and constants are installed-static scope for the pinned libcp.
- Runtime route and exhaustive value comparison are one Unit-1 `28mm`
  treatment under the exact settings above.
- This is editor compatibility/reference scope, not merge-critical scope.
- Other bodies/focals, DebugView formulas/meanings, QuickSelect internals and
  commit semantics, and complete editor parity remain open.
- Admit as a `CLM-COMPAT-001` addendum; retain `PARTIAL` / `REFERENCE_ONLY`.
