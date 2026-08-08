# Static + Direct-Runtime Proof: Pipeline Slot 15 Is Linear-ProPhoto Materialization

## Question

The admitted payload order named index `15` from public RTTI as
`Pipeline::setToneMapping`, but did not classify the callback's pixel
operation. This bundle asks whether that callback applies a nonlinear
photographic tone/look curve or performs another operation.

## Scope

This proof combines SHA-pinned installed-bundle inspection with direct
x86_64 execution of the installed constructors and selected row converter.
Existing retained target censuses supply Unit-1 `28/35/70/150mm` liveness for
the three slot-15 wrappers.

It proves the fixed destination configuration and the equal-config behavior.
It does not claim that every live wrapper invocation sees an equal input
configuration, enumerate unequal source configurations observed in profile 3,
or close every alternate color-space converter selected by `0xaa110`.

## Fixed Destination Packet

The once initializer at `0x2d6d20` allocates `0x34` bytes, constructs
`ColorSpace(5)` through `0xa9910`, and invokes `0xa9ea0` with target selector
`5` and `ChromaticAdaptation` value `1`. Embedded property schema independently
maps selector `5` to public `linear_prophoto_rgb`.

Direct installed-code execution reproduces the singleton byte for byte. Its
layout is:

| Offset | Meaning | Exact value |
|---|---|---|
| `+0x00..+0x20` | RGB-to-XYZ matrix, row-major float32 | see below |
| `+0x24` | white `x` | `0.34566918015480042` (`0x3eb0fb8d`) |
| `+0x28` | white `y` | `0.35849618911743164` (`0x3eb78cd0`) |
| `+0x2c` | source color-space selector | `5` |
| `+0x30` | target color-space selector | `5` |

Exact matrix:

```text
[ 0.79767489433288574, 0.13519169390201569, 0.031353399157524109 ]
[ 0.28804019093513489, 0.71187412738800049, 0.00008569999772589654 ]
[ 0,                   0,                   0.82520997524261475  ]
```

This is the installed linear-ProPhoto/D50 configuration already independently
identified at the final output boundary.

## Wrapper Behavior

The Bayer (`0x34a610`), BayerFloat (`0x34a780`), and Color (`0x34a8f0`)
wrappers are structurally identical:

1. obtain the singleton above;
2. compare its source selector, white point, nine matrix floats, and target
   selector against the current image descriptor's `+0x48..+0x78` config;
3. return immediately if every field compares equal;
4. otherwise tail-call `0xa9f20` in place with adaptation argument `1` and
   the singleton as destination configuration.

RTTI at `0x5ab2e0` names the worker exactly as
`ImageConvertColorSpace(Image<vec4x32f>&, Image<vec4x32f> const&,
ColorSpace const&, ColorSpace const&, ChromaticAdaptation)::$_0`.

There is no nonlinear tone/look function in any of the three slot-15
wrappers. Their concrete operation is conditional color-space
materialization to linear ProPhoto/D50.

## Equal-Config Pixel Formula

For destination selector `5` and source selector `5`, `0xaa110` selects row
converter `0xab940`. The equal-whitepoint branch of `0xa9340` returns exact
float32 identity. A direct fixture containing negative, zero, ordinary,
greater-than-one, and nontrivial lane-3 values passed through the installed
converter with the singleton on both sides returns all eight float words
bit-for-bit unchanged.

Thus, when the incoming descriptor already carries the fixed
linear-ProPhoto/D50 packet:

```text
dst(x,y).rgba = src(x,y).rgba    // exact 16-byte copy
```

No clamp, transfer curve, exposure shaping, alpha/lane-3 replacement, or
fitted "Lumen look" is applied in this case.

## Four-Focal Consequence

The retained exact target sets in
`lldb_src1_virtual_target_census_four_zoom.md` prove these slot-15 wrappers
live beneath the Unit-1 visible-source producer at all canonical focal tiers.
The installed callback bodies are shared and contain no focal/body/firmware
selector. Four-focal liveness therefore supports the stage classification,
while actual equal-versus-unequal branch incidence remains explicitly open.

That final incidence boundary is closed for the tested profile-3 route by the
follow-up
`bundle_lldb_pipeline_slot15_branch_incidence_four_zoom_two_body.md`: the
complete Unit-1 quartet records `4,684` equal/copy branches and zero unequal
conversions, with targeted Unit-2 wide/tele controls agreeing at their stated
scopes.

## Reproduction

```bash
python3 tools/lldb_probes/pipeline_linear_prophoto_stage/verify_pipeline_linear_prophoto_stage.py
```

Expected terminal lines include:

```text
slot15_target=linear_prophoto_rgb selector=5 adaptation=1
source_enum=5 target_enum=5
converter_5_5=0xab940 equal_whitepoint_matrix=identity fixture=bit_exact_copy
payload_wrappers=0x34a610,0x34a780,0x34a8f0 conditional_in_place_conversion=1
```

Reusable artifacts:

- `tools/lldb_probes/pipeline_linear_prophoto_stage/dump_pipeline_color_config.c`
- `tools/lldb_probes/pipeline_linear_prophoto_stage/run_dump.sh`
- `tools/lldb_probes/pipeline_linear_prophoto_stage/verify_pipeline_linear_prophoto_stage.py`

The verifier pins the installed `libcp.dylib` SHA-256, all constructor,
matrix-builder, dispatcher, converter, and payload-wrapper body ranges used by
the conclusion, the public selector label, and the worker RTTI/vtable edge.

## Admission Boundary

Safe admission: payload slot `15`, despite its setter name, is a conditional
linear-ProPhoto/D50 color-space materialization stage. Equal matching configs
are exact copies. A clean-room implementation must not insert a fitted
nonlinear look/tone curve at this slot.

This bundle alone does not admit universal no-op incidence, observed source
config distribution, generic conversion formulas for every unequal selector
pair, or any body/firmware cause. The follow-up branch-incidence bundle closes
the tested profile-3 source-config distribution and exact-copy outcome only at
its explicit four-focal/two-body scope.
