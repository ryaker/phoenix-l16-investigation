# Codex Audit: Opus Quarantine Validation Start, 2026-06-04

## Scope

This register records Codex validation work against Opus's quarantined branch:

- Branch: `origin/research/opus-quarantine-2026-06-02`
- Branch HEAD: `7c159c918aabce766e7d11fb94db14b6596bd538`
- Entry directory: `docs/audits/opus_findings_for_codex/`

This register is not canonical truth. It does not promote any Opus finding to
`docs/TRUTH.md`, `docs/canonical/CLAIM_LEDGER.md`, or any other canonical file.
Every Opus finding remains `NEEDS_CODEX_VALIDATION` unless a later Codex
evidence bundle or deterministic audit admits it.

## Method Boundary

The Opus branch was inspected read-only with `git show` / `git ls-tree`; it was
not checked out. Local `main` was kept as the working tree.

Codex first committed and pushed the prior verified `0x23faf0` checkpoint
before inspecting Opus material:

- Commit: `49f2557` (`Document State helper 23faf0 record chain`)

Unrelated untracked local scripts under `tools/*.py` were not staged, cited, or
used as evidence in this audit.

## Packet Set Read

The first pass read:

- `docs/audits/opus_findings_for_codex/README.md`
- `docs/audits/opus_findings_for_codex/PIPELINE_SYNTHESIS.md`
- `docs/audits/opus_findings_for_codex/terminal_merge_3661b0_FOURZOOM.md`
- `docs/audits/opus_findings_for_codex/merge_magnitudes_FOURZOOM.md`
- `docs/audits/opus_findings_for_codex/contributor_gate_FOURZOOM.md`
- `docs/audits/opus_findings_for_codex/final_compositing_consumer_FOURZOOM.md`
- `docs/audits/opus_findings_for_codex/RESIDUAL_VALIDATION_LEDGER.md`
- `docs/audits/opus_findings_for_codex/parked_residuals_decoded_FOURZOOM.md`
- `docs/audits/opus_findings_for_codex/static_submechanisms_verified_FOURZOOM.md`
- `docs/audits/opus_pending/2026-06-02/four_zoom_data_W1c.md`
- `docs/audits/opus_pending/2026-06-02/four_zoom_data_W5_magnitudes.md`
- `docs/audits/opus_pending/2026-06-02/REMEDIATION_LEDGER.md`

## First Validation Target

Codex selected the Opus terminal-merge / IRAMP claim cluster as the first
validation target because it is load-bearing for the replacement goal:

- Candidate reducer body: `0x3661b0`
- Caller-facing entry: `0x365960`
- Candidate coverage / contributor selection gate: `0x36930f`
- Candidate score producer: `0x36cde0`
- Candidate reciprocal normalizer: `0x36a938`
- Candidate weighted stores: `0x36a8c0..0x36a8cb`,
  `0x36aa30..0x36aa57`

## Independently Re-Extracted Static Facts

All facts in this section were re-extracted from the installed bundle:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

using `arch -x86_64 lldb -b` disassembly commands on 2026-06-04.

### `0x365960` Caller-Facing IRAMP Entry

Static disassembly confirms:

- `0x365960` saves the incoming arguments, including the two vectors passed in
  `rcx` and `r8`.
- `0x3659a8..0x3659cd` compares a transformed count from `r8` against the
  count from `rcx`.
- `0x365efe..0x365f4b` handles the non-empty ROI path, resizes / prepares the
  output descriptor from the ROI, and calls `0x3661b0` at `0x365f4b`.
- The call passes `rdi = rbp-0x158` and `rsi = rbx`, matching the previously
  documented entry-to-inner-body split.

This confirms the static caller/inner-body boundary. It does not by itself
prove four-zoom runtime values.

### `0x3661b0` Inner Body Shape

Static disassembly confirms:

- `0x3661b0` saves `arg0` in `r15` / `rbp-0x4388`.
- The body reads the ROI rectangle from `rsi` at entry.
- `0x366a50..0x366a61` reads `arg0+0x18` as a vector-like begin/end pair and
  computes an element count using `(end - begin) / 16`.
- `0x366b18` reads `arg0+0x8` into `r13`, a separate object used later by the
  post-reciprocal weighted-add path.
- `0x36a08f..0x36a14b` derives an output image data pointer from `arg0+0x38`
  and stores it at `rbp-0x4270`.

This confirms that Opus's corrected `ctx+0x18` contributor-vector language is
consistent with installed-bundle disassembly. It also confirms that older prose
which treated `arg0+0x8` as the same contributor vector is too imprecise.

