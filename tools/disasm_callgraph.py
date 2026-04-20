#!/usr/bin/env python3
"""Tool #3 — Disasm Call-Graph Database
Stream-parse libcp_disasm_intel.txt and build a queryable sqlite DB
of call edges and string xrefs. Never loads full file into memory.

Build:  python3 tools/disasm_callgraph.py build [--disasm <path>] [--db <path>]
Query:  python3 tools/disasm_callgraph.py callers 0x30b9f0
        python3 tools/disasm_callgraph.py callees 0x30b770
        python3 tools/disasm_callgraph.py xref-string "Requested DOFCache"
        python3 tools/disasm_callgraph.py xref-rip 0x5e41b4
        python3 tools/disasm_callgraph.py function-at 0x30b9f0
"""

import argparse
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

DEFAULT_DISASM = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/libcp_disasm_intel.txt"
DEFAULT_DB = str(Path(__file__).parent / "libcp_callgraph.db")
DEFAULT_DYLIB = "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
SUMMARY_PATH = str(Path(__file__).parent / "libcp_callgraph_summary.md")

# Compiled regexes — compile once
# Disasm format (Intel, otool-style, no hex bytes column):
#   <16-hex-VA> <symbol>:     — function header (leading zeros)
#   <short-VA>:    \t<mnemonic>\t<operands>   — instruction line
RE_SYM_HEADER   = re.compile(r'^([0-9a-f]{1,16})\s+<(.+?)>:\s*$')
RE_INSN_VA      = re.compile(r'^\s+([0-9a-f]+):\s')
# Applied to full instruction text (mnemonic + operands)
RE_DIRECT_CALL  = re.compile(r'\bcall[q]?\s+(?:0x)?([0-9a-f]+)\b')
RE_INDIRECT_CALL = re.compile(r'\bcall[q]?\s+(?:r[a-z0-9]+|QWORD PTR|\[)', re.IGNORECASE)
# Intel: [rip + 0xOFFSET]
RE_LEA_RIP      = re.compile(r'\blea\b.*\[rip\s*[+\-]\s*0x([0-9a-f]+)\]', re.IGNORECASE)

SCHEMA = """
CREATE TABLE IF NOT EXISTS functions (
    entry_va INTEGER PRIMARY KEY,
    size     INTEGER,
    name     TEXT
);
CREATE TABLE IF NOT EXISTS call_edges (
    from_va  INTEGER,
    to_va    INTEGER,
    kind     TEXT
);
CREATE TABLE IF NOT EXISTS string_xrefs (
    from_va   INTEGER,
    target_va INTEGER,
    string    TEXT
);
CREATE TABLE IF NOT EXISTS rip_refs (
    from_va   INTEGER,
    target_va INTEGER
);
CREATE INDEX IF NOT EXISTS idx_callers ON call_edges(to_va);
CREATE INDEX IF NOT EXISTS idx_callees ON call_edges(from_va);
CREATE INDEX IF NOT EXISTS idx_rip_target ON rip_refs(target_va);
CREATE INDEX IF NOT EXISTS idx_strxref ON string_xrefs(string);
"""


def get_cstring_range(dylib_path: str) -> tuple[int, int]:
    """Use otool -l to find __cstring section VA range."""
    try:
        out = subprocess.check_output(
            ["otool", "-l", dylib_path],
            stderr=subprocess.DEVNULL
        ).decode(errors='replace')
    except Exception:
        return (0, 0)

    in_cstring = False
    addr = None
    size = None
    for line in out.splitlines():
        line = line.strip()
        if "sectname __cstring" in line:
            in_cstring = True
        elif in_cstring:
            if line.startswith("addr "):
                try:
                    addr = int(line.split()[1], 16)
                except ValueError:
                    pass
            elif line.startswith("size "):
                try:
                    size = int(line.split()[1], 16)
                except ValueError:
                    pass
            elif line.startswith("sectname") and addr and size:
                break
        if addr and size:
            break
    if addr and size:
        return (addr, addr + size)
    return (0, 0)


