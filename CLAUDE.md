# L16 Phoenix Investigation — Session Handoff

**Repo:** github.com/ryaker/phoenix-l16-investigation (CC0-1.0, public)
**Canonical truth:** `docs/TRUTH.md` (check `Version:` in frontmatter — currently **v3.x**, ledger-backed)

> Authority order: if any doc disagrees with `docs/canonical/CLAIM_LEDGER.md`, **the ledger wins.**
> `docs/TRUTH.md` may only summarize claims already admitted into the ledger.

## Read FIRST every session

1. `docs/TRUTH.md` — human-readable root summary (git-versioned, no date in filename).
2. `docs/canonical/CLAIM_LEDGER.md` — **claim-level authority.** Status vocabulary + per-zoom validation + readiness.
3. `docs/canonical/PARITY_BLOCKERS.md` — the unknowns that still block clean-room parity.
4. `docs/canonical/WSJF_PRIORITY.md` — WSJF ranking + dependency-adjusted lane order for the blocker set.
5. `docs/canonical/MERGE_CRITICAL_TRUTH.md` — merge-critical subset.
6. `docs/audits/README.md` — artifact custody boundary (durable evidence must NOT live in `/tmp`).

## Current state (post-v3 ledger rebuild, last campaign 2026-05-27)

The earlier v2-era "16 of 17 OPEN items RESOLVED / spike UNBLOCKED / proceed to SPIKE" conclusion has been
**superseded** by the v3 ledger rebuild. The merge mechanism was re-opened as the real parity wall.

- **Claim ledger (authority) status:** a mix of `PROVEN`, `PARTIAL`, `OPEN`, and `REFUTED` claims —
  read `docs/canonical/CLAIM_LEDGER.md` for the live tally; do not paraphrase it from here.
- **Active parity blockers** (`docs/canonical/PARITY_BLOCKERS.md`), WSJF-ordered for execution:
  1. `src1` / `src2` pre-fusion merge/reduction mechanism (`CLM-PREFUSION-002`) — **Lane A, start first.**
  2. Pair-grid producer calibration semantics / LRI origins — Lane B (parallel peer).
  3. Tele odd-camera routing / C6 (`0xf2720` route) — Lane C (most recently worked).
  4. Four-zoom merge topology closure — Lane E (integration/validation).
  5. Final merge acceptance / rejection logic — Lane D (broad deep-decode).
- **The spike is NOT unblocked.** Rich's rule stands: "Spike is validation, not investigation" — it happens
  only after the blocking unknowns close in the ledger.

**Most recent campaign (Lane C / C6):** proved the key-`15` construct→clear mutation chain (cleared at
`0x3c90a5`), censused all 58 direct `call 0xf2720` sites with tele runtime coverage, and ran a grid of
negative data-watchpoints showing the zero-filled ImagePyramid/geometry route is inert under four-zoom
bridge HDR. Remaining C6 work: untested-field/alias proof, final effect of watched `+0x60..+0x67` reads,
alternate-route proof, or terminal-filter proof. See `docs/evidence/lldb_c6_*` and `bundle_*` docs.

## Evidence custody (enforced)

- Durable audit registers → `docs/audits/`.
- Proof / probe writeups → `docs/evidence/` (121 tracked `bundle_*` / `lldb_*` docs; each probe ships its
  `.lldb` script + `.py` probe + `run_*.sh` where applicable).
- Reusable probe harnesses → `tools/lldb_probes/`.
- Rerunnable raw outputs → ignored `runs/<topic>/`.
- `/tmp` and `/private/tmp` are one-command OS scratch only — **never** cite them as live evidence in
  handoffs, canonical docs, or specs.

## Binaries + LRIs — VERIFIED PATHS (re-verified 2026-05-29)

All VAs in the ledger/TRUTH reference the specific `libcp.dylib` below. Re-verify VAs if it is ever swapped.

**Binaries (all Mach-O x86_64 — invoke under `arch -x86_64`; this Mac is Apple Silicon):**

| What | Path |
|---|---|
| `lri_process` binary | `/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process` |
| `libcp.dylib` | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |
| Lumen.app (DYLD_FRAMEWORK_PATH root) | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app` |

⚠ **Stale paths in older tooling:** some scripts under `tools/` hardcode a top-level `lri_process` and a
`Lumen/Lumen.app` path that do not exist. Patch or override via args before running; verify with `ls`/`file`.

**LRIs — canonical four-zoom corpus (all paths have a space in `Base Photos` — always quote):**

| Zoom tier | LRI | Unit | Path |
|---|---|---|---|
| 28mm (Tier 0 anchor) | L16_02130 | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| 35mm (Tier 0 crop) | L16_03041 | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| 70mm (Tier 1 anchor) | L16_03434 | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` (178 MB) |
| 150mm (Tier 1 crop) | L16_02285 | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

