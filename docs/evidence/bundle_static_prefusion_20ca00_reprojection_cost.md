# Installed-Bundle Proof: `0x20ca00` Reprojection Cost And Ray-Scale Solve

## Scope

This note independently checks the older Opus research claim that the
Triangulator path uses a one-parameter reprojection solve.

The high-level claim is supported, with two exact corrections:

1. `0x20ca00` is the executor callback inside
   `lt::Triangulator::refine3dPoints()`, not the method entry.
2. address point `0x667240` belongs to
   `ceres::AutoDiffCostFunction<lt::Internal::ReProjectionCost, ...>`, not to
   a raw `ReProjectionCost` vtable.

This is installed-bundle type, wiring, loss-payload, and residual-formula
proof. It does not assign a public LRI field, physical unit, or final depth-map
meaning to the solved scalar.

## Repo-Local Verifier

`tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_reprojection_cost_static.py`

The verifier reads the installed Mach-O directly, checks exact typeinfo and
imported-symbol names, SHA-guards five instruction windows, decodes their
anchors with Capstone, resolves RIP-relative targets, and verifies the literal
double payloads.

## Exact Cost Type

Address point `0x667240` has typeinfo name:

```text
ceres::AutoDiffCostFunction<
  lt::Internal::ReProjectionCost,
  2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0>
```

Its substantive `Evaluate` slot is `+0x10 = 0x20ded0`. The template arguments
and constructor writes agree on two residuals and one scalar parameter block.
The wrapper stores its `ReProjectionCost` functor pointer at `+0x28`.

## Residual And Loss Wiring

The parent constructs a `ceres::CauchyLoss` object at `rbp-0x288`. Its two
double payload fields are exactly `(1.0, 1.0)`. The parent captures that object
at callable `+0x28`; callback `0x20d54e` reloads the same pointer as the
`LossFunction*` argument to imported
`ceres::Problem::AddResidualBlock(CostFunction*, LossFunction*, double*)`.

The other call arguments are:

```text
rdi = callback-local ceres::Problem at rbp-0xc0
rsi = stored AutoDiffCostFunction wrapper
rdx = captured CauchyLoss object
rcx = one double parameter at rbp-0xc8
```

## Residual Formula

On the residual-only `Evaluate` path, let:

```text
s  = the one scalar parameter
bx = functor double at +0x00
by = functor double at +0x08
M  = functor 3x4 double matrix at +0xa0..+0xf8
u0 = functor double at +0x50
v0 = functor double at +0x58
```

The installed instructions compute:

```text
ray = (bx*s, by*s, s, 1)
(X,Y,Z) = M * ray
residual[0] = X/Z - u0
residual[1] = Y/Z - v0
```

The single scalar is therefore an internal scale along ray `(bx,by,1)` in a
two-coordinate reprojection objective. Calling it an internal **ray-depth
scale** is supported by the named cost type and exact formula. Its public
physical unit and LRI origin are not established here.

The separate post-solve formula verifier proves that the same local parameter
slot `rbp-0xc8` is consumed after `ceres::Solve` to reconstruct and transform
the selected owner record's three-float output.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_reprojection_cost_static.py
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
wrapper=ceres::AutoDiffCostFunction<lt::Internal::ReProjectionCost, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0>
address_point=0x667240 evaluate=0x20ded0
loss=ceres::CauchyLoss payload=(1.0,1.0) captured_at=callable+0x28
parameter=one scalar residuals=two
ray=(functor[0]*s,functor[8]*s,s)
point=M3x4(functor+0xa0)*ray_homogeneous
residual=(point.x/point.z-functor[0x50],point.y/point.z-functor[0x58])
```

## Proven Facts

1. `0x667240` is the address point of the named one-parameter, two-residual
   `AutoDiffCostFunction<ReProjectionCost,...>` wrapper.
2. The callback passes that wrapper, the captured unit-payload Cauchy loss,
   and local double `rbp-0xc8` to `AddResidualBlock`.
3. The residual-only evaluator scales ray `(bx,by,1)` by that scalar, applies a
   3x4 transform, perspective-divides, and subtracts stored coordinates.
4. The same scalar slot is consumed by the separately verified post-solve
   record reconstruction formula.
5. The earlier selected sentinel-gate proof therefore excludes one local
   `ReProjectionCost` residual for each admitted skipped pair iteration.

## Safe Conclusion

The installed `0x20ca00` callback contains a robust one-scalar ray-depth
reprojection solve, and its local sentinel gate has a precise consequence:
admitted skipped pairs do not contribute their local `ReProjectionCost`
residual.

This does not prove public depth units, the scalar's LRI origin, runtime solved
values, all-pairs terminality, image/source contribution, reducer closure, or
final acceptance/rejection.

