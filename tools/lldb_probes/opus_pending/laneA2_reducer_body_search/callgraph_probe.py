#!/usr/bin/env python3
# Lane A2 static reducer/body search probe (STATIC ONLY -- otool disasm + raw pointer-table reads).
# NO render, NO runtime, NO breakpoints. Reproduces:
#   - direct-call graph reachability between 0x23faf0 (record-clone helper) hosts and image kernels
#   - vtable / RTTI resolution for kernels reached only via std::function/vtable indirection
#
# Usage:
#   1) otool -arch x86_64 -tV <libcp.dylib> > full_disasm.txt
#   2) python3 callgraph_probe.py full_disasm.txt <libcp.dylib>
#
# Output is printed; capture to runs/laneA2_reducer_body_search/*.log

import re, bisect, struct, sys

DIS = sys.argv[1] if len(sys.argv) > 1 else 'full_disasm.txt'
LIB = sys.argv[2] if len(sys.argv) > 2 else \
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"

IMG_KERNELS = {0x3ec770, 0x365960, 0x3661b0, 0x2f78e0, 0x369f80, 0x3ec960}
RECORD_CLONE = 0x23faf0  # State-helper-derived tree-node-family copy ctor / clone

def load_entries(path):
    entries = []
    for l in open(path).read().splitlines():
        m = re.match(r'^([0-9a-f]{16})\t(.*)', l)
        if m:
            entries.append((int(m.group(1), 16), m.group(2)))
    return entries

def build_graph(entries):
    prologue_va = [va for va, t in entries if t == 'pushq\t%rbp']
    call_re = re.compile(r'callq\t(0x[0-9a-f]+)')
    edges = {}
    cur = None
    for va, t in entries:
        if t == 'pushq\t%rbp':
            cur = va
        if cur is not None:
            m = call_re.search(t)
            if m:
                edges.setdefault(cur, set()).add(int(m.group(1), 16))
    rev = {}
    for f, ts in edges.items():
        for t in ts:
            rev.setdefault(t, set()).add(f)
    return prologue_va, edges, rev

def func_start(prologue_va, va):
    j = bisect.bisect_right(prologue_va, va) - 1
    return prologue_va[j] if j >= 0 else None

def transitive_callers(rev, seeds):
    reach = set()
    stack = list(seeds)
    while stack:
        n = stack.pop()
        for c in rev.get(n, ()):
            if c not in reach:
                reach.add(c)
                stack.append(c)
    return reach

def read_cstr(data, off):
    e = data.find(b'\x00', off)
    return data[off:e].decode('latin1', 'replace')

def find_ptr_refs(data, va, limit=20):
    needle = struct.pack('<Q', va)
    offs = []
    s = 0
    while True:
        i = data.find(needle, s)
        if i < 0:
            break
        offs.append(i)
        s = i + 1
        if len(offs) > limit:
            break
    return offs

def main():
    entries = load_entries(DIS)
    prologue_va, edges, rev = build_graph(entries)
    data = open(LIB, 'rb').read()

    print("=== Lane A2 static reducer/body search ===")
    print("IMG kernels:", [hex(x) for x in sorted(IMG_KERNELS)])

    reach = transitive_callers(rev, IMG_KERNELS)
    print("\n[reachability] functions transitively reaching an img kernel (DIRECT-CALL only):",
          sorted('0x%x' % x for x in reach))

    hosts = set()
    for va, t in entries:
        if t.strip() == 'callq\t0x%x' % RECORD_CLONE:
            hosts.add(func_start(prologue_va, va))
    print("[record-clone] distinct 0x%x host functions: %d" % (RECORD_CLONE, len(hosts)))
    print("[record-clone] hosts INTERSECT img-reaching set:",
          sorted('0x%x' % x for x in (hosts & reach)) or "EMPTY")
    print("[record-clone] img-reaching fns that call 0x%x:" % RECORD_CLONE,
          sorted('0x%x' % x for x in (rev.get(RECORD_CLONE, set()) & reach)) or "EMPTY")

    print("\n[direct-callers]")
    for k in sorted(IMG_KERNELS):
        print("  0x%x:" % k,
              sorted('0x%x' % x for x in rev.get(k, set())) or "none (indirect/vtable-only)")

    print("\n[vtable/RTTI] pointer-table references to indirect-only kernels:")
    for k in sorted(IMG_KERNELS):
        if not rev.get(k):
            print("  0x%x ptr-refs:" % k, [hex(o) for o in find_ptr_refs(data, k)])

if __name__ == '__main__':
    main()
