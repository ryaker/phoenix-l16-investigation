#!/usr/bin/env python3
"""Tool #1 — LLDB BP-Matrix Harness
Run a configurable set of LLDB breakpoints against multiple LRI files.
Output: hit-count pivot table CSV/MD + scope.md.

Usage:
  python3 tools/lldb_bp_matrix.py \
    --bp-config tools/configs/my_bps.yaml \
    --lri-list tools/configs/test_lris.txt \
    --output-dir /tmp/lldb_matrix/run01/ \
    [--render-mode bridge_hdr|bridge_ldr] \
    [--timeout-per-render 600]
"""

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_BINARY = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process"
DEFAULT_DYLIB  = "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"

LLDB_PYTHON_TEMPLATE = '''
import lldb, json, sys, time

def run(debugger, args_list):
    binary   = {binary!r}
    lri_path = {lri_path!r}
    out_path = {out_path!r}
    bps_cfg  = {bps_cfg!r}   # list of {{va_offset: int, label: str}}

    target = debugger.CreateTargetWithFileAndArch(binary, "x86_64")
    if not target:
        result = {{"lri": lri_path, "error": "create_target_failed", "hits": {{}}, "slide": "0x0"}}
        with open(out_path, "w") as f: json.dump(result, f)
        return

    err   = lldb.SBError()
    hits  = {{label: 0 for d in bps_cfg for label in [d["label"]]}}
    bps   = {{}}

    # Callbacks
    def _make_cb(label):
        def cb(frame, bp_loc, extra_args, internal_dict):
            hits[label] += 1
            return False  # auto-continue
        return cb

    # Launch stopped at entry so we can resolve slide before setting BPs
    launch_info = lldb.SBLaunchInfo([lri_path, out_path + ".render"])
    launch_info.SetWorkingDirectory("/tmp")
    launch_info.SetLaunchFlags(lldb.eLaunchFlagStopAtEntry)

    process = target.Launch(launch_info, err)
    if not process or not process.IsValid() or err.Fail():
        result = {{"lri": lri_path, "error": f"launch_failed:{{err}}", "hits": hits, "slide": "0x0"}}
        with open(out_path, "w") as f: json.dump(result, f)
        return

    # Resolve libcp slide
    slide = 0
    for i in range(target.GetNumModules()):
        mod = target.GetModuleAtIndex(i)
        if "libcp.dylib" in mod.GetFileSpec().GetFilename():
            slide = mod.GetObjectFileHeaderAddress().GetLoadAddress(target) - \
                    mod.GetObjectFileHeaderAddress().GetFileAddress()
            break

    # Install breakpoints with auto-continue
    for d in bps_cfg:
        abs_va = slide + d["va_offset"]
        bp = target.BreakpointCreateByAddress(abs_va)
        if not bp or not bp.IsValid():
            sys.stderr.write(f"[WARN] BP at {{hex(abs_va)}} ({{d[\'label\']}}) did not resolve\\n")
            continue
        bp.SetAutoContinue(True)
        cb = _make_cb(d["label"])
        bp.SetScriptCallbackFunction(None)  # clear any prior
        bp.SetCallback(cb, {{}} )
        bps[d["label"]] = bp

    t0 = time.time()
    process.Continue()
    # Wait for process exit
    listener = debugger.GetListener()
    while True:
        event = lldb.SBEvent()
        if listener.WaitForEvent(5, event):
            if lldb.SBProcess.EventIsProcessEvent(event):
                state = lldb.SBProcess.GetStateFromEvent(event)
                if state in (lldb.eStateExited, lldb.eStateCrashed, lldb.eStateDetached):
                    break
        else:
            # Timeout check done externally via SIGTERM
            pass

    elapsed = time.time() - t0
    exit_status = process.GetExitStatus()

    result = {{
        "lri": lri_path,
        "slide": hex(slide),
        "hits": hits,
        "exit_status": exit_status,
        "render_seconds": round(elapsed, 2)
    }}
    with open(out_path, "w") as f:
        json.dump(result, f)

run(lldb.debugger, [])
'''


def load_bp_config(config_path: str) -> dict:
    """Load YAML bp-config. Returns dict with 'binary', 'dylib', 'breakpoints'."""
    if yaml is None:
        # Minimal YAML parser for our simple format
        return _parse_yaml_simple(config_path)
    with open(config_path) as f:
        return yaml.safe_load(f)


