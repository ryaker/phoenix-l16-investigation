# findings_for_codex — Tier 1 (graduated, four-zoom-upgraded)

This directory is **EMPTY by default** and fills slowly. A packet appears here ONLY after it has passed the
four-zoom upgrade playbook and is therefore eligible to be shared as a finding for Codex's validation.

## Why this tier exists (Rich, 2026-06-03)
The work under `docs/audits/opus_pending/2026-06-02/` (Tier 0 / staging / "quarantine²") is raw RE — mostly
STATIC disasm or SINGLE-ZOOM runtime. That is **not finding-grade**: handing it to Codex as "findings" would
make him *discover* my corner-cutting rather than *confirm* validated work. So nothing in staging is a finding
until I upgrade it myself.

## Graduation gate (the four-zoom playbook) — ALL steps required
A staging packet graduates into this directory only after:
1. **Load-bearing claims enumerated** (each VA / constant / mechanism the packet asserts).
2. **Four-zoom runtime data captured** — 28mm L16_02130 / 35mm L16_03041 / 70mm L16_03434 / 150mm L16_02285
   (all Unit-1): at each claim's breakpoint/site, read the actual per-tier operands (values, camera sets,
   contributor counts, params) — NOT just hit-counts. (LRI-only claims: re-parse ALL FOUR LRIs, not a subset.)
3. **Per-tier verified** — the claim holds (or is scope-bound / corrected) at every tier it's asserted for.
4. **Packet rewritten** to four-zoom OBSERVED with explicit per-tier data + scope; tool limits (Rosetta
   read-watchpoints dead) stated per-datum, never used to downgrade the whole finding.
5. **`git mv`** staging → here, and the REMEDIATION_LEDGER row flipped to GRADUATED.

Still `NEEDS_CODEX_VALIDATION` even here — Codex validates/upgrades to ledger truth. This tier only means
"done to the rigor that makes it worth his time."