### Contributor Selection / Coverage Gate

Static disassembly confirms the candidate selection gate:

```text
0x3692f0  leaq (%rcx,%rcx,4), %rdx
0x3692f4  shlq $0x7, %rdx
0x3692f8  movl 0x28(%rdi,%rdx), %eax
0x3692fc  imull %r13d, %eax
0x369300  addl %r8d, %eax
0x369306  movq 0x30(%rdi,%rdx), %r12
0x36930b  movl (%r12,%rsi,8), %eax
0x36930f  cmpl $0x80000000, %eax
0x369314  jne 0x369320
0x36931b  jmp 0x369f0b
```

The static shape proves an index-map read at contributor record `+0x30` and a
skip path when the read value equals `0x80000000`. It does not yet prove
four-zoom runtime values for this sentinel gate under Codex rerun.

### Tuple / Score Producer Boundary

Static disassembly confirms:

- `0x369e31..0x369e3f` calls `0x36cde0` with `rdi = rbp-0x4240` and
  `rsi = rbp-0x11a0`.
- `0x369e7e`, `0x369e8b`, and `0x369e91` store `{first, second, xmm0}` into a
  three-float output tuple after the `0x36cde0` call.
- `0x36cde0` begins at `0x36cde0`, preserves the two patch pointers as `r12`
  and `r14`, and returns through `0x36e511 mulss`, `0x36e515 sqrtss`,
  `0x36e528 retq`.

This confirms the static `sqrt(xmm0 * xmm1)` return form already present in
current canonical evidence. It does not yet validate Opus's mid-render
non-degenerate score-magnitude table.

### Reciprocal / Weighted-Add Surfaces

Static disassembly confirms:

- `0x36a8c0..0x36a8cb` loads a source `vec4`, multiplies by a `vec4` weight,
  adds the destination `vec4`, and stores the updated destination.
- `0x36a8fe` adds the current scalar into a running scalar sum.
- `0x36a934..0x36a938` broadcasts the scalar sum and computes `rcpss`.
- `0x36aa30..0x36aa57` loads a normalized source `vec4`, blends lane 3 from
  `xmm4`, multiplies by a separable weight product, adds the destination
  `vec4`, and stores the updated destination.
- `0x36ab88..0x36ac38` copies / blends the accumulated local tile back into
  the real output-image data pointer previously stored at `rbp-0x4270`.

This confirms the static accumulator surfaces. It does not yet prove Opus's
claimed four-zoom runtime `Σscore` values.

## Current Validation Status

| Claim cluster | Codex status | Notes |
|---|---|---|
| `0x365960 -> 0x3661b0` static caller/inner split | STATIC CONFIRMED | Fresh installed-bundle re-disassembly matches the candidate. |
| `0x3661b0` uses `arg0+0x18` vector count | STATIC CONFIRMED, RUNTIME COUNT-USE CONFIRMED | Fresh re-disassembly confirms the corrected vector location. The first 2026-06-04 runtime harness sampled `0x3661b0` entry, but its closure-vector reads were rejected as count evidence. The follow-up `0x366a65` probe then sampled the actual post-`sarq` count-use site and verified live count `5` for all four canonical focal tiers. |
| `0x36930f` sentinel skip gate | STATIC CONFIRMED, BRANCH TARGETS RUNTIME CONFIRMED | The compare/skip sequence is real. The 2026-06-04 Codex rerun sampled the first eight compare hits per focal tier and all sampled `eax` values were `0x80000000`. The 2026-06-05 branch-target rerun then confirmed both `0x36931b` sentinel-skip packets with `eax == 0x80000000` and `0x369320` valid-target packets with non-sentinel table values across all four canonical focal tiers. This is branch-target evidence, not full candidate-policy closure. |
| `0x36cde0` returns `sqrt(xmm0*xmm1)` | STATIC CONFIRMED, RUNTIME MAGNITUDE CONFIRMED | Already consistent with current evidence. The 2026-06-04 rerun captured live first-window packets; the 2026-06-05 W5 reproduction captured representative nonzero score factors, product, and square-root result on all four focal tiers. Opus's exact sample rows are still not admitted as constants. |
| `0x36a938` reciprocal normalizer | STATIC CONFIRMED, RUNTIME MAGNITUDE CONFIRMED | The instruction is real. The 2026-06-04 first-eight sample set saw `xmm2_low == 0.200000003` for all four focal tiers; the 2026-06-05 W5 reproduction captured non-common denominators on all four focal tiers and verified `rcpss` approximates `1/xmm2`. This is representative magnitude evidence, not a full `sum(score)` census. |
| `0x36aa30..0x36aa57` weighted destination store | STATIC CONFIRMED, RUNTIME PARTIAL | Already consistent with current evidence. The 2026-06-04 rerun captured live destination-store packets at `0x36aa57`; public field/weight semantics remain unproven. |
| Opus phrase "`0x3661b0` is the N-to-1 score-normalized weighted-average reducer" | NOT YET ADMITTED | Static pieces are promising, but canonical promotion requires a Codex-owned runtime rerun of contributor counts, sentinel-gate behavior, score/denominator magnitudes, and output-store context. |