def extract_strings_at(dylib_path: str, target_vas: list[int], cstring_start: int) -> dict[int, str]:
    """Read strings at target VAs from the dylib using file offset = VA (for __TEXT)."""
    result = {}
    if not target_vas or cstring_start == 0:
        return result
    try:
        with open(dylib_path, 'rb') as f:
            for va in target_vas:
                offset = va  # __TEXT vmaddr=0, so file_offset = VA
                if offset < 0:
                    continue
                try:
                    f.seek(offset)
                    raw = f.read(256)
                    end = raw.find(b'\x00')
                    s = raw[:end].decode('utf-8', errors='replace') if end >= 0 else raw.decode('utf-8', errors='replace')
                    if s and all(0x20 <= ord(c) < 0x7f or c in '\t\n' for c in s):
                        result[va] = s
                except Exception:
                    pass
    except Exception:
        pass
    return result


def build_db(disasm_path: str, db_path: str, dylib_path: str):
    print(f"[build] Streaming {disasm_path}", file=sys.stderr)
    print(f"[build] Output DB: {db_path}", file=sys.stderr)

    cstring_start, cstring_end = get_cstring_range(dylib_path)
    print(f"[build] __cstring range: 0x{cstring_start:x} – 0x{cstring_end:x}", file=sys.stderr)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()

    # Batch insert buffers
    BUF_SIZE = 50000
    funcs_buf = []
    edges_buf = []
    rip_buf = []

    current_func_va = None
    current_func_name = None
    current_func_start = None
    prev_insn_va = None
    prev_insn_end = None  # VA of next instruction after prev

    line_count = 0
    func_count = 0
    edge_count = 0
    rip_count = 0
    rip_cstring_targets = []  # (from_va, target_va) where target is in __cstring

    def flush_buffers():
        nonlocal edge_count, rip_count
        if funcs_buf:
            cur.executemany(
                "INSERT OR REPLACE INTO functions(entry_va,size,name) VALUES(?,?,?)",
                funcs_buf
            )
            funcs_buf.clear()
        if edges_buf:
            cur.executemany(
                "INSERT INTO call_edges(from_va,to_va,kind) VALUES(?,?,?)",
                edges_buf
            )
            edge_count += len(edges_buf)
            edges_buf.clear()
        if rip_buf:
            cur.executemany(
                "INSERT INTO rip_refs(from_va,target_va) VALUES(?,?)",
                rip_buf
            )
            rip_count += len(rip_buf)
            rip_buf.clear()
        conn.commit()

    with open(disasm_path, 'r', errors='replace') as f:
        for line in f:
            line_count += 1
            if line_count % 5_000_000 == 0:
                flush_buffers()
                print(f"[build] {line_count:,} lines | {func_count} funcs | {edge_count} edges | {rip_count} rip_refs",
                      file=sys.stderr)

            line_stripped = line.rstrip('\n')

            # Function header: "000000000030b9f0 <_ZN..._E>:"
            m = RE_SYM_HEADER.match(line_stripped)
            if m:
                va = int(m.group(1), 16)
                name = m.group(2)
                if current_func_va is not None and prev_insn_end is not None:
                    size = prev_insn_end - current_func_va
                    funcs_buf.append((current_func_va, size, current_func_name))
                    func_count += 1
                current_func_va = va
                current_func_name = name
                prev_insn_va = None
                prev_insn_end = None
                continue

            # Instruction line: "  30b9f0:  <bytes>  <mnemonic> <operands>"
            m_va = RE_INSN_VA.match(line_stripped)
            if not m_va or current_func_va is None:
                continue

            insn_va = int(m_va.group(1), 16)
            prev_insn_va = insn_va
            # We'll estimate next-insn VA from the next line; for now track current
            # In this disasm format: "    <VA>:    \t<mnemonic>\t<operands>"
            # No hex bytes column. Use full remainder of line for regex search.
            insn_text = line_stripped[m_va.end():]

            # Direct call: call 0xTARGET <label>
            m_call = RE_DIRECT_CALL.search(insn_text)
            if m_call:
                target_str = m_call.group(1)
                # Reject hits where the "target" is just from the label annotation
                target = int(target_str, 16)
                # Sanity: call targets should be in plausible dylib VA range
                if 0x1000 < target < 0x10000000:
                    edges_buf.append((insn_va, target, 'direct'))
                    if len(edges_buf) >= BUF_SIZE:
                        flush_buffers()
                continue

            # Indirect call: call rax / call [rip+...] / call QWORD PTR [...]
            if RE_INDIRECT_CALL.search(insn_text):
                edges_buf.append((insn_va, 0, 'indirect'))
                if len(edges_buf) >= BUF_SIZE:
                    flush_buffers()
                continue

            # RIP-relative LEA: lea rax, [rip + 0xOFFSET]
            m_rip = RE_LEA_RIP.search(insn_text)
            if m_rip:
                offset_str = m_rip.group(1)
                if offset_str:
                    offset = int(offset_str, 16)
                    next_va = insn_va + 7  # approximate: LEA is typically 7 bytes
                    target_va = next_va + offset
                    rip_buf.append((insn_va, target_va))
                    if cstring_start <= target_va < cstring_end:
                        rip_cstring_targets.append((insn_va, target_va))
                    if len(rip_buf) >= BUF_SIZE:
                        flush_buffers()

    # Flush final function
    if current_func_va is not None:
        funcs_buf.append((current_func_va, 0, current_func_name))
        func_count += 1

    flush_buffers()

    # String xref post-pass: look up __cstring strings
    print(f"[build] Resolving {len(rip_cstring_targets)} __cstring xrefs...", file=sys.stderr)
    unique_targets = list({t for _, t in rip_cstring_targets})
    str_map = extract_strings_at(dylib_path, unique_targets, cstring_start)

    xref_rows = []
    for from_va, target_va in rip_cstring_targets:
        s = str_map.get(target_va)
        if s:
            xref_rows.append((from_va, target_va, s))

    if xref_rows:
        cur.executemany(
            "INSERT INTO string_xrefs(from_va,target_va,string) VALUES(?,?,?)",
            xref_rows
        )
        conn.commit()

    # Write summary
    cur.execute("SELECT COUNT(*) FROM functions")
    n_funcs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM call_edges")
    n_edges = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM string_xrefs")
    n_xrefs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM rip_refs")
    n_rip = cur.fetchone()[0]

    summary = f"""# libcp Call-Graph Database Summary

Built from: `{disasm_path}`
DB: `{db_path}`

| Metric | Count |
|--------|-------|
| Functions | {n_funcs:,} |
| Call edges (direct) | {n_edges:,} |
| RIP refs | {n_rip:,} |
| String xrefs | {n_xrefs:,} |
| __cstring range | 0x{cstring_start:x} – 0x{cstring_end:x} |
"""
    with open(SUMMARY_PATH, 'w') as f:
        f.write(summary)

    conn.close()
    print(f"[build] Done. {n_funcs:,} funcs / {n_edges:,} edges / {n_xrefs:,} str-xrefs", file=sys.stderr)
    print(summary)


