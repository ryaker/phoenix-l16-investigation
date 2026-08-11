#!/usr/bin/env bash
# whatknown.sh <address|type|keyword>  — MANDATORY evidence-first lookup.
#
# Run this BEFORE ordering or doing ANY reverse-engineering / LLDB investigation.
# It searches EVERY evidence artifact at once: probe scripts (docstrings + address
# constants), evidence bundles, the claim ledger, parity blockers, LIBRARY_INVENTORY,
# TRUTH, the parity spec, and the disassembly symbol map.
#
# RULE: if this returns ANY hit for your target, it is ALREADY documented ->
# READ and CONNECT it. Do NOT launch an investigation. Only targets that return
# NOTHING here are genuine unknowns worth new RE.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
q="${1:-}"
[[ -z "$q" ]] && { echo "usage: whatknown.sh <address(0x..)|lt::Type|keyword>"; exit 2; }

# hex address? build a case-insensitive with/without-0x, leading-zero-tolerant pattern
qn="$(printf '%s' "$q" | sed -E 's/^0[xX]//')"
if printf '%s' "$qn" | grep -qiE '^[0-9a-f]{3,}$'; then
  pat="0x0*${qn}([^0-9a-fA-F]|$)|(^|[^0-9a-fA-F])${qn}([^0-9a-fA-F]|$)"
else
  pat="$q"
fi

hits=0
show() { # $1=label $2..=paths
  local label="$1"; shift
  local out; out="$(grep -rniIE "$pat" "$@" 2>/dev/null | grep -viE '\.pyc|Binary file' | head -30)"
  if [[ -n "$out" ]]; then echo "--- $label ---"; echo "$out"; hits=$((hits+1)); fi
}

echo "### whatknown: $q   (pattern: $pat)"
show "PROBES (tools/lldb_probes: docstrings, address constants, run notes)" "$ROOT/tools/lldb_probes"
show "OTHER TOOLS/SCRIPTS" "$ROOT/tools" --include=*.py --include=*.sh --exclude-dir=lldb_probes
show "EVIDENCE BUNDLES (docs/evidence)" "$ROOT/docs/evidence"
show "CANONICAL (ledger / blockers / inventory / spec / truth)" \
     "$ROOT/docs/canonical" "$ROOT/docs/LIBRARY_INVENTORY.md" "$ROOT/docs/TRUTH.md"

# disasm symbol line for an address (what the function is / who calls it)
if printf '%s' "$qn" | grep -qiE '^[0-9a-f]{3,}$'; then
  d="$(grep -niE "(^| )${qn}:" "$ROOT/tools/libcp_disasm_intel.txt" 2>/dev/null | head -2; \
       grep -niE "call.*0x0*${qn}( |$|<)" "$ROOT/tools/libcp_disasm_intel.txt" 2>/dev/null | head -4)"
  [[ -n "$d" ]] && { echo "--- DISASM (definition + callers) ---"; echo "$d"; hits=$((hits+1)); }
fi

echo "============================================================"
if [[ "$hits" -eq 0 ]]; then
  echo "NO HITS -> genuinely undocumented. This is a real unknown; investigation justified."
else
  echo "DOCUMENTED ($hits artifact groups). READ/CONNECT the above. Do NOT re-investigate."
fi