def _parse_yaml_simple(config_path: str) -> dict:
    """Hand-parse the bp-config YAML (avoids pyyaml dependency)."""
    result = {"binary": DEFAULT_BINARY, "dylib": DEFAULT_DYLIB, "breakpoints": []}
    with open(config_path) as f:
        lines = f.readlines()
    in_bps = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("binary:"):
            result["binary"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("dylib:"):
            result["dylib"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("breakpoints:"):
            in_bps = True
        elif in_bps and stripped.startswith("- {"):
            # e.g.:  - { va: 0x3f0b90, label: DOFCache_render }
            inner = stripped[3:].rstrip("}").strip()
            kv = {}
            for part in inner.split(","):
                k, v = part.strip().split(":", 1)
                kv[k.strip()] = v.strip()
            if "va" in kv and "label" in kv:
                result["breakpoints"].append({
                    "va": int(kv["va"], 16),
                    "label": kv["label"]
                })
    return result


def load_lri_list(list_path: str) -> list[str]:
    paths = []
    with open(list_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                paths.append(line)
    return paths


def run_lldb_on_lri(binary: str, lri_path: str, bps: list[dict], output_json: str,
                    timeout_seconds: int = 600) -> dict:
    """Spawn arch -x86_64 lldb with inline Python script. Returns parsed result dict."""

    bps_cfg = [{"va_offset": bp["va"], "label": bp["label"]} for bp in bps]

    script_content = LLDB_PYTHON_TEMPLATE.format(
        binary=binary,
        lri_path=lri_path,
        out_path=output_json,
        bps_cfg=bps_cfg
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tf:
        tf.write(script_content)
        script_path = tf.name

    # Write lldb commands file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lldbinit', delete=False) as tf2:
        tf2.write(f"command script import {script_path}\n")
        tf2.write("quit\n")
        lldb_init_path = tf2.name

    cmd = ["arch", "-x86_64", "lldb", "--no-use-colors", "--source", lldb_init_path]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait()
            return {
                "lri": lri_path,
                "error": "timeout",
                "hits": {bp["label"]: 0 for bp in bps},
                "slide": "0x0",
                "exit_status": -1,
                "render_seconds": timeout_seconds
            }
    except Exception as e:
        return {
            "lri": lri_path,
            "error": str(e),
            "hits": {bp["label"]: 0 for bp in bps},
            "slide": "0x0",
            "exit_status": -1,
            "render_seconds": 0
        }
    finally:
        os.unlink(script_path)
        os.unlink(lldb_init_path)

    # Read result JSON
    if os.path.exists(output_json):
        try:
            with open(output_json) as f:
                return json.load(f)
        except Exception as e:
            return {
                "lri": lri_path,
                "error": f"json_parse_failed:{e}",
                "hits": {bp["label"]: 0 for bp in bps},
                "slide": "0x0"
            }
    else:
        return {
            "lri": lri_path,
            "error": "no_output_json",
            "hits": {bp["label"]: 0 for bp in bps},
            "slide": "0x0",
            "stderr": stderr.decode(errors='replace')[-500:]
        }


def write_matrix_csv(results: list[dict], bp_labels: list[str], output_dir: Path):
    lri_names = [Path(r["lri"]).name for r in results]

    csv_path = output_dir / "matrix.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["BP_label"] + lri_names)
        for label in bp_labels:
            row = [label]
            for r in results:
                row.append(r.get("hits", {}).get(label, 0))
            writer.writerow(row)
    return csv_path


def write_matrix_md(results: list[dict], bp_labels: list[str], output_dir: Path):
    lri_names = [Path(r["lri"]).name for r in results]
    slides = [r.get("slide", "?") for r in results]
    elapsed = [r.get("render_seconds", 0) for r in results]
    errors = [r.get("error", "") for r in results]

    md_path = output_dir / "matrix.md"
    with open(md_path, 'w') as f:
        f.write("# LLDB BP-Matrix Results\n\n")
        f.write("| BP_label | " + " | ".join(lri_names) + " |\n")
        f.write("|---" + "|---" * len(lri_names) + "|\n")
        for label in bp_labels:
            row = [label]
            for r in results:
                count = r.get("hits", {}).get(label, 0)
                row.append(str(count))
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n## Per-LRI metadata\n\n")
        f.write("| LRI | slide | render_sec | error |\n")
        f.write("|---|---|---|---|\n")
        for i, r in enumerate(results):
            f.write(f"| {lri_names[i]} | {slides[i]} | {elapsed[i]} | {errors[i] or '-'} |\n")
    return md_path


def write_scope_md(results: list[dict], bp_labels: list[str],
                   render_mode: str, output_dir: Path):
    scope_path = output_dir / "scope.md"
    lri_names = [Path(r["lri"]).name for r in results]

    # Detect untested axes
    untested = []
    focal_found = set()
    for n in lri_names:
        for t in ["28mm", "35mm", "70mm", "150mm"]:
            if t in n or t.replace("mm", "") in n:
                focal_found.add(t)
    all_focal = {"28mm", "35mm", "70mm", "150mm"}
    missing_focal = all_focal - focal_found
    if missing_focal:
        untested.append(f"focal lengths not tested: {', '.join(sorted(missing_focal))}")

    hdr_tested = "bridge_hdr" in render_mode or "hdr" in render_mode.lower()
    ldr_tested = "bridge_ldr" in render_mode or "ldr" in render_mode.lower()
    if hdr_tested and not ldr_tested:
        untested.append("LDR mode not tested (all LRIs rendered as HDR)")
    if ldr_tested and not hdr_tested:
        untested.append("HDR mode not tested (all LRIs rendered as LDR)")

    zero_hit_labels = []
    for label in bp_labels:
        total_hits = sum(r.get("hits", {}).get(label, 0) for r in results)
        if total_hits == 0:
            zero_hit_labels.append(label)

    with open(scope_path, 'w') as f:
        f.write("# Scope Record\n\n")
        f.write(f"**Render mode**: {render_mode}\n\n")
        f.write("## Tested conditions\n\n")
        for r in results:
            f.write(f"- `{Path(r['lri']).name}` — slide {r.get('slide','?')}, "
                    f"{r.get('render_seconds','?')}s, "
                    f"exit {r.get('exit_status','?')}\n")
        f.write("\n## Untested axes\n\n")
        if untested:
            for u in untested:
                f.write(f"- {u}\n")
        else:
            f.write("- None identified (all major axes covered)\n")
        f.write("\n## Zero-hit BPs (scoped to these tested conditions ONLY)\n\n")
        if zero_hit_labels:
            for label in zero_hit_labels:
                f.write(f"- `{label}` — 0 hits under tested conditions above\n")
            f.write("\n**Cannot conclude**: these are dead code. They may fire under untested conditions.\n")
        else:
            f.write("- None (all BPs fired at least once)\n")
    return scope_path


def main():
    parser = argparse.ArgumentParser(description="LLDB BP-Matrix Harness")
    parser.add_argument("--bp-config", required=True, help="YAML BP config file")
    parser.add_argument("--lri-list", required=True, help="Text file with LRI paths (one per line)")
    parser.add_argument("--output-dir", required=True, help="Directory for output files")
    parser.add_argument("--render-mode", default="bridge_hdr",
                        choices=["bridge_hdr", "bridge_ldr"],
                        help="Render mode label for scope.md")
    parser.add_argument("--timeout-per-render", type=int, default=600,
                        help="Per-LRI timeout in seconds")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_bp_config(args.bp_config)
    binary = cfg.get("binary", DEFAULT_BINARY)
    bps = cfg.get("breakpoints", [])
    bp_labels = [bp["label"] for bp in bps]

    lri_paths = load_lri_list(args.lri_list)
    if not lri_paths:
        print("[ERROR] No LRI paths found in list file.", file=sys.stderr)
        sys.exit(1)

    print(f"[matrix] {len(bps)} BPs × {len(lri_paths)} LRIs", file=sys.stderr)
    print(f"[matrix] binary: {binary}", file=sys.stderr)
    print(f"[matrix] output: {output_dir}", file=sys.stderr)

    results = []
    jsonl_path = output_dir / "raw_results.jsonl"

    with open(jsonl_path, 'w') as jsonl_f:
        for i, lri_path in enumerate(lri_paths):
            lri_name = Path(lri_path).name
            print(f"\n[{i+1}/{len(lri_paths)}] {lri_name} ...", file=sys.stderr)

            output_json = str(output_dir / f"{lri_name}.result.json")
            t0 = time.time()

            try:
                result = run_lldb_on_lri(
                    binary=binary,
                    lri_path=lri_path,
                    bps=bps,
                    output_json=output_json,
                    timeout_seconds=args.timeout_per_render
                )
            except Exception as e:
                result = {
                    "lri": lri_path,
                    "error": str(e),
                    "hits": {label: 0 for label in bp_labels},
                    "slide": "0x0"
                }

            results.append(result)
            jsonl_f.write(json.dumps(result) + "\n")
            jsonl_f.flush()

            # Print per-LRI summary
            if result.get("error"):
                print(f"  ERROR: {result['error']}", file=sys.stderr)
            else:
                hits_summary = {k: v for k, v in result.get("hits", {}).items() if v > 0}
                print(f"  slide={result.get('slide','?')} "
                      f"time={result.get('render_seconds','?')}s "
                      f"exit={result.get('exit_status','?')} "
                      f"hits={hits_summary}",
                      file=sys.stderr)

    csv_path = write_matrix_csv(results, bp_labels, output_dir)
    md_path = write_matrix_md(results, bp_labels, output_dir)
    scope_path = write_scope_md(results, bp_labels, args.render_mode, output_dir)

    print(f"\n[matrix] Done.")
    print(f"  raw JSONL : {jsonl_path}")
    print(f"  matrix CSV: {csv_path}")
    print(f"  matrix MD : {md_path}")
    print(f"  scope MD  : {scope_path}")

    # Print pivot to stdout
    print("\n## Hit-count pivot")
    lri_names = [Path(r["lri"]).name for r in results]
    header = f"{'BP_label':<35} " + "  ".join(f"{n[:20]:>20}" for n in lri_names)
    print(header)
    print("-" * len(header))
    for label in bp_labels:
        row = f"{label:<35} " + "  ".join(
            f"{r.get('hits', {}).get(label, 0):>20}" for r in results
        )
        print(row)


if __name__ == "__main__":
    main()