> **35mm seed correction:** the old seed `L16_02951.lri` (2018-12-19) was filename/date-chosen and is NOT a
> true 35mm bridge-tier capture. It was superseded by `L16_03041.lri`. See
> `docs/evidence/lri_35mm_seed_correction_true35_runtime.md`.

**Invocation template (LLDB session):**
```bash
arch -x86_64 lldb -s /path/to/script.lldb \
  /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
# Inside script: set DYLD_FRAMEWORK_PATH + DYLD_LIBRARY_PATH env before run,
# then: process launch -- --profile 3 "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
```

**Caveats:**
- `/Volumes/Base Photos/` is external — confirm mounted first: `ls "/Volumes/Base Photos/"`.
- `lri_process` CLI `--export-fmt 4` writes JPEGs with `.dng` extension (per `docs/LIBRARY_INVENTORY.md`).
  For real DNG ground truth use the `Renderer::writeImage(..., DNG, ...)` path, not the CLI.

## Discipline rules (Rich's verbatim)

- **"Spike doesn't happen till we know and have confirmed everything needed. Spike is not invetigatory it is validation."** (2026-04-20)
- **"Do parallel grep sweeps, dump to files, you later analyze."** (2026-04-20)
- **Round 4 Precision Rule:** paraphrases that "sound like absolutes" must be scope-bound. 0-hits-under-tested-conditions ≠ "NEVER FIRES".
- **Ledger discipline:** never silently strengthen a `PARTIAL`/`OPEN` claim to `PROVEN` in any downstream doc. `0 hits` keeps its tested scope.
- **Unit-bound vs universal (CORRECTED 2026-05-30 — see `docs/evidence/bundle_proof_two_unit_corpus_static.md`):** corpus = 2 physical L16 units, identified by per-file intrinsics calibration SHA-256: **Unit-1 `722a6e72…`** (5724 files), **Unit-2 `223961c6…`** (3484 files). Folders are organized by **shot date, not unit** — 13 date-folders mix both units, so unit identity comes from the per-file hash, never the folder. ⚠ The old "Unit A = L16_02130+L16_03434; Unit B = L16_03041+L16_02285" labeling is **REFUTED** — all four canonical seeds are **Unit-1**, so every "four-zoom verified" claim was tested on ONE body across four focals, NOT two bodies; universality is **unproven** until re-run on the Unit-2 same-name twins: 28mm `2018-07-04/L16_02130`, 35mm `2018-10-28/L16_03041`, 70mm `2020-07-14/L16_03434`, 150mm `2018-07-07/L16_02285`. (CA-vs-FL owner mapping unproven — GPS undecoded; see `docs/hypotheses/HYP-unit-ca-fl-assignment.md`.)

## Contamination guard

- `archive/` is pre-commit-hook-enforced frozen. Do NOT cite `archive/TRUTH-v1-*.md`, `archive/phoenix-pipeline-facts-*-DEPRECATED.md`, or `archive/stale_copies/*.md` as authoritative.
- `/Users/ryaker/Documents/Light_Work/docs/reverse_engineering/` 01..27 numbered docs = separate older research thread; often contradicts the ledger. Do NOT cite without cross-check.
- Scratch files at `/Volumes/Dev/lumen-phoenix-scratch/*.md` are OK to read when a canonical doc cites them by path.
- `docs/quarantine/` holds explicitly-quarantined contradictions — reference-only, never authority.

## Fact vs hypothesis discipline (Rich, 2026-05-30)

- **No guesses as facts.** A fact requires a machine-deterministic check (byte-search, reproducible
  script) or a runtime observation. LLM-read disassembly is NOT fact until independently re-extracted.
- Unproven-but-plausible findings are **first-class tracked hypotheses**, not deleted and not hidden:
  they live in `docs/hypotheses/` (committed), each with provenance + proof/disproof plan. See
  `docs/hypotheses/README.md`.
- **No doc outside `docs/hypotheses/` may cite a hypothesis as fact** until it is promoted via a
  `docs/evidence/` proof doc. Hypotheses carry no ledger status.
- Zones: `docs/evidence/` = proven/citable; `docs/hypotheses/` = unproven sister facts/not citable;
  `docs/quarantine/` = superseded/contradictions/reference-only.
