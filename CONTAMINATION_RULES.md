# Contamination Rules — Paths that look authoritative but aren't

## How contamination happened (2026-04-20)

Three identical copies of `phoenix-pipeline-facts.md` existed across this tree. The top-level file was a 760-byte deprecation pointer; the two sub-folder copies held the OLD April-13 content with no deprecation marker. A `find` or `Read` by the short name returned three paths, all looking valid. An agent resuming from a conversation summary read the sub-folder copy as authoritative and made code changes that contradicted the verified April-17 truth doc.

The same pattern exists with `Documents/Light_Work/docs/reverse_engineering/` (44 numbered docs from a separate older research thread) and older POC code at `/Volumes/Dev/Light_Spike/`.

## DO NOT read as authoritative

### Inside this repo

| Path | Status | Why |
|------|--------|-----|
| `archive/**` | frozen | Deprecated. Read-only. Pre-commit hook rejects writes. |
| `phoenix-pipeline-facts.md` (top-level) | pointer | 760-byte pointer; actual content is `docs/TRUTH.md`. |
| `lumen-phoenix-current-state.md` (top-level) | pointer | 822-byte pointer; actual content is `docs/TRUTH.md`. |
| `phoenix-handoff/phoenix-pipeline-facts.md` | MOVED to archive | Was a stale April-13 copy. Now in `archive/stale_copies/`. |
| `phoenix-spec-writing/phoenix-pipeline-facts.md` | MOVED to archive | Was a stale April-13 copy. Now in `archive/stale_copies/`. |

### Outside this repo

| Path | Status | Why |
|------|--------|-----|
| `/Users/ryaker/Documents/Light_Work/docs/reverse_engineering/` (44 .md) | separate thread | Older research thread, NOT integrated into TRUTH.md. Contradicts it in places (e.g., doc 23 says "awb_mode=0 → mode 2 D65 directly" but TRUTH says CCM blends A↔D65 per-tile inside IRAMP at 0xbf4a0). |
| `/Volumes/Dev/Light_Spike/` | old POC | Pre-IRAMP architecture; step1-6_*.py + lumen-phoenix-poc-spec.md are based on architectural models refuted by TRUTH. |
| `/Users/ryaker/Library/Mobile Documents/com~apple~CloudDocs/L16_review_2026-04-09/FLOW_REFINED/` | old merge outputs | Pre-IRAMP homography merge attempts. Informational only. |

## DO read as authoritative

| Path | Purpose |
|------|---------|
| `docs/TRUTH.md` | THE truth. Read first. Dated canonical version at `docs/phoenix-truth-<LATEST-DATE>.md`. |
| `docs/LIBRARY_INVENTORY.md` | 411-symbol libcp API, no refutations. |

## Evidence sources (read only when TRUTH.md cites them by path)

| Path | Purpose |
|------|---------|
| `/Volumes/Dev/lumen-phoenix-scratch/*.md` | 100+ agent reports cited by TRUTH.md (iramp_*.md, blc_*.md, ccm_*.md, composite_anchor_n1_reducer.md, session{2,3,4,5,6}_*.md, legacy_doc_audit{,_round2}.md, etc.). |
| `phoenix-handoff/investigation_traceability/*.md` | 23 session reports (still on-repo for now; may move to evidence/). |

## Historical (for learning what was verified/superseded)

| Path | Purpose |
|------|---------|
| `~/.claude/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/*.jsonl` | 282 MB of Claude Code transcripts. Contains agent reports + LLDB output that the scratch .md summarized. |
| `archive/**` | Frozen old docs. Audit trail only. |

## Contamination-detection checklist

Before treating any doc as authoritative:

1. Is its path inside `docs/`? If no → suspect.
2. Is it cited by `docs/TRUTH.md`? If no → suspect.
3. Is the file date newer than `docs/phoenix-truth-<LATEST-DATE>.md`? If no → stale until proven otherwise.
4. Does the top-of-file frontmatter say DEPRECATED, REFUTED, or point to another doc? If yes → do not use its claims.
5. Is it in `archive/`? If yes → read only to understand history, never for current facts.

## Fix tracking

This repo was initialized to prevent future contamination. The git history starting 2026-04-20 shows every move and can be used to trace "when did claim X become/stop being authoritative."
