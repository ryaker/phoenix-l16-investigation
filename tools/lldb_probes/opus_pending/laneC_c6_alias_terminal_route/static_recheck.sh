#!/bin/zsh
# Lane C — C6 alias/terminal-route STATIC re-check (no runtime; pure otool/grep).
# Usage: ./static_recheck.sh [path-to-libcp.dylib]
# Emits the same observations the packet is built on. file offset == VA.
set -e
LIB="${1:-/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib}"
echo "== binary =="; ls -l "$LIB"; shasum -a 256 "$LIB"
echo "expected sha256: b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

TMP="$(mktemp)"
otool -arch x86_64 -tV "$LIB" > "$TMP"
echo "== disasm lines: $(wc -l < "$TMP") =="

echo "== ANCHOR 0x3eced0 fn + triple inside =="
grep -n '^00000000003eced0' "$TMP" || echo "MISS 0x3eced0"
ANCHLN=$(grep -n '^00000000003eced0' "$TMP" | head -1 | cut -d: -f1)
[ -n "$ANCHLN" ] && sed -n "${ANCHLN},$((ANCHLN+200))p" "$TMP" | grep -nE 'mulps|maxps|sqrtps' | head -3

echo "== f2720 key getter (expect: movl 0x60(%rdi),%eax) =="
L=$(grep -n '^00000000000f2720' "$TMP" | head -1 | cut -d: -f1); sed -n "${L},$((L+4))p" "$TMP"

echo "== clear 0x3c90a5 (expect: movb \$0x0,0x30(%rax), preceded by cmpl \$0xf) =="
L=$(grep -n '^00000000003c90a5' "$TMP" | head -1 | cut -d: -f1); sed -n "$((L-3)),${L}p" "$TMP"

echo "== ANGLE 1: constructor f2770 item dst-field set =="
awk 'NR>=237811 && NR<=238010' "$TMP" \
  | grep -oE '(movl|movb|movw|movq)\t[^,]+, 0x[0-9a-f]+\((%rdx|%r13)\)' \
  | grep -oE '0x[0-9a-f]+\((%rdx|%r13)\)' | sort -u

echo "== ANGLE 2: count of cmpl \$0xf,%eax preceded by callq 0xf2720 =="
grep -nE 'cmpl\s+\$0xf, %eax' "$TMP" | cut -d: -f1 | while read ln; do
  sed -n "$((ln-1))p" "$TMP" | grep -q 'callq[[:space:]]*0xf2720' && echo "  getter-fed @ $(sed -n ${ln}p "$TMP" | awk '{print $1}')"
done

echo "== ANGLE 3: f6c60 classifier masks (expect 0xfc00 and 0x1f) =="
L=$(grep -n '^00000000000f6c60' "$TMP" | head -1 | cut -d: -f1); sed -n "${L},$((L+20))p" "$TMP" | grep -E 'cmpl|movl.*0xfc00|movl.*0x1f|btl|\$0x2,|unknown camera'

echo "== counts =="
echo "f2720 callers: $(grep -cE 'callq[[:space:]]*0xf2720' "$TMP")"
echo "f6c60 callers: $(grep -cE 'callq[[:space:]]*0xf6c60' "$TMP")"
echo "f2750 callers: $(grep -cE 'callq[[:space:]]*0xf2750' "$TMP")"
rm -f "$TMP"
