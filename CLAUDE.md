# L16 Phoenix Investigation — Session Handoff

**Repo:** github.com/ryaker/phoenix-l16-investigation (CC0-1.0, public)
**Canonical truth:** `docs/TRUTH.md` (check `Version:` in frontmatter — currently v2)

## Read FIRST every session

1. `docs/TRUTH.md` — git-versioned canonical truth. No date in filename.
2. `/tmp/l16_open_audit/_FINDINGS.md` — 2026-04-20 OPEN-items audit register (841 lines, 17 items, verdict per item)
3. `~/.claude/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/memory/open_items_plan.md` — closure plan for remaining 4 non-resolved items

## Current state (2026-04-20 post-Session-1)

- **14 of 17 OPEN items RESOLVED** (#15 Q-DROPPED-CONSUMER closed 2026-04-20 via Session 1 LLDB)
- **3 PARTIAL** (non-blocking for bridge HDR 28mm spike): #06 Q12 ZOOM_CCM (70/150mm partial), #10 OPEN-DARKCURRENT (reconfirmed inactive on bridge HDR path — formula extraction deferred to non-HDR profile), #16 OPEN-SCOPE-VERIFY (150mm kernel untested)
- **0 TRULY OPEN.** **28mm bridge HDR spike is UNBLOCKED.**

**#15 closure summary:** HW read-watchpoints on 4 dropped-cam RIC L0 buffers (A2/A3/A4/A5) at 28mm bridge HDR captured 102,361 trips over 480s — 100% of unique trip PCs trace through IRAMP-family code. Dropped cams ARE consumed via IRAMP body's composite-anchor pre-fusion kernel at `libcp+0x2b3410` (4-way SIMD weighted blend, new VA). "Skip dropped-cam ISP" optimization REFUTED. Rich's D5 directive ("run ISP for all 16") now satisfied by positive evidence. Details: `/tmp/l16_open_audit/session1_findings.md`.

## Next action

28mm bridge HDR spike is UNBLOCKED — proceed to SPIKE (validation-only per Rich's rule). Remaining optional work (non-spike-blocking):
- **#16 70mm/150mm verification** — 2 LLDB sessions on L16_03434 + L16_02285. Gates 70/150mm spike only.
- **#10 formula extraction** — requires non-HDR render profile (DirectRenderer or DPC); outside bridge HDR scope.

See `~/.claude/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/memory/open_items_plan.md` for LLDB BP/watchpoint list.

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
| 35mm (Tier 0 crop) | L16_02951 | Unit B | `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri` |
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
- **Unit-bound vs universal:** Rich's corpus = 2 physical L16 units. Unit A = L16_02130+L16_03434; Unit B = L16_02951+L16_02285. Unit-bound until proven universal.

## Contamination guard

- `archive/` is pre-commit-hook-enforced frozen. Do NOT cite `archive/TRUTH-v1-*.md`, `archive/phoenix-pipeline-facts-*-DEPRECATED.md`, or `archive/stale_copies/*.md` as authoritative.
- `/Users/ryaker/Documents/Light_Work/docs/reverse_engineering/` 01..27 numbered docs = separate older research thread; often contradicts `docs/TRUTH.md`. Do NOT cite without cross-check.
- Scratch files at `/Volumes/Dev/lumen-phoenix-scratch/*.md` are OK to read when `docs/TRUTH.md` cites them by path.

## Audit artifacts (keep available across sessions)

- `/tmp/l16_audit_sweep.sh` — macOS-compatible parallel grep template (17 OPEN items, 216-md corpus)
- `/tmp/l16_open_audit/_FINDINGS.md` — per-item audit register
- `/tmp/l16_open_audit/NN_TOPIC.txt` — per-item grep dumps
