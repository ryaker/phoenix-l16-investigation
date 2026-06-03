#!/bin/zsh
# Lane B Unit-2 four-zoom: run ONE instrumented render at a time.
# Usage: run_one.sh <zoom_label> <lri_path>
#
# lri_process CLI:  lri_process <input.lri> <output> [--profile N]
#
# Runtime quirk (observed 2026-06-02): lri_process intermittently exits with
# "Cannot open" + status 1 BEFORE the IRAMP accumulator. It is timing related
# (the same .lldb succeeds on other attempts). The .lldb writes the captured
# tile + regs + bt to a RESULT json from inside lldb (Python file I/O), so the
# capture survives independent of stdout. The wrapper retries until coeff16 is
# captured. lldb stdout is left attached to the caller's terminal (NOT
# redirected to a regular file -- that redirection makes the race ~always fail).
# The raw console is captured by the caller; we additionally keep the RESULT
# json + the last attempt's console (via `script` typescript) in the packet.
#
# Capture pattern (manual stop, no breakpoint callback):
#   stop at main -> libcp_base -> anchor disasm at base+0x3eced0 ->
#   bare BP base+0x369fa4, delete main -> process continue -> first-hit stop ->
#   read $rbp-0xa0 (16 floats) + regs + bt -> write RESULT json.

set -u

ZOOM="$1"
LRI="$2"

QUAR="/Volumes/Dev/L16-opus-quarantine"
RUNS="$QUAR/runs/laneB_unit2_fourzoom"
LRI_PROCESS="/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process"
FW="/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
LOG="$RUNS/${ZOOM}.log"
OUT="/tmp/laneB_${ZOOM}_out.hdr"
RESULT="$RUNS/${ZOOM}_result.json"
SCRIPT="$RUNS/${ZOOM}.lldb"

mkdir -p "$RUNS"
/bin/rm -f "$RESULT"

cat > "$SCRIPT" <<'EOF'
target create __LRI_PROCESS__
settings set target.env-vars DYLD_FRAMEWORK_PATH=__FW__ DYLD_LIBRARY_PATH=__FW__
breakpoint set --name main
process launch -- "__LRI__" "__OUT__" --profile 3
command script import __PROBE_PY__
script lanebcap.run(lldb, "__ZOOM__", "__LRI__", "__RESULT__")
quit
EOF

/usr/bin/sed -i '' \
  -e "s|__LRI_PROCESS__|$LRI_PROCESS|g" \
  -e "s|__FW__|$FW|g" \
  -e "s|__LRI__|$LRI|g" \
  -e "s|__OUT__|$OUT|g" \
  -e "s|__ZOOM__|$ZOOM|g" \
  -e "s|__RESULT__|$RESULT|g" \
  -e "s|__PROBE_PY__|$QUAR/tools/lldb_probes/opus_pending/laneB_unit2_fourzoom/lanebcap.py|g" \
  "$SCRIPT"

cd /tmp || exit 3
MAX=10
attempt=0
while [ $attempt -lt $MAX ]; do
  attempt=$((attempt+1))
  # Direct lldb invocation, stdout straight to the log file. (Wrapping this in
  # `( ... ) | tee` made the "Cannot open" race ~always fire; direct is stable.)
  arch -x86_64 lldb -b -s "$SCRIPT" > "$LOG" 2>&1
  if [ -f "$RESULT" ] && /usr/bin/grep -q '"coeff16": \[' "$RESULT"; then
    echo "LANEB_WRAPPER zoom=$ZOOM attempt=$attempt result=CAPTURED"
    break
  else
    transient=$(/usr/bin/grep -c "Cannot open" "$LOG" 2>/dev/null)
    echo "LANEB_WRAPPER zoom=$ZOOM attempt=$attempt result=RETRY cannot_open=$transient"
  fi
done

echo "=== RESULT JSON ($RESULT) ==="
[ -f "$RESULT" ] && /bin/cat "$RESULT" || echo "NO RESULT FILE"
