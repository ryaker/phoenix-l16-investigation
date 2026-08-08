# Static/Runtime Evidence: MonoFusion Mode Selector by Renderer Profile

**Date:** 2026-07-02  
**Status:** VERIFIED; canonical `CLM-PREFUSION-002` closure candidate  
**Canonical scope:** profile-3 bridge HDR, Unit-1 `28/35/70/150mm`, with
exact-focal Unit-2 `28/70mm` discriminators  
**Compatibility scope:** profile matrix on canonical Unit-1 `35mm`

## Question

Is unobserved MonoFusion mode `1` reachable on the canonical profile-3 path,
or must its separate `0x19f790` formula be decoded for parity?

## Reusable Harness

`tools/lldb_probes/prefusion_monofusion_mode_selector/`

- `mode_selector_probe.py`
- `profile{0,1,2,3}.lldb`
- `run_all.sh`
- `verify_mode_selector.py`

The verifier also consumes the admitted two-body reports under
`runs/prefusion_monofusion_worker/` and
`runs/prefusion_monofusion_identity/`. Rerunnable profile reports, HDRs, and
the aggregate verification packet live under ignored
`runs/prefusion_monofusion_mode_selector/`.

No `/tmp` or `/private/tmp` artifact is an evidence dependency.

## Installed Selector Custody

Installed `libcp.dylib` is pinned to SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The sole MonoFusion owner-construction path:

1. calls selector `0x40b2b0` at `0x406746`;
2. moves returned `%al` into `%r8d` at `0x40674b`;
3. calls constructor thunk `0x1b17b0` at `0x40676b`;
4. tail-enters constructor `0x1b1360`; and
5. stores `%r8b` once into `MonoFusion+0x00` at `0x1b1389`.

Worker `0x1b37a0` compares that byte at `0x1b39c6`. Nonzero calls mode-1
body `0x19f790` through the unique direct call at `0x1b3aae`; zero calls
mode-0 body `0x1a3c00` through the unique direct call at `0x1b3b61`.

The selector's input is the same installed
`lt::Internal::PipelineBase::Demosaicking` config passed to sibling converter
`0x40b1d0`. Installed RTTI contains that exact public C++ type name, and the
sibling converter maps enum values `0/2` to installed string `light_v2` and
`1/3` to `light_v1`.

Selector `0x40b2b0` has the exhaustive formula:

```text
enum 0 -> mode 0
enum 1 -> mode 1
enum 2 -> mode 1
enum 3 -> mode (config.byte_4 == 0)
other  -> throw "Invalid Renderer profile!"
```

The public meaning of `config.byte_4` is not required for canonical closure:
its runtime value and the selector result are directly captured below.

## Same-LRI Profile Matrix

The matrix uses canonical Unit-1 `35mm`
`2018-12-26/L16_03041.lri` and the public
`CIAPI::Renderer::Create(RendererProfile)` API exposed by the repo-local
runner.

| Renderer profile | Demosaicking `(enum,byte_4)` | Stored mode | Mode-0 calls | Mode-1 calls | Render result |
|---:|---|---:|---:|---:|---|
| `0` | `(0,1)` | `0` | `0` | `0` | later fails: invalid pyramid level |
| `1` | `(1,1)` | `1` | `0` | `48` | complete `10432x7824` HDR |
| `2` | `(2,1)` | `1` | `0` | `48` | complete `10432x7824` HDR |
| `3` | `(3,1)` | `0` | `282` | `0` | complete `10432x7824` HDR |

Counts are observations from these renders, not algorithm constants.

This proves mode `1` is real and reachable. It is not dead code. It belongs
to Renderer profiles `1` and `2` for this input, while the canonical Desktop
profile `3` deterministically selects mode `0`.

## Canonical Four-Focal Exclusion

The existing full-render reports provide the focal and body join:

| Scope | MonoFusion result |
|---|---|
| Unit-1 `28mm` profile 3 | mode `0`; mode-1 calls `0` |
| Unit-1 `35mm` profile 3 | mode `0`; mode-1 calls `0` |
| Unit-2 `28mm` profile 3 | mode `0`; mode-1 calls `0` |
| Unit-1 `70mm` profile 3 | no MonoFusion construction; direct tele adapter |
| Unit-1 `150mm` profile 3 | no MonoFusion construction; direct tele adapter |
| Unit-2 `70mm` profile 3 | no MonoFusion construction; direct tele adapter |

Thus the canonical quartet is exhaustive by route:

```text
28mm / 35mm: MonoFusion mode 0
70mm / 150mm: no MonoFusion
```

Possible camera-firmware differences across capture dates are not used as a
causal explanation. The Unit-2 checks are discriminators for route
portability only.

Verifier output:

```text
PASS MonoFusion selector profiles=0->0,1->1,2->1,3->0 canonical_wide=mode0 canonical_tele=no-MonoFusion
```

## Admission and Implementation Consequence

For the canonical profile-3 clean-room parity target:

- the already-admitted mode-0 formula is the complete wide `src2`
  MonoFusion implementation;
- tele uses the already-admitted direct B4 descriptor route;
- mode `1` is formally excluded from all four canonical focal routes; and
- no mode-1 formula stub is needed in the profile-3 spec.

Mode `1` remains an explicitly unsupported compatibility path for
Renderer profiles `1` and `2`. A future implementation claiming those
profiles must decode `0x19f790`; this evidence does not provide that formula.
