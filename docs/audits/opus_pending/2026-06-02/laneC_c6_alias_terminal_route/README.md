# Lane C — C6 alias / terminal-filter / alternate-route (STATIC research packet)

**status: NEEDS_CODEX_VALIDATION**
**method: STATIC ONLY** (`otool -arch x86_64 -tV`; no render, no runtime breakpoints).
**agent: opus-quarantine — NO authority over truth.** Weak language only.
**created: 2026-06-02**

binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
sha256: `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

anchorPassed: **true** (0x3eced0 is the enclosing function; mulps->maxps->sqrtps triple at 0x3ecfe4+ inside it).

## What this packet covers
All three remaining Lane C / C6 open angles, STATIC, bounded:

- **ANGLE 1 (alias/untested-field) — CANDIDATE.** The C6 item constructor `0xf2770` writes NO fields in
  the briefing's +0x68..0xa0 band. Non-covered *defined* fields = 0x38,0x40,0x44,0x48,0x4c,0x4d,0x50,
  0x54,0x104,0x108,0xd8..0xfc; first-class getters exist for +0x4c/+0x4d/+0x100. A blind binary-wide
  +0x68..0xa0 read list (145 VAs) is included but is a cross-struct superset, NOT C6-attributed.

- **ANGLE 2 (terminal-filter) — LEAD.** Only ONE literal `cmpl $0xf` key==15 test via the `0xf2720`
  getter exists (the clear at 0x3c909d). The two fully-traced C6 selection paths (0x1a8df0 family) ARE
  +0x30-gated and skip a cleared item. BUT the camera-group-type classifier `0xf6c60` is +0x30-BLIND
  and operates on the key value (which the clear leaves == 15). No fully-traced non-skipping image path
  confirmed; guard-domination over all 58 callers is the open item.

- **ANGLE 3 (alternate route) — no static route confirmed.** Key VALUE 15 survives the +0x30 clear and
  classifies as camera-group-type 2 (`0xf6c60`: mask 0xfc00 covers bits 10..15). The key feeds
  list-search predicates and group-type key-collection lists, but no `call 0xf2720`-independent path
  carrying a key-15-derived POINTER into an image kernel was found under this search.

## Files
- `manifest.json` — lane, sha256, anchor, re-confirmed C6 anchors.
- `commands.txt` — every command, reproducible.
- `observations.md` — VERBATIM disasm excerpts + log paths, scope-bound, per angle.
- `non_claims.md` — explicit limits (8 items).
- `proof_or_disproof_plan.md` — Codex closure plan (runtime allowed for Codex only).
- raw logs: `runs/laneC_c6_alias_terminal_route/*.log`
- full dump: `runs/laneC_c6_alias_terminal_route/full_disasm.txt`
- probe: `tools/lldb_probes/opus_pending/laneC_c6_alias_terminal_route/static_recheck.sh`

## Load-bearing single fact
`0x3c90a5 = movb $0x0, 0x30(%rax)` clears item+0x30 ONLY; item+0x60 (the key, read by `0xf2720`) is
untouched, so the key remains 15 and the +0x30-blind classifier `0xf6c60` still maps it to group-type 2
after the clear. Whether that surviving classification reaches pixels is UNRESOLVED here.