def open_db(db_path: str) -> sqlite3.Connection:
    if not Path(db_path).exists():
        print(f"[ERROR] DB not found: {db_path}", file=sys.stderr)
        print("Run: python3 tools/disasm_callgraph.py build", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(db_path)


def cmd_callers(db_path: str, target_va_str: str):
    va = int(target_va_str, 16)
    conn = open_db(db_path)
    rows = conn.execute(
        "SELECT from_va, kind FROM call_edges WHERE to_va=? ORDER BY from_va",
        (va,)
    ).fetchall()
    if not rows:
        print(f"No callers of 0x{va:x}")
        return
    print(f"Callers of 0x{va:x} ({len(rows)} hits):")
    for from_va, kind in rows:
        # Try to find function containing from_va
        func = conn.execute(
            "SELECT name, entry_va FROM functions WHERE entry_va <= ? ORDER BY entry_va DESC LIMIT 1",
            (from_va,)
        ).fetchone()
        func_str = f"  [{func[1]:x} <{func[0]}>]" if func else ""
        print(f"  0x{from_va:x}  ({kind}){func_str}")
    conn.close()


def cmd_callees(db_path: str, from_va_str: str):
    va = int(from_va_str, 16)
    conn = open_db(db_path)
    # Get all instructions in this function
    func = conn.execute(
        "SELECT entry_va, size, name FROM functions WHERE entry_va <= ? ORDER BY entry_va DESC LIMIT 1",
        (va,)
    ).fetchone()
    if func and func[1] > 0:
        func_end = func[0] + func[1]
        rows = conn.execute(
            "SELECT from_va, to_va, kind FROM call_edges WHERE from_va >= ? AND from_va < ? ORDER BY from_va",
            (func[0], func_end)
        ).fetchall()
        print(f"Callees from 0x{func[0]:x} <{func[2]}> ({len(rows)} call sites):")
    else:
        rows = conn.execute(
            "SELECT from_va, to_va, kind FROM call_edges WHERE from_va=? ORDER BY from_va",
            (va,)
        ).fetchall()
        print(f"Callees from 0x{va:x} ({len(rows)} hits):")
    for from_va, to_va, kind in rows:
        callee = conn.execute(
            "SELECT name FROM functions WHERE entry_va=?", (to_va,)
        ).fetchone()
        callee_str = f" <{callee[0]}>" if callee else ""
        print(f"  0x{from_va:x} → 0x{to_va:x}{callee_str}  ({kind})")
    conn.close()


def cmd_xref_string(db_path: str, pattern: str):
    conn = open_db(db_path)
    rows = conn.execute(
        "SELECT from_va, target_va, string FROM string_xrefs WHERE string LIKE ? ORDER BY from_va",
        (f"%{pattern}%",)
    ).fetchall()
    if not rows:
        print(f"No string xrefs matching: {pattern!r}")
        return
    print(f"String xrefs matching {pattern!r} ({len(rows)} hits):")
    for from_va, target_va, s in rows:
        print(f"  0x{from_va:x} → 0x{target_va:x}  {s!r}")
    conn.close()


def cmd_xref_rip(db_path: str, target_va_str: str):
    va = int(target_va_str, 16)
    conn = open_db(db_path)
    rows = conn.execute(
        "SELECT from_va FROM rip_refs WHERE target_va=? ORDER BY from_va",
        (va,)
    ).fetchall()
    if not rows:
        print(f"No RIP refs to 0x{va:x}")
        return
    print(f"RIP refs to 0x{va:x} ({len(rows)} hits):")
    for (from_va,) in rows:
        func = conn.execute(
            "SELECT name, entry_va FROM functions WHERE entry_va <= ? ORDER BY entry_va DESC LIMIT 1",
            (from_va,)
        ).fetchone()
        func_str = f"  [{func[1]:x} <{func[0]}>]" if func else ""
        print(f"  0x{from_va:x}{func_str}")
    conn.close()


def cmd_function_at(db_path: str, va_str: str):
    va = int(va_str, 16)
    conn = open_db(db_path)
    row = conn.execute(
        "SELECT entry_va, size, name FROM functions WHERE entry_va <= ? ORDER BY entry_va DESC LIMIT 1",
        (va,)
    ).fetchone()
    if not row:
        print(f"No function found containing 0x{va:x}")
        return
    entry_va, size, name = row
    if size > 0 and va > entry_va + size:
        print(f"0x{va:x} is not within any known function (closest: 0x{entry_va:x})")
        return
    print(f"Function containing 0x{va:x}:")
    print(f"  entry_va : 0x{entry_va:x}")
    print(f"  size     : 0x{size:x} ({size} bytes)")
    print(f"  name     : {name}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Disasm Call-Graph Database")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--disasm", default=DEFAULT_DISASM)
    p_build.add_argument("--db", default=DEFAULT_DB)
    p_build.add_argument("--dylib", default=DEFAULT_DYLIB)

    p_callers = sub.add_parser("callers")
    p_callers.add_argument("va")
    p_callers.add_argument("--db", default=DEFAULT_DB)

    p_callees = sub.add_parser("callees")
    p_callees.add_argument("va")
    p_callees.add_argument("--db", default=DEFAULT_DB)

    p_xref_str = sub.add_parser("xref-string")
    p_xref_str.add_argument("pattern")
    p_xref_str.add_argument("--db", default=DEFAULT_DB)

    p_xref_rip = sub.add_parser("xref-rip")
    p_xref_rip.add_argument("va")
    p_xref_rip.add_argument("--db", default=DEFAULT_DB)

    p_func = sub.add_parser("function-at")
    p_func.add_argument("va")
    p_func.add_argument("--db", default=DEFAULT_DB)

    args = parser.parse_args()

    if args.cmd == "build":
        build_db(args.disasm, args.db, args.dylib)
    elif args.cmd == "callers":
        cmd_callers(args.db, args.va)
    elif args.cmd == "callees":
        cmd_callees(args.db, args.va)
    elif args.cmd == "xref-string":
        cmd_xref_string(args.db, args.pattern)
    elif args.cmd == "xref-rip":
        cmd_xref_rip(args.db, args.va)
    elif args.cmd == "function-at":
        cmd_function_at(args.db, args.va)


if __name__ == "__main__":
    main()
