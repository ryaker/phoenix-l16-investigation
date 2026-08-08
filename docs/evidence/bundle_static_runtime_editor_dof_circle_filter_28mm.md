# Evidence: Editor DOF Uniform Circle Filter

**Date:** 2026-07-16  
**Status:** VERIFIED, reference-only editor scope  
**Installed bundle:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

## Scope

This bundle closes the exact `lt::ImageCircleFilter<lt::vec4x32f>` and
`lt::ImageCircleFilter<float>` aperture kernels and their edge policy.
Formula proof is SHA-pinned installed static proof. Liveness and radius
incidence come from one Unit-1 `28mm`, profile-3, RenderType-1 mode-1 DOF
treatment.

It does not close the caller's blur-layer selection, foreground/background
occlusion logic, or final layer composition.

## Artifacts

- Runtime interposer:
  `tools/lldb_probes/editor_render_type_topology/capture_editor_dof_math_interpose.c`
- Runner:
  `tools/lldb_probes/editor_render_type_topology/run_editor_dof_math.sh`
- Verifier:
  `tools/lldb_probes/editor_render_type_topology/verify_editor_dof_circle_filter.py`
- Runtime report:
  `runs/editor_render_type_topology/editor_dof_math_mode1_blur9_f2.json`

The verifier pins both constructors, both worker bodies, and their initial-sum
helpers by full-body SHA-256, then independently decodes the decisive
instructions with Capstone.

## Exact Kernel

For integer radius `r > 0`, define one horizontal half-width per vertical
offset:

```text
h(dy) = floor(sqrt(r*r - dy*dy)),  dy in [-r,r]
```

The support is the inclusive integer lattice disk:

```text
D(r) = {(dx,dy): dy in [-r,r], dx in [-h(dy),h(dy)]}
count(r) = sum_dy (2*h(dy)+1)
weight(r) = float32(1.0 / float32(count(r)))
```

For either scalar or four-float pixels:

```text
output(x,y) = weight(r) *
              sum_(dx,dy in D(r))
                input(clamp(x+dx,xmin,xmax),
                      clamp(y+dy,ymin,ymax))
```

Every included lattice point has the same weight. There is no Gaussian,
radial feather, polygonal aperture weight, or edge renormalization. Border
samples are replicated by coordinate clamp, so the constant full-disk count
and normalization remain in force at image edges.

The implementation uses an initial clamped disk sum followed by incremental
add/subtract updates as the output coordinate advances. The vec4 specialization
uses `addps/subps/mulps`; the scalar specialization uses
`addss/subss/mulss`. This operation order matters for bit-exact reproduction.

## Observed Radius Kernels

```text
r=1 h=[0,1,0]                         count=5   weight=0.20000000298023224 bits=cdcc4c3e
r=2 h=[0,1,2,1,0]                     count=13  weight=0.07692307978868485 bits=d9899d3d
r=3 h=[0,2,2,3,2,2,0]                 count=29  weight=0.03448275849223137 bits=cb3d0d3d
r=4 h=[0,2,3,3,4,3,3,2,0]             count=49  weight=0.02040816284716129 bits=052fa73c
r=5 h=[0,3,4,4,4,5,4,4,4,3,0]         count=81  weight=0.01234567910432816 bits=88454a3c
r=6 h=[0,3,4,5,5,5,6,5,5,5,4,3,0]     count=113 weight=0.00884955748915672 bits=bcfd103c
r=7 h=[0,3,4,5,6,6,6,7,6,6,6,5,4,3,0] count=149 weight=0.00671140942722559 bits=62ebdb3b
```

The treatment records `2,335` vec4 calls with radii `1..6` and `375` scalar
calls with radii `1..7`. Those counts and ranges are treatment incidence, not
algorithm constants or proof that other runs cannot request other positive
radii.

## Verification

```text
static_circle_filter=OK vec4_and_float_builders_workers
runtime_circle_filter=OK vec4_calls=2335 radii=1..6 float_calls=375 radii=1..7
```

Run:

```bash
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_dof_circle_filter.py
```

## Admission Boundary

Admit as a `CLM-COMPAT-001` reference-only addendum. The exact circle kernel
and border behavior are installed-static same-mechanism proof; runtime
liveness is one Unit-1 `28mm` treatment. Do not infer complete DOF composition,
other mode behavior, or cross-focal runtime incidence.
