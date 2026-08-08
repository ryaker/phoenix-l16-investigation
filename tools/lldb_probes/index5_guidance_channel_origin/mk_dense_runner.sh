#!/bin/bash
# mk_dense_runner.sh <name> <lri_path>  -> emits a safe single-plane guidance dump runner
# Only breakpoints 0x27c062 (per-plane, NOT the hot 0x3f5035), reset max=1 -> dump first
# anchor plane, kill immediately. This is the version that ran 4x without memory issues.
NAME="$1"; LRI="$2"; OUT=/Users/ryaker/L16_Phoenix/phoenix_out
P=/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/index5_guidance_channel_origin
cat > "$P/run_${NAME}.lldb" <<EOF
command script import $P/guidance_dense_dump_probe.py
script guidance_dense_dump_probe.reset("$OUT/GUID_${NAME}", 1)
settings set target.env-vars DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks
target create /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
process handle SIGSEGV -p true -s false -n false
breakpoint set --shlib libcp.dylib --address 0x27c062
script guidance_dense_dump_probe.attach(lldb.debugger)
process launch -- "$LRI" "/private/tmp/${NAME}.hdr" --profile 3 --export-fmt 3 --no-auto-lris
script guidance_dense_dump_probe.write_report(lldb.debugger, "$OUT/GUID_${NAME}.json")
quit
EOF
echo "wrote $P/run_${NAME}.lldb"
