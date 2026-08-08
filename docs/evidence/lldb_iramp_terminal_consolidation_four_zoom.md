# LLDB IRAMP Terminal Consolidation Evidence

**Date:** 2026-06-18
**Status:** Runtime consolidation evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local `lri_process`, and the
canonical four-zoom bridge HDR quartet with `--no-auto-lris`.

This document validates the existing Opus-directed IRAMP terminal harness as a
reusable consolidation probe. It proves that sampled packets in one complete
four-zoom run family reach the IRAMP entry, inner worker, sentinel compare,
score multiply, tuple score store, reciprocal, and weighted-store sites with
clean render exits and internally consistent packet arithmetic.

It does not prove the complete `0x3661b0` reducer, public field names, a final
source-contribution decision, or final merge acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harness:

- `tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_probe.py`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_28mm.lldb`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_35mm.lldb`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_70mm.lldb`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/iramp_terminal_150mm.lldb`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/run_four_zoom.sh`
- `tools/lldb_probes/codex_opus_iramp_terminal_validation/verify_iramp_terminal_consolidation.py`

Generated raw reports and HDR outputs live under ignored local directory:

- `runs/codex_opus_iramp_terminal_validation/`

No live `/tmp` or `/private/tmp` artifact is cited by this evidence.

The original run command was:

```bash
bash tools/lldb_probes/codex_opus_iramp_terminal_validation/run_four_zoom.sh
```

The verifier command is:

```bash
python3 tools/lldb_probes/codex_opus_iramp_terminal_validation/verify_iramp_terminal_consolidation.py
```

## Breakpoint Sites

The harness records capped samples from these sites:

| VA | Probe name | Local role checked by verifier |
|---:|---|---|
| `0x365960` | `entry_365960` | IRAMP entry packet with `src1`, `src2`, source vector, warp vector, scale, ROI |
| `0x3661b0` | `inner_3661b0` | Inner closure packet carrying the same `src1` / `src2` pointers and output-image pointer |
| `0x36930f` | `sentinel_cmp_36930f` | Local `0x80000000` index sentinel compare sample |
| `0x36e511` | `score_mul_36e511` | Score-factor multiply packet with `sqrt(xmm0 * xmm1)` |
| `0x369e91` | `tuple_score_store_369e91` | Three-float tuple score store address packet |
| `0x36a938` | `reciprocal_36a938` | Positive uniform `xmm2` packet before reciprocal |
| `0x36aa57` | `weighted_store_36aa57` | Aligned destination `vec4` weighted-store packet |

This evidence relies on the existing static/runtime IRAMP documents for the
full instruction-window interpretation. The new verifier validates that this
single Opus-directed harness remains internally consistent and rerunnable.

## Runtime Result

Every render completed with process exit status `0`, emitted a Radiance HDR
output, and recorded exactly eight JSON events per breakpoint site.

| Zoom | JSON events | Site samples | Probe errors | Step cap | Entry source span | Entry warp span | Entry scale | Sentinel partner records |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| `28mm` | 56 | 8 per site | 0 | no | 80 bytes / 5 `0x10` items | 400 bytes / 5 `0x50` items | `2.507692337` | 1 |
| `35mm` | 56 | 8 per site | 0 | no | 80 bytes / 5 `0x10` items | 400 bytes / 5 `0x50` items | `2.507692337` | 1 |
| `70mm` | 56 | 8 per site | 0 | no | 80 bytes / 5 `0x10` items | 400 bytes / 5 `0x50` items | `2.138461590` | 1 |
| `150mm` | 56 | 8 per site | 0 | no | 80 bytes / 5 `0x10` items | 400 bytes / 5 `0x50` items | `2.138461590` | 3 |

The verifier enforces:

- process exit status `0`
- no probe errors and no drive step-cap hit
- 56 events per tier, with contiguous sequence numbers
- eight capped events for each target site
- Radiance HDR output for each tier
- entry source-vector span `80` with five 16-byte items
- entry warp-vector span `400` with five `0x50`-byte items
- stable entry `src1` / `src2` pointers per tier
- inner closure `+0x08` / `+0x10` matching the entry `src1` / `src2` pointers
- sentinel-compare samples all reading `eax == 0x80000000`
- sentinel partner-vector spans matching the sampled partner-record counts
- score multiply packets satisfying `product == xmm0 * xmm1` and
  `sqrt_product == sqrt(product)`
- tuple score-store addresses satisfying `base + index_times3 * 4 + 0x8`
- reciprocal packets satisfying `predicted_exact_reciprocal_low == 1 / xmm2[0]`
- weighted-store destinations satisfying `dest == base + byte_offset`

Verifier output:

```text
28mm: OK events=56 srcs=5 warps=5 sentinel_partner_records=1 scale=2.507692337
35mm: OK events=56 srcs=5 warps=5 sentinel_partner_records=1 scale=2.507692337
70mm: OK events=56 srcs=5 warps=5 sentinel_partner_records=1 scale=2.138461590
150mm: OK events=56 srcs=5 warps=5 sentinel_partner_records=3 scale=2.138461590
```

## Accepted Conclusions

- The Opus-directed terminal harness is reusable and now has a repo-local
  verifier.
- The sampled `0x365960` entry packets validate the already-known five-source /
  five-warp IRAMP signature in this run family.
- The sampled `0x3661b0` packets show the inner closure carrying the same
  `src1` / `src2` pointers from entry plus a nonzero output-image pointer.
- The sampled `0x36930f` packets in this harness are sentinel-side samples:
  every admitted packet has `eax == 0x80000000`.
- The sampled score multiply, tuple-score store, reciprocal, and weighted-store
  packets are internally consistent with the local arithmetic/address formulas
  recorded by the probe.

## Non-Claims

- This does not observe the valid non-sentinel target; use
  `lldb_iramp_sentinel_gate_targets_four_zoom.md` for that separate proof.
- This does not prove a one-to-one score-multiply to tuple-store mapping for
  every sampled packet. The `35mm` event order has interleaving that prevents
  that stronger claim from this harness alone.
- This does not prove public semantic names for tuple fields, score factors,
  weights, closure fields, or output channels.
- This does not prove the complete candidate predicate.
- This does not prove final source contribution, anti-ghosting behavior, or
  final merge acceptance / rejection.
- This does not strengthen the canonical ledger beyond the existing
  `CLM-MERGE-005` partial IRAMP bounds.
