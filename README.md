# L16 Phoenix Reverse-Engineering Repo

## ONE rule for all agents and humans

**Read `docs/TRUTH.md` first. Do not treat any other doc as authoritative unless `docs/TRUTH.md` cites it.**

See `READING_PROTOCOL.md` for the full reading order and `CONTAMINATION_RULES.md` for the list of paths that look authoritative but are stale/deprecated.

## Layout

```
docs/          Canonical truth doc + stable references. Read-first.
evidence/      Pointer to /Volumes/Dev/lumen-phoenix-scratch/ (100+ agent reports cited by TRUTH).
archive/       Deprecated docs + stale copies. FROZEN — never edit, never re-read as authoritative.
spike/         Throwaway validation code (phoenix_pipeline.py + diagnostics). NOT Phoenix itself.
tools/         Probe scripts, LLDB helpers, disassembly references.
hooks/         Git pre-commit enforcement.
```

## Before writing any code

1. Read `docs/TRUTH.md` end-to-end.
2. Re-check dates. If a newer `docs/phoenix-truth-<LATER-DATE>.md` exists, read that instead.
3. Only run spike code if the investigation in `docs/TRUTH.md` is end-to-end verified (no open questions in the area being tested).
4. Spike outputs (MAD, per-region deltas) are validation evidence — they NEVER feed back into `docs/TRUTH.md`. Contamination rule.

## Spike-the-doc-not-Phoenix pattern

Spike = throwaway validation Python that exercises the TRUTH doc end-to-end. If spike output is bad, the conclusion is "either the spike has a bug OR a finding in TRUTH is wrong — investigate which." Never "edit TRUTH to match what the spike produced."

## Repo history

Initialized 2026-04-20 after a session where stale sub-folder copies of `phoenix-pipeline-facts.md` were read as authoritative, leading to code changes that contradicted verified runtime behavior. The repo exists to make such contamination structurally impossible.
