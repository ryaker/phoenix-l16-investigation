# L16 Phoenix Investigation — Session Handoff

**Repo:** github.com/ryaker/phoenix-l16-investigation (CC0-1.0, public)
**Canonical truth:** `docs/TRUTH.md` (check `Version:` in frontmatter — currently v3)

## Read FIRST every session

1. `docs/TRUTH.md` — git-versioned canonical truth. No date in filename.
2. `docs/canonical/CLAIM_LEDGER.md` — claim-level authority.
3. `docs/audits/README.md` — artifact custody boundary. Durable audit/probe evidence must not live in `/tmp` or `/private/tmp`.
4. `docs/canonical/PARITY_BLOCKERS.md` — the unknowns that still block clean-room parity.
5. `docs/canonical/WSJF_PRIORITY.md` — WSJF ranking + dependency-adjusted lane order for the blocker set.

> Authority order: if any doc disagrees with `docs/canonical/CLAIM_LEDGER.md`, **the ledger wins.**

## Current state (post-v3 ledger rebuild, last campaign 2026-05-27)

The earlier v2-era "16 of 17 OPEN items RESOLVED / spike UNBLOCKED" conclusion has been **superseded** by the
v3 ledger rebuild, which re-opened the merge mechanism as the real parity wall. Do not paraphrase claim
counts from here — read `docs/canonical/CLAIM_LEDGER.md` for the live `PROVEN/PARTIAL/OPEN/REFUTED` tally.

- **Active parity blockers** (`docs/canonical/PARITY_BLOCKERS.md`), WSJF dependency-adjusted order:
  1. `src1` / `src2` pre-fusion merge/reduction mechanism (`CLM-PREFUSION-002`) — **Lane A, start first.**
  2. Pair-grid producer calibration semantics / LRI origins — Lane B (parallel peer).
  3. Tele odd-camera routing / C6 (`0xf2720` route) — Lane C (most recently worked).
  4. Four-zoom merge topology closure — Lane E (integration/validation).
  5. Final merge acceptance / rejection logic — Lane D (broad deep-decode).
- **The spike is NOT unblocked.** "Spike is validation, not investigation" — it happens only after the
  blocking unknowns close in the ledger.

**Most recent campaign (Lane C / C6):** proved the key-`15` construct→clear mutation chain (cleared at
`0x3c90a5`), censused all 58 direct `call 0xf2720` sites with tele runtime coverage, and ran a grid of
negative data-watchpoints showing the zero-filled ImagePyramid/geometry route is inert under four-zoom
bridge HDR. Remaining C6 work: untested-field/alias proof, final effect of watched `+0x60..+0x67` reads,
alternate-route proof, or terminal-filter proof. See `docs/evidence/lldb_c6_*` and `bundle_*` docs.

### Superseded historical note (retained for provenance only)

The v2-era Sessions 1–3 (28mm/70mm/150mm bridge HDR, composite-anchor kernel `libcp+0x2b3410`, the
"#15/#16/#06" OPEN-item numbering, and the "proceed to SPIKE" conclusion) predate the v3 ledger. They are
preserved in git history and in `docs/canonical/TRUTH_RECONCILIATION.md`; they are **not** current state.

## Instrumentation gotcha (revised v2.1.3)

BP at `libcp+0x2b3410` (composite-anchor kernel) DOES work for hit-counting — captured 1.7M hits at 70mm and 1.5M at 150mm before SIGABRT killed the render. LLDB retains BP counters past target termination, so the quit-script still prints counts. **Earlier v2.1.2 claim "BP crashes render" was a verify-before-trust failure** — I declared impossibility from incomplete log-tail polling without checking the `HIT COUNTS` line at the very end.

Takeaway: BP-based hit-counting on hot Halide-JIT kernels (1-2M hits/render) works for counts but not for producing completed output. If a render needs to complete AND be instrumented, use HW read-watchpoints on data (Session 1 approach). If only a hit count is needed, BP auto-continue is fine — SIGABRT-mid-render is acceptable if the quit script executes after.

