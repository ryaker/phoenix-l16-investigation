# PatchNLM Weight Formula: Installed Static Proof + Live Operand Replay

## Result

The selected profile-3 `ImageDenoisePatchNLM<4>` callback family is
formula-closed. For a candidate 4x4 patch `C` and reference 4x4 patch `R`,
all operations below are float32/SSE operations in installed instruction
order:

```text
A[c] = sum over the 16 patch positions p of abs(C[p][c] - R[p][c])
D    = max(A[0], A[1], A[2], A[3])
V[c] = 16 * coefficient[c] * range_scale[pixel][c]
q[c] = rcpps(V[c])
w[c] = max_sse(0, 1 - max_sse(0, D - V[c]) * q[c])
sum[c]      += w[c]
weighted[c] += w[c] * candidate_source[c]
output[c]    = rcpps(sum[c]) * weighted[c], c in {0,1,2}
output[3]    = preserve_source[3]
```

`rcpps` is used without Newton refinement. The distance is one scalar shared
by RGB after a maximum over the four accumulated lanes, but the threshold and
weight are componentwise. Lane 3 has zero range scale in the live packet;
`V[3]=0`, `q[3]=+inf`, and SSE NaN/max behavior makes `w[3]=0`. The final
`blendps $8` restores lane 3 from the preserve-source descriptor.

The immediate caller constructs the coefficient as
`strength * (1, config+0x0c, config+0x0c, 1)`. The accepted Unit-1 28mm
packet is `strength=1.4`, `config+0x0c=2`, hence
`(1.4,2.8,2.8,1.4)`. It also carries `r8d=5` and `r9d=2`, matching the
admitted window and phased reference step. The later topology addendum closes
the derived radius and candidate checkerboard.

## Installed proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

| Range | SHA-256 | Role |
|---|---|---|
| `0x3066d0..0x306d40` | `bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8` | parent setup / four callback dispatches |
| `0x3070e0..0x307d90` | `862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb` | patch distance, tent, weighted accumulation |
| `0x307d90..0x307ea7` | `1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab` | reciprocal normalization / lane-3 preserve |
| `0x2f57e7..0x2f5826` | `c8229b174916baad2cf67e523c1547519989d4e7ec89101125946fa52b90ada8` | coefficient-vector construction |
| `0x2f5b03..0x2f5b31` | `b458de38366c215988c85239939cac082eee1b22b9e7cbbe76dec4fbaf94a3f6` | selected positive-body callsite |

The verifier also pins `(16,16,16,16)`, `(1,1,1,1)`, and the four-lane
`0x7fffffff` absolute-value mask. The patch loop advances by `0x40` four
times through `0x100` bytes, consuming exactly sixteen `vec4` patch samples.

## Runtime replay

The compact probe captured the first event on the tent's sloped branch from a
complete Unit-1 28mm profile-3 render. Input LRI SHA-256 is
`2ac51af5c219639638ba34bb98975b62ee922331214043a938a7c37052700ff5`.

```text
D = 0.34896159172058105
V = (0.3310309052467346, 0.6001805663108826,
     0.7186398506164551, 0)
q = (3.02099609375, 1.666015625, 1.3916015625, +inf)
w = (0.9458314776420593, 1, 1, 0)
replay delta = 0
process exit = 0
```

## Scope

The exact formula is SHA-pinned installed-bundle proof and is independent of
focal tier. Runtime arithmetic replay is Unit-1 28mm. Existing accepted route
census in `bundle_static_runtime_denoise_route_cnr_parameters_four_zoom.md`
proves the same `0x3066d0 -> 0x3070a0/0x3070e0 -> 0x307d90` family is live at
Unit-1 28mm, 35mm, 70mm, and 150mm; exact-35mm Unit-2 also selects it. This
does not assign a public protobuf name or upstream calibration origin to the
generated `range_scale` image.

## Reproduction

```bash
tools/lldb_probes/nlm_weight_formula/run_28mm.sh
python3 tools/lldb_probes/nlm_weight_formula/verify_nlm_weight_formula.py
```
