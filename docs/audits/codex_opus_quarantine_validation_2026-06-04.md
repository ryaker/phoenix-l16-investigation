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
| `0x3661b0` uses `arg0+0x18` vector count | STATIC CONFIRMED, RUNTIME COUNT STILL OWED | Fresh re-disassembly confirms the corrected vector location. The 2026-06-04 runtime harness sampled `0x3661b0` entry, but its closure-vector reads are not accepted as count evidence because the sampled entry packets produced non-countable overlapping raw pointer fields. A later-instruction probe at the actual count-use site is still required. |
| `0x36930f` sentinel skip gate | STATIC CONFIRMED, RUNTIME PARTIAL | The compare/skip sequence is real. The 2026-06-04 Codex rerun sampled the first eight hits per focal tier and all sampled `eax` values were `0x80000000`; this proves the sentinel path occurs under the tested conditions, not the full distribution. |
| `0x36cde0` returns `sqrt(xmm0*xmm1)` | STATIC CONFIRMED, RUNTIME PARTIAL | Already consistent with current evidence. The 2026-06-04 rerun captured live `xmm0`, `xmm1`, product, and square-root packets at `0x36e511`; multi-threaded sampling prevents treating row order as a complete per-candidate trace. |
| `0x36a938` reciprocal normalizer | STATIC CONFIRMED, RUNTIME PARTIAL | The instruction is real. The 2026-06-04 first-eight sample set saw `xmm2_low == 0.200000003` for all four focal tiers, predicting reciprocal about `5.0`. This is a sampled denominator, not yet a full `sum(score)` census. |
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

## Opus Internal Tension Noted

Some Opus packets contain both "four-zoom OBSERVED" banners and older body
sections that still say "static only" or "runtime owed." Codex should not admit
packet-level status. Each finding must be split into atomic static or runtime
claims and validated separately.

## Next Validation Steps

1. Create a later-instruction runtime probe at the `0x3661b0` vector-count use
   site (`0x366a50..0x366a61`) instead of trying to infer closure counts from
   the `0x3661b0` entry packet.
2. Reproduce or refute Opus's LLDB ignore-count / conditional-breakpoint method
   for mid-render score and `Σscore` magnitudes.
3. Probe non-sentinel `0x36930f` packets, or prove a scope-bound condition under
   which the first-eight sample window is expected to be all sentinel.
4. Only after successful Codex-owned runtime reproduction, write an evidence
   bundle under `docs/evidence/` and then consider canonical ledger changes.

## Non-Claims

- This audit does not prove Lumen-quality merge parity.
- This audit does not prove a clean-room implementation specification.
- This audit does not admit Opus's pipeline synthesis as truth.
- This audit does not prove public semantic names for tuple fields, score
  fields, weight tables, or output channels.
- This audit does not close final anti-ghosting acceptance / rejection logic.