At 150mm, BPs elsewhere (e.g. S2's proven 70mm probe re-run against 150mm) still trigger `EXC_BAD_ACCESS` at `libcp+0x2e945d`. Per Rich (2026-04-20): "Lumen ships working 150mm renders — crash has to be ours." Our probes perturb thread timing in a way that surfaces a race; not a libcp bug.

## Next action

Work the WSJF-ranked parity blockers in `docs/canonical/WSJF_PRIORITY.md`, dependency-adjusted order:
start **Lane A (`src1`/`src2` pre-fusion reducer, `CLM-PREFUSION-002`)** first; run Lane B (pair-grid
calibration / LRI origins) as a parallel peer; Lane C (C6) can continue but its final closure may depend on
Lane A. Hold Lane E (four-zoom topology) as the integration/validation lane. The spike does **not** start
until the blocking unknowns close in the ledger.

Each probe is committed under `docs/evidence/` as a `bundle_*` / `lldb_*` writeup with its `.lldb` script +
`.py` probe + `run_*.sh`. Never strengthen a `PARTIAL`/`OPEN` ledger claim in downstream prose.

## Binaries + LRIs — VERIFIED PATHS (re-verified 2026-05-29)

Every session needs these. They are NOT in `docs/TRUTH.md` (TRUTH has VAs only, not filesystem paths).

**Binaries (all Mach-O x86_64 — must invoke under `arch -x86_64`, this Mac is Apple Silicon):**

| What | Path |
|---|---|
| `lri_process` binary | `/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process` |
| `libcp.dylib` (all VAs in TRUTH reference this) | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |
| Lumen.app (DYLD_FRAMEWORK_PATH root — has libceres etc.) | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app` |

⚠ **Stale paths in tooling:** `tools/probe_symbol_bp.py`, `tools/probe_wb_hit.py`, `tools/run_ics_70mm.lldb` all hardcode `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process` (top-level, doesn't exist) and `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/...` (doesn't exist). Patch or override via args before running.

**LRIs (all paths have a space in `Base Photos` — always quote):**

| Zoom tier | LRI | Unit | Path |
|---|---|---|---|
| 28mm (Tier 0 anchor) | L16_02130 | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| 35mm (Tier 0 crop) | L16_03041 | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` (corrected seed — old `L16_02951` was a 98mm tele sample; see `docs/evidence/lri_35mm_seed_correction_true35_runtime.md`) |
| 70mm (Tier 1 anchor) | L16_03434 | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` (178 MB) |
| 150mm (Tier 1 crop) | L16_02285 | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

**Invocation template (LLDB session):**
```bash
arch -x86_64 lldb -s /path/to/script.lldb \
  /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
# Inside script: set DYLD_FRAMEWORK_PATH + DYLD_LIBRARY_PATH env before run,
# then: process launch -- --profile 3 "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
```

**Caveats:**
- Volume `/Volumes/Base Photos/` is external — confirm mounted before running: `ls "/Volumes/Base Photos/"`
- `lri_process` CLI `--export-fmt 4` writes JPEGs with `.dng` extension (per `docs/LIBRARY_INVENTORY.md:95`). For real DNG ground truth use `Renderer::writeImage(..., DNG, ...)` path, not CLI.
- All VAs in TRUTH are against this specific libcp.dylib (6.93 MB, x86_64). If the dylib is ever swapped/rebuilt, VAs re-verify required.

## Discipline rules (Rich's verbatim)

- **"Spike doesn't happen till we know and have confirmed everything needed. Spike is not invetigatory it is validation."** (2026-04-20)
- **"Do parallel grep sweeps, dump to files, you later analyze."** (2026-04-20)
- **Round 4 Precision Rule:** paraphrases that "sound like absolutes" must be scope-bound. 0-hits-under-tested-conditions ≠ "NEVER FIRES".
- **Unit-bound vs universal:** Rich's corpus = 2 physical L16 units. Unit A = L16_02130+L16_03434; Unit B = L16_03041+L16_02285. Unit-bound until proven universal.
- **No guesses as facts (2026-05-30):** a fact needs a machine-deterministic check (byte-search /
  reproducible script) or a runtime observation. LLM-read disassembly is NOT fact until independently
  re-extracted. Unproven-but-plausible findings are tracked as first-class hypotheses in
  `docs/hypotheses/` (committed, with provenance + proof/disproof plan); no doc outside that folder may
  cite a hypothesis as fact, and hypotheses carry no ledger status. See `docs/hypotheses/README.md`.

## Contamination guard

- `archive/` is pre-commit-hook-enforced frozen. Do NOT cite `archive/TRUTH-v1-*.md`, `archive/phoenix-pipeline-facts-*-DEPRECATED.md`, or `archive/stale_copies/*.md` as authoritative.
- `/Users/ryaker/Documents/Light_Work/docs/reverse_engineering/` 01..27 numbered docs = separate older research thread; often contradicts `docs/TRUTH.md`. Do NOT cite without cross-check.
- Scratch files at `/Volumes/Dev/lumen-phoenix-scratch/*.md` are OK to read when `docs/TRUTH.md` cites them by path.

## Audit artifact custody

- Durable audit registers belong in `docs/audits/`.
- Reusable probe harnesses belong in `tools/lldb_probes/`.
- Rerunnable raw outputs belong in ignored `runs/<topic>/`.
- `/tmp` and `/private/tmp` may be used only as one-command OS scratch. Do not cite them as live evidence dependencies in handoffs, canonical docs, or specs.