## Codex Runtime Harness Result, 2026-06-04

Codex created and ran a local no-auto-LRIS harness:

- Harness: `tools/lldb_probes/codex_opus_iramp_terminal_validation/`
- Command: `bash tools/lldb_probes/codex_opus_iramp_terminal_validation/run_four_zoom.sh`
- Raw outputs: `runs/codex_opus_iramp_terminal_validation/`
- Sample cap: eight recorded packets per target VA per focal tier.
- Target VAs: `0x365960`, `0x3661b0`, `0x36930f`, `0x369e91`,
  `0x36a938`, `0x36aa57`, `0x36e511`.

The first sandboxed attempt failed at `process launch` with `lost connection`
before any JSON report was written. The same command then completed under the
same elevated LLDB/debugserver permission class used by earlier successful
probes. The completed run wrote four full-size HDR outputs and four JSON
reports under the repo-owned `runs/` directory; no live `/tmp` or
`/private/tmp` artifact is cited by this audit.

Runtime health summary:

| Focal tier | LRI | Process exit | JSON events | Errors | Entry source count | Entry warp count | Entry scale | First-eight sentinel samples | First-eight reciprocal denominator |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 28mm | `2018-07-23/L16_02130.lri` | `0` | 56 | 0 | 5 | 5 | `2.507692` | 8/8 `0x80000000` | `0.200000003` |
| 35mm | `2018-12-26/L16_03041.lri` | `0` | 56 | 0 | 5 | 5 | `2.507692` | 8/8 `0x80000000` | `0.200000003` |
| 70mm | `2019-05-18/L16_03434.lri` | `0` | 56 | 0 | 5 | 5 | `2.138462` | 8/8 `0x80000000` | `0.200000003` |
| 150mm | `2018-07-29/L16_02285.lri` | `0` | 56 | 0 | 5 | 5 | `2.138462` | 8/8 `0x80000000` | `0.200000003` |

Sampled score / store ranges from the JSON reports:

| Focal tier | Tuple score range at `0x369e91` | `sqrt(xmm0*xmm1)` range at `0x36e511` | `xmm1` low-lane range before `0x36aa57` store |
|---|---:|---:|---:|
| 28mm | `0..0.684525967` | `0..0.684525995` | `-1.5260408e-05..2.93675239e-05` |
| 35mm | `0..0.488706499` | `0..0.776478814` | `-8.50486595e-06..3.02012559e-05` |
| 70mm | `0..0` | `0..0` | `-7.62457785e-05..4.72249085e-05` |
| 150mm | `0..1` | `0..1` | `-4.16435723e-05..9.29167873e-05` |

Accepted conclusions from this runtime pass:

- Under `--profile 3 --export-fmt 3 --no-auto-lris`, all four canonical focal
  tiers reached the sampled terminal IRAMP sites and completed rendering.
- At `0x365960`, the sampled entry packets showed source count `5` and warp
  count `5` for all four focal tiers.
- At `0x36930f`, the sampled first-eight packets per focal tier all observed
  `eax == 0x80000000`.
- At `0x36a938`, the sampled first-eight packets per focal tier all observed
  low-lane denominator `0.200000003`, corresponding to reciprocal about `5.0`.
- At `0x36e511`, live factor/product/square-root packets were captured,
  including non-zero values for 28mm, 35mm, and 150mm under this sample window.
- At `0x36aa57`, live weighted-store packets were captured for all four focal
  tiers.

Rejected / not-yet-admitted conclusions:

- The harness does not prove the full runtime distribution of sentinel and
  non-sentinel paths; it proves only the first-eight sampled packets per focal
  tier.
- The harness does not prove the full denominator / `sum(score)` distribution;
  all sampled reciprocal denominators were `0.2`, so deeper magnitude sampling
  remains required.
- The harness does not prove `0x3661b0` runtime contributor count from
  `arg0+0x18`; the entry-packet closure-vector read is explicitly rejected as
  count evidence.
