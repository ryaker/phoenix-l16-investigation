# Hypotheses Zone

This directory is the home for **tracked but unproven findings** — "sister facts."

A hypothesis is a real, plausible finding that is **not yet machine-verified or runtime-confirmed**. It is
kept here so it is **not lost and not unknown**: the idea, its provenance, and the exact work needed to
prove or disprove it stay visible and version-controlled — without ever masquerading as fact.

## The Rule (non-negotiable)

- **No document outside `docs/hypotheses/` may cite a hypothesis as fact.** Canonical docs
  (`docs/canonical/*`), evidence docs (`docs/evidence/*`), `docs/TRUTH.md`, and the claim ledger may
  reference a hypothesis's **existence and proof plan**, but may never restate its content as established.
- A hypothesis carries **no claim status** in the ledger. It is not `PARTIAL`, not `OPEN-with-evidence`.
  It is a candidate awaiting proof.
- Promotion to fact happens **only** in a `docs/evidence/` proof doc backed by a machine-deterministic
  check or a runtime observation. When that happens, update the hypothesis status to `PROMOTED` with a
  pointer to the proof doc.
- **Four-zoom rule.** For any merge-critical / pipeline-behavior claim, promotion requires explicit
  coverage at **28mm, 35mm, 70mm, AND 150mm** (per the claim ledger). A result observed at fewer focal
  lengths is **scope-bound to those focal lengths** and may NOT be promoted or generalized — assume
  nothing about cross-zoom behavior; observe it. (Exception: a fact that is purely a property of the
  binary's bytes — e.g. a constant's value or storage offset — is zoom-independent and needs only one
  machine-deterministic check; but any claim about how/whether that code *runs* still needs four zooms.)
- Disproof is recorded here as `REFUTED` with the disproving evidence. Refuted hypotheses are **kept**
  (not deleted) so the same wrong lead is not re-investigated.

## Status Vocabulary

- `HYPOTHESIS` — default. Plausible, sourced, unproven. Uncitable as fact.
- `PROMOTED` — proven; now a fact in a named `docs/evidence/` doc (link it). Body kept for history.
- `REFUTED` — disproven; disproof recorded. Kept as a do-not-repeat marker.

## What Every Hypothesis Doc Must Contain

1. **Statement** — the precise claim, with VAs/values.
2. **Provenance** — exactly how it was produced (e.g. which workflow/agent), and the reliability caveat
   (LLM-read disasm? agent glitch? single tool?).
3. **Why it is not yet fact** — the specific verification gap.
4. **Proof plan** — the exact experiment that would make it fact (command/probe/render).
5. **Disproof criteria** — what observation would refute it.

## Naming

`HYP-<claim-id-or-lane>-<topic>.md` (e.g. `HYP-PREFUSION-002-2f8040-normalizer.md`).

## Relationship To Other Zones

- `docs/evidence/` = proven (machine-verified or runtime-observed) facts. **Citable.**
- `docs/hypotheses/` = unproven sister facts. **Not citable as fact.**
- `docs/quarantine/` = explicitly-quarantined contradictions / superseded claims. Reference-only.
