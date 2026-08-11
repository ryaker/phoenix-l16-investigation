# Research Protocol — evidence-first, or you re-derive Codex's work

This project has 500+ evidence files, ~50 probe scripts, a claim ledger, a
library inventory, and full disassembly dumps. Grepping a few files by hand is
NOT sufficient to know whether something is already reverse-engineered — the
answer is routinely buried in a probe docstring or the inventory. Re-discovering
already-documented facts has wasted large amounts of time and usage.

## The hard gate (mandatory, no exceptions)

Before ordering OR doing ANY reverse-engineering / LLDB investigation of a
target — an address (`0x…`), an `lt::Type`, or a topic — you MUST first run:

```
tools/whatknown.sh <target>
```

It searches ALL artifacts at once (probe scripts incl. docstrings + address
constants, evidence bundles, ledger, blockers, LIBRARY_INVENTORY, TRUTH, spec,
and the disasm symbol map) and prints a verdict:

- **DOCUMENTED (N artifact groups)** → the target is already known. READ and
  CONNECT the cited artifacts. Do NOT launch an investigation. If a formula is
  proven elsewhere, cite the claim and wire it — do not re-derive it.
- **NO HITS** → genuinely undocumented. This is a real unknown; investigation is
  justified. This is the ONLY case in which you spend probe/RE effort.

Paste the `whatknown` verdict into your reasoning/handoff before proceeding. If
you launch a subagent for investigation, its FIRST required step is to run
`whatknown` on every target and report the verdict; an investigation subagent
that skips this is doing it wrong.

## Distinguish the two kinds of "not done yet"

- **Porting gap** — the formula IS proven (whatknown = DOCUMENTED); Phoenix just
  implements it approximately or not at all. Fix by reading the proven formula
  and porting it exactly. No new RE, no comparison.
- **Genuine unknown** — whatknown = NO HITS across all artifacts. Only these
  deserve reverse-engineering.

Spending RE effort on a porting gap (because you didn't run whatknown) is the
failure this protocol exists to prevent.

## When you DO close a genuine unknown

Write the result into an evidence bundle AND add the address/type to the record
so `whatknown` finds it next time. Move the item from `PARITY_BLOCKERS.md` per
its exit criteria. The drawdown only converges if closed items stop being
re-investigated.