- The harness does not prove a clean-room algorithm or Lumen-quality parity.

## Count-Use Follow-Up Result, 2026-06-04

Codex then created and ran a focused later-instruction harness:

- Evidence document: `docs/evidence/lldb_iramp_count_use_vector_four_zoom.md`
- Harness: `tools/lldb_probes/codex_iramp_count_use_validation/`
- Raw outputs: `runs/codex_iramp_count_use_validation/`
- Breakpoint: `libcp+0x366a65`, immediately after
  `0x366a61 sarq $0x4,%rbx`.

The target static window is:

```asm
0x366a50  movq  0x18(%r15), %rcx
0x366a54  movq  (%rcx), %rax
0x366a57  movq  0x8(%rcx), %rcx
0x366a5b  movq  %rcx, %rbx
0x366a5e  subq  %rax, %rbx
0x366a61  sarq  $0x4, %rbx
0x366a65  je    0x366ae1
```

The corrected rerun completed cleanly across all four focal tiers:

| Focal tier | Process exit | Events | Breakpoint hits | Probe errors | Disabled after cap | `(end-begin)` | Computed count | Live `rbx` |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 28mm | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| 35mm | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| 70mm | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |
| 150mm | `0` | 16 | 16 | 0 | yes | 80 | 5 | 5 |

This closes the narrow runtime count-use question for the sampled canonical
four-zoom bridge HDR quartet. It does not close full contributor acceptance,
full denominator distributions, public vector semantics, or the complete
`0x3661b0` reducer algorithm.

## W5 Magnitude Reproduction Result, 2026-06-05

Codex then created and ran a W5 reproduction harness:

- Evidence document: `docs/evidence/lldb_iramp_w5_magnitude_repro_four_zoom.md`
- Harness: `tools/lldb_probes/codex_opus_w5_magnitude_repro/`
- Raw outputs: `runs/codex_opus_w5_magnitude_repro/`

The harness used LLDB core-handled ignore-count / conditional breakpoints.
Python was used only after breakpoint stops to read registers and write JSON;
it was not installed as a per-hit callback.

Accepted runtime score captures:

| Focal tier | Capture | Factor A | Factor B | Product after `mulss` | Score after `sqrtss` |
|---|---|---:|---:|---:|---:|
| 28mm | `score_28mm` | `0.845083833` | `1.000000000` | `0.845083833` | `0.919284403` |
| 35mm | `score_nonzero_35mm` | `0.283306062` | `0.843024850` | `0.238834053` | `0.488706499` |
| 70mm | `score_nonzero_70mm` | `0.660202682` | `0.800213039` | `0.528302789` | `0.726844430` |
| 150mm | `score_150mm` | `0.941425800` | `1.000000000` | `0.941425800` | `0.970270991` |

Accepted reciprocal captures:

| Focal tier | `xmm2` before `rcpss` | Exact `1/xmm2` | `xmm2` after `rcpss` |
|---|---:|---:|---:|
| 28mm | `0.399711609` | `2.501803745` | `2.501953125` |
| 35mm | `1.023340702` | `0.977191661` | `0.977294922` |
| 70mm | `0.902118564` | `1.108501743` | `1.108398438` |
| 150mm | `1.149109244` | `0.870239279` | `0.870239258` |

The first fixed-ignore score attempts for `35mm` and `70mm` landed on real
zero-factor packets in this Codex run, so they were rejected as
non-degenerate-score evidence and replaced by condition-only nonzero captures.

This reproduces the W5 method and admits representative non-degenerate
arithmetic at the score and reciprocal sites. It does not admit Opus's exact W5
numeric table as constants, does not provide a full distribution, and does not
close the complete reducer algorithm.

## Sentinel-Gate Branch-Target Result, 2026-06-05

Codex then created and ran a focused branch-target harness:

- Evidence document: `docs/evidence/lldb_iramp_sentinel_gate_targets_four_zoom.md`
- Harness: `tools/lldb_probes/codex_iramp_sentinel_gate_validation/`
- Raw outputs: `runs/codex_iramp_sentinel_gate_validation/`
- Target sites: `0x36931b` sentinel skip target and `0x369320` valid target.

The final accepted run followed two rejected harness attempts:

- Python absolute-address breakpoints did not bind to `libcp` and produced zero
  hits.
- Shared-library breakpoints then stopped correctly, but missing breakpoint-ID
  mapping prevented cap-disable on the first 28mm rerun; that run was
  terminated and not admitted.

The corrected harness capped each branch target at 12 packets per focal tier
and completed cleanly:

