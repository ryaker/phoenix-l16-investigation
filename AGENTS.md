# L16 Phoenix Investigation — Session Handoff

**Repo:** github.com/ryaker/phoenix-l16-investigation (CC0-1.0, public)
**Canonical truth:** `docs/TRUTH.md` (check `Version:` in frontmatter — currently v3)

## Read FIRST every session

1. `docs/TRUTH.md` — git-versioned canonical truth. No date in filename.
2. `docs/canonical/CLAIM_LEDGER.md` — claim-level authority.
3. `docs/audits/README.md` — artifact custody boundary. Durable audit/probe evidence must not live in `/tmp` or `/private/tmp`.
4. `~/.Codex/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/memory/open_items_plan.md` — historical closure plan; use only after checking current canonical blockers.

## Current state (2026-04-20 post-Sessions-1+2+3)

- **16 of 17 OPEN items RESOLVED.** Sessions 1+2+3 closed #15, #06 Q12, and #16 on 2026-04-20. Doc-hygiene v2.1.1 closed #17.
- **1 PARTIAL** (non-blocking): #10 OPEN-DARKCURRENT — reconfirmed inactive on bridge HDR; formula extraction deferred to non-HDR profile.
- **0 TRULY OPEN.** **28mm + 70mm + 150mm bridge HDR spikes all architecturally UNBLOCKED.**

**Session closure summary:**
- **Session 1 (28mm L16_02130):** HW read-watchpoints on 4 dropped-cam RIC L0 buffers captured 102K trips; 100% IRAMP-family. New VA found: composite-anchor kernel at `libcp+0x2b3410` (4-way SIMD weighted blend). Closes #15.
- **Session 2 (70mm L16_03434):** Full Phase 1 clean render. Dispatcher cam_ids `[8,10..14]`=B4+C1..C5 match TRUTH M4. CCMInterp 12 hits with 3 distinct dest-rdis (vs 28mm's 1). All 4 #16 kernels fire consistently with 28mm. Closes #06/70mm + #16/70mm.
- **Session 3 (150mm L16_02285):** Partial Phase 1 (render crashed at `libcp+0x2e945d` under instrumentation — Rich verdict: crash is ours, Lumen.app ships working 150mm). Pre-crash data captured dispatcher cam_ids + IRAMP body first-hits matching 70mm exactly — confirms 150mm takes 70mm tier via `outer_enum=1`. Closes #16/150mm architecturally.
- **Doc-hygiene:** 12 load-bearing scratch files + external tech-doc cited in TRUTH v2.1.1. Closes #17.

## Instrumentation gotcha (revised v2.1.3)

BP at `libcp+0x2b3410` (composite-anchor kernel) DOES work for hit-counting — captured 1.7M hits at 70mm and 1.5M at 150mm before SIGABRT killed the render. LLDB retains BP counters past target termination, so the quit-script still prints counts. **Earlier v2.1.2 claim "BP crashes render" was a verify-before-trust failure** — I declared impossibility from incomplete log-tail polling without checking the `HIT COUNTS` line at the very end.

Takeaway: BP-based hit-counting on hot Halide-JIT kernels (1-2M hits/render) works for counts but not for producing completed output. If a render needs to complete AND be instrumented, use HW read-watchpoints on data (Session 1 approach). If only a hit count is needed, BP auto-continue is fine — SIGABRT-mid-render is acceptable if the quit script executes after.

At 150mm, BPs elsewhere (e.g. S2's proven 70mm probe re-run against 150mm) still trigger `EXC_BAD_ACCESS` at `libcp+0x2e945d`. Per Rich (2026-04-20): "Lumen ships working 150mm renders — crash has to be ours." Our probes perturb thread timing in a way that surfaces a race; not a libcp bug.

## Next action

All bridge HDR spikes architecturally UNBLOCKED. Per Rich's rule ("spike is validation, not investigation"), proceed to SPIKE.
- **#10 formula extraction** — optional future work, requires non-HDR render profile (DirectRenderer or DPC); outside bridge HDR scope.
- **#15 cross-zoom HW-watchpoint confirmation** — optional non-blocking future work: re-run Session 1's watchpoint script against 70mm/150mm dropped-cam buffers to directly observe 0x2b3410 at those tiers (infeasible via BP).

See `~/.Codex/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/memory/open_items_plan.md` for LLDB BP/watchpoint list.

## Binaries + LRIs — VERIFIED PATHS (2026-04-20)

Every session needs these. They are NOT in `docs/TRUTH.md` (TRUTH has VAs only, not filesystem paths). Verified Mach-O + file existence on this machine on 2026-04-20.

**Binaries (all Mach-O x86_64 — must invoke under `arch -x86_64`, this Mac is Apple Silicon):**

| What | Path |
|---|---|
| `lri_process` binary | `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process` |
| `libcp.dylib` (all VAs in TRUTH reference this) | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |
| Lumen.app (DYLD_FRAMEWORK_PATH root — has libceres etc.) | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app` |

⚠ **Stale paths in tooling:** `tools/probe_symbol_bp.py`, `tools/probe_wb_hit.py`, `tools/run_ics_70mm.lldb` all hardcode `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process` (top-level, doesn't exist) and `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/...` (doesn't exist). Patch or override via args before running.

**LRIs (all paths have a space in `Base Photos` — always quote):**

| Zoom tier | LRI | Unit | Path |
|---|---|---|---|
| 28mm (Tier 0 anchor) | L16_02130 | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| 35mm (Tier 0 crop) | L16_03041 | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| 70mm (Tier 1 anchor) | L16_03434 | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` (178 MB) |
| 150mm (Tier 1 crop) | L16_02285 | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

**Invocation template (LLDB session):**
```bash
arch -x86_64 lldb -s /path/to/script.lldb \
  /Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
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

## Contamination guard

- `archive/` is pre-commit-hook-enforced frozen. Do NOT cite `archive/TRUTH-v1-*.md`, `archive/phoenix-pipeline-facts-*-DEPRECATED.md`, or `archive/stale_copies/*.md` as authoritative.
- `/Users/ryaker/Documents/Light_Work/docs/reverse_engineering/` 01..27 numbered docs = separate older research thread; often contradicts `docs/TRUTH.md`. Do NOT cite without cross-check.
- Scratch files at `/Volumes/Dev/lumen-phoenix-scratch/*.md` are OK to read when `docs/TRUTH.md` cites them by path.

## Audit artifact custody

- Durable audit registers belong in `docs/audits/`.
- Reusable probe harnesses belong in `tools/lldb_probes/`.
- Rerunnable raw outputs belong in ignored `runs/<topic>/`.
- `/tmp` and `/private/tmp` may be used only as one-command OS scratch. Do not cite them as live evidence dependencies in handoffs, canonical docs, or specs.