| Focal tier | Process exit | Sentinel-target packets with `eax == 0x80000000` | Valid-target packets | Valid table-low-dword matches `eax` | Valid `eax` range | Partner-record count in sampled window |
|---|---:|---:|---:|---:|---:|---:|
| 28mm | `0` | 12/12 | 12 | 12/12 | `-1..150` | 1 |
| 35mm | `0` | 12/12 | 12 | 12/12 | `8..644` | 1 |
| 70mm | `0` | 12/12 | 12 | 12/12 | `5..194` | 1 |
| 150mm | `0` | 12/12 | 12 | 12/12 | `-1..185` | 4 |

Accepted conclusion: both local branch targets are runtime-live on the
canonical four-zoom bridge HDR quartet. `0x36931b` is reached with the sentinel
value preserved in `eax`, and `0x369320` is reached with non-sentinel table
values that match the low dword read from `r12 + rsi * 8`.

Non-claim: this is not a full sentinel/valid distribution, not final
contributor acceptance, not downstream score-threshold policy, and not full
`0x3661b0` reducer closure.

## Terminal Producer-Barrier Correction, 2026-06-05

Codex re-read the Opus terminal packet's "producer barrier" language against
current committed evidence and fresh installed-bundle disassembly. The packet's
claim that `0x3ebf5d` is the unresolved producer boundary for
`PipelineCache+0x258` / `PipelineCache+0x270` is not admitted.

Fresh static logs:

- `runs/codex_opus_terminal_producer_correction/static_3ebb80_visible_src2_descriptor.log`
- `runs/codex_opus_terminal_producer_correction/static_3ec770_iramp_processlevel0_args.log`

The `0x3ebb80` window shows `0x3ebf5d` in the already-proven visible-`src2`
source-descriptor construction path:

- `0x3ebf36` zeroes stack descriptor `rbp-0x2200`.
- `0x3ebf3d` loads `PipelineCache+0x1d8` into `rdi`.
- `0x3ebf48` loads vtable slot `+0x18`.
- `0x3ebf5d` calls the loaded slot target with `rsi = rbp-0x2200`.
- `0x3ec41a` later stores the descriptor into callback field `+0x08`.
- `0x3ec462` dispatches the generic executor that consumes the callback.

Existing runtime evidence
[lldb_src2_descriptor_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_descriptor_origin_four_zoom.md)
and
[lldb_src2_406a10_branch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_406a10_branch_four_zoom.md)
already admits the runtime target of that visible-`src2` vtable slot as
`0x406a10` across the canonical four-zoom quartet.

Separately, the `0x3ec770` `processLevel0` window shows the IRAMP argument
handoff:

- `0x3ec7ac`: `rsi = *(PipelineCache+0x238)`
- `0x3ec7b3`: `rdx = *(PipelineCache+0x248)`
- `0x3ec7c2`: `rcx = PipelineCache+0x270`
- `0x3ec7c9`: `r8 = PipelineCache+0x258`
- `0x3ec7da`: calls `0x365960`

Existing evidence
[bundle_proof_iramp_live_signature_and_warp_records.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_live_signature_and_warp_records.md)
admits those `+0x270` / `+0x258` offsets as live IRAMP arguments and records
their consumption through `0x365960 -> 0x3661b0`.

Accepted correction: `0x3ebf5d` is the visible-`src2` source-descriptor
producer call boundary, not a proven producer for the IRAMP
`PipelineCache+0x270` source-vector or `PipelineCache+0x258` paired-record
vector. The upstream producers of `+0x270` and `+0x258` remain separate
unknowns unless proven by their own runtime/static custody chain.

## Opus Internal Tension Noted

Some Opus packets contain both "four-zoom OBSERVED" banners and older body
sections that still say "static only" or "runtime owed." Codex should not admit
packet-level status. Each finding must be split into atomic static or runtime
claims and validated separately.

## Next Validation Steps

1. If exact Opus W5 sample rows matter, build a hit-window-specific reproduction
   harness; otherwise keep the admitted W5 fact at representative magnitude
   scope.
2. Continue reducing `0x3661b0` from arithmetic surfaces into a complete
   accept/reject/store topology before considering any "full reducer" claim.

## Non-Claims

- This audit does not prove Lumen-quality merge parity.
- This audit does not prove a clean-room implementation specification.
- This audit does not admit Opus's pipeline synthesis as truth.
- This audit does not prove public semantic names for tuple fields, score
  fields, weight tables, or output channels.
- This audit does not close final anti-ghosting acceptance / rejection logic.
